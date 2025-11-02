import os, sqlite3, tempfile, datetime, time
from flask import Flask, request, send_file, render_template_string, g
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from dotenv import load_dotenv
from utils import download_file
from transcribe import transcribe
from nlp import simple_symptom_checker
from tts import text_to_speech
from geolocate import find_nearest_clinic

# -------------------- ENV SETUP --------------------
load_dotenv()
print("✅ Twilio SID:", os.getenv("TWILIO_ACCOUNT_SID"))

DATABASE = os.path.join(os.getcwd(), "data", "consultations.db")
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

app = Flask(__name__)

# -------------------- DATABASE --------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caller TEXT,
            timestamp TEXT,
            recording_url TEXT,
            transcript TEXT,
            condition TEXT,
            advice TEXT,
            clinic_name TEXT,
            clinic_address TEXT
        )
    """)
    db.commit()

with app.app_context():
    init_db()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db:
        db.close()

# -------------------- ROUTES --------------------

@app.route("/health")
def health():
    return "OK"

@app.route("/voice", methods=["POST"])
def voice():
    """Single 15s recording input."""
    resp = VoiceResponse()
    resp.say("Hello. Please describe your symptoms after the beep. You have fifteen seconds.")
    resp.record(
        maxLength=15,
        playBeep=True,
        trim="trim-silence",
        action="/process_recording",
        method="POST"
    )
    resp.say("No recording received. Goodbye.")
    return str(resp)

@app.route("/process_recording", methods=["POST"])
def process_recording():
    recording_url = request.form.get("RecordingUrl")
    caller = request.form.get("From")

    if not recording_url:
        resp = VoiceResponse()
        resp.say("Sorry, we did not receive a recording. Goodbye.")
        return str(resp)

    print(f"Processing recording from {caller}: {recording_url}")

    # 1️⃣ Download
    local_path = download_file(recording_url, tempfile.gettempdir())

    # 2️⃣ Transcribe
    transcript = transcribe(local_path)
    print(f"🎙️ Transcript: {transcript}")

    # 3️⃣ Analyze
    analysis = simple_symptom_checker(transcript)
    condition = analysis.get("condition", "unknown")
    advice = analysis.get("advice", "Please provide more details about your symptoms.")

    # 4️⃣ Nearest clinic
    region = os.getenv("DEFAULT_REGION", "Hyderabad, India")
    clinic = find_nearest_clinic(region)
    clinic_name = clinic.get("name", "Not found")
    clinic_address = clinic.get("address", "N/A")

    # 5️⃣ Compose message
    response_text = (
        f"Based on your description, it seems like {condition}. "
        f"My advice: {advice}. The nearest clinic available is {clinic_name}. "
        "Please take care and consult a doctor if symptoms worsen."
    )

    # 6️⃣ TTS generation
    tts_path = text_to_speech(response_text)
    print(f"🔊 TTS saved at: {tts_path}")
    time.sleep(2)

    # 7️⃣ Save DB entry
    db = get_db()
    db.execute("""
        INSERT INTO consultations (caller, timestamp, recording_url, transcript, condition, advice, clinic_name, clinic_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        caller,
        datetime.datetime.utcnow().isoformat(),
        recording_url,
        transcript,
        condition,
        advice,
        clinic_name,
        clinic_address
    ))
    db.commit()

    # 8️⃣ Twilio Voice Response
    resp = VoiceResponse()
    resp.say("Thank you. Please wait while I prepare your health advice.")
    resp.play(url=request.url_root + "tts_response")
    resp.say("Thank you for using our AI health assistant. Goodbye.")

    # 9️⃣ SMS fallback
    send_sms_fallback(caller, f"🩺 Your symptoms: {transcript}\n\n{response_text}")

    return str(resp)

# -------------------- SMS --------------------
def send_sms_fallback(to_number, message):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    if not (sid and token and from_number):
        print("⚠️ Missing Twilio credentials. SMS not sent.")
        return
    client = Client(sid, token)
    try:
        client.messages.create(body=message[:1500], from_=from_number, to=to_number)
        print(f"📱 SMS sent to {to_number}")
    except Exception as e:
        print(f"SMS Error: {e}")

@app.route("/tts_response", methods=["GET"])
def tts_response():
    path = "/tmp/response.mp3"
    if not os.path.exists(path):
        return "No TTS file", 404
    return send_file(path, mimetype="audio/mpeg")

# -------------------- Dashboard --------------------
@app.route("/dashboard")
def dashboard():
    db = get_db()
    rows = db.execute("SELECT * FROM consultations ORDER BY id DESC LIMIT 100").fetchall()
    return render_template_string("""
    <html><body><h2>Consultations Dashboard</h2>
    <table border=1 cellpadding=5>
    <tr><th>ID</th><th>Caller</th><th>Transcript</th><th>Condition</th><th>Advice</th><th>Clinic</th></tr>
    {% for r in rows %}
      <tr><td>{{r['id']}}</td><td>{{r['caller']}}</td><td>{{r['transcript']}}</td>
      <td>{{r['condition']}}</td><td>{{r['advice']}}</td><td>{{r['clinic_name']}}</td></tr>
    {% endfor %}
    </table></body></html>
    """, rows=rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
