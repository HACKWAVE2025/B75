import os
import sqlite3
import tempfile
import datetime
import time
from flask import Flask, request, send_file, render_template_string, g
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from dotenv import load_dotenv

# Local imports
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

# -------------------- DB --------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS consultations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller TEXT,
        timestamp TEXT,
        recording_url TEXT,
        transcript TEXT,
        condition TEXT,
        advice TEXT,
        clinic_name TEXT,
        clinic_address TEXT
    )"""
    )
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

# Step 1: Record the user's voice (single input)
@app.route("/voice", methods=["POST"])
def voice():
    resp = VoiceResponse()
    resp.say("Hello! Please describe your symptoms after the beep. You have fifteen seconds.")
    
    # Record once, and go to /process_recording after that
    resp.record(
        maxLength=15,
        playBeep=True,
        trim="trim-silence",
        action="/process_recording",
        method="POST"
    )
    
    resp.say("No recording received. Goodbye.")
    return str(resp)

# Step 2: Process the recording and generate advice
@app.route("/process_recording", methods=["POST"])
def process_recording():
    recording_url = request.form.get("RecordingUrl")
    caller = request.form.get("From")

    print(f"Processing recording from {caller}: {recording_url}")
    resp = VoiceResponse()

    try:
        if not recording_url:
            resp.say("Sorry, we didn't receive any recording.")
            return str(resp)

        # Download Twilio audio
        local_path = download_file(recording_url, tempfile.gettempdir())

        # Transcribe the user audio
        transcript = transcribe(local_path)
        print(f"🎙 Transcript: {transcript}")

        # Run symptom analysis
        analysis = simple_symptom_checker(transcript)
        condition = analysis.get("condition", "Unknown condition")
        advice = analysis.get("advice", "Please describe your symptoms clearly.")

        # Find clinic
        region = os.getenv("DEFAULT_REGION", "Hyderabad, India")
        clinic = find_nearest_clinic(region)
        clinic_name = clinic.get("name", "Nearest clinic not found")
        clinic_address = clinic.get("address", "")

        # Prepare AI spoken response
        response_text = (
            f"You said: {transcript}. "
            f"It seems like {condition}. My advice: {advice}. "
            f"The nearest clinic is {clinic_name}. Please take care."
        )

        # Convert advice to speech
        tts_path = text_to_speech(response_text)
        print(f"🔊 TTS saved at: {tts_path}")

        # Save consultation
        db = get_db()
        db.execute(
            """INSERT INTO consultations (caller, timestamp, recording_url, transcript, condition, advice, clinic_name, clinic_address)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                caller,
                datetime.datetime.now(datetime.UTC).isoformat(),
                recording_url,
                transcript,
                condition,
                advice,
                clinic_name,
                clinic_address,
            ),
        )
        db.commit()

        # Play back to the user (once only)
        resp.say("Here is your health analysis.")
        resp.play(url=request.url_root + "tts_response")
        resp.say("Thank you for using our AI health assistant. Goodbye!")

        # Send SMS summary
        send_sms_fallback(caller, response_text)

    except Exception as e:
        print("❌ Error:", e)
        resp.say("Sorry, an error occurred while processing your symptoms. Please try again later.")

    return str(resp)

# -------------------- SMS --------------------
def send_sms_fallback(to_number, message):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not (sid and token and from_number):
        print("⚠ Twilio credentials missing; SMS skipped.")
        return

    client = Client(sid, token)
    try:
        client.messages.create(body=message[:1500], from_=from_number, to=to_number)
        print(f"📱 SMS sent to {to_number}")
    except Exception as e:
        print("⚠ SMS error:", e)

# -------------------- Serve TTS --------------------
@app.route("/tts_response", methods=["GET"])
def tts_response():
    path = os.path.join(tempfile.gettempdir(), "response.mp3")
    if not os.path.exists(path):
        return "No TTS file found", 404
    return send_file(path, mimetype="audio/mpeg")

# -------------------- Dashboard --------------------
@app.route("/dashboard")
def dashboard():
    db = get_db()
    rows = db.execute("SELECT * FROM consultations ORDER BY id DESC LIMIT 50").fetchall()
    return render_template_string("""
    <html><body><h2>Consultation History</h2>
    <table border=1>
      <tr><th>ID</th><th>Caller</th><th>Transcript</th><th>Condition</th><th>Advice</th></tr>
      {% for r in rows %}
      <tr><td>{{r['id']}}</td><td>{{r['caller']}}</td><td>{{r['transcript']}}</td><td>{{r['condition']}}</td><td>{{r['advice']}}</td></tr>
      {% endfor %}
    </table>
    </body></html>
    """, rows=rows)

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
