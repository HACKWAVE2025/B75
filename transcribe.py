import os
import tempfile
from transformers import pipeline
import torch
from openai import OpenAI

# Load OpenAI API key from environment (if available)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def transcribe(audio_path):
    """
    Transcribe the user's recorded audio using OpenAI Whisper if available,
    otherwise fallback to Hugging Face Whisper (free).
    """
    print(f"Processing audio for transcription: {audio_path}")

    # ---------- STEP 1: Try OpenAI Whisper ----------
    if OPENAI_API_KEY:
        try:
            print("🎧 Using OpenAI Whisper for transcription...")
            client = OpenAI(api_key=OPENAI_API_KEY)

            # Convert audio to proper format (OpenAI requires .mp3/.m4a/.wav/.webm)
            with open(audio_path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="gpt-4o-mini-transcribe",  # New model supports speech-to-text
                    file=f
                )
            text = transcription.text.strip()
            print(f"✅ OpenAI Transcript: {text}")
            return text

        except Exception as e:
            print("⚠️ OpenAI Whisper failed, using fallback:", e)

    # ---------- STEP 2: Use Hugging Face Whisper ----------
    try:
        print("🎙️ Using Hugging Face model: openai/whisper-small.en ...")
        asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-small.en",
            device=0 if torch.cuda.is_available() else "cpu"
        )
        result = asr_pipeline(audio_path)
        text = result["text"].strip()
        print(f"✅ HF transcript: {text}")
        return text

    except Exception as e:
        print("❌ Both transcription methods failed:", e)
        return "Unable to transcribe user speech."

