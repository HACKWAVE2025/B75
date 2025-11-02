from gtts import gTTS
import tempfile, os

def text_to_speech(text, out_path=None, lang='en'):
    if not out_path:
        out_path = os.path.join(tempfile.gettempdir(), "response.mp3")
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(out_path)
    print(f"🔊 Saved TTS at: {out_path}")
    return out_path
