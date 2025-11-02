import os
from openai import OpenAI
from transformers import pipeline

def transcribe(audio_path):
    """
    Transcribes an audio file using OpenAI Whisper first,
    then falls back to Hugging Face Whisper if quota or connection fails.
    """
    transcript_text = "Unable to transcribe user speech."

    # Try OpenAI Whisper
    try:
        print("🎧 Using OpenAI Whisper for transcription...")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcript_text = transcript.text.strip()
        print(f"✅ OpenAI Whisper transcript: {transcript_text}")
        return transcript_text
    except Exception as e:
        print(f"⚠️ OpenAI Whisper failed, using fallback: {e}")

    # Fallback: Hugging Face Whisper (runs locally)
    try:
        print("🎙️ Using Hugging Face model: openai/whisper-base.en ...")
        asr = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-base.en",
            device=-1  # use CPU
        )
        result = asr(audio_path)
        transcript_text = result["text"].strip()
        print(f"✅ HF transcript: {transcript_text}")
    except Exception as e:
        print(f"❌ Both transcription methods failed: {e}")
        transcript_text = "Unable to transcribe user speech."

    return transcript_text
