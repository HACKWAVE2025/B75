
# AI-Driven Symptom Checker (Dial-in) — Live Mode

This is an upgraded, demo-ready **Live Mode** prototype for the dial-in symptom checker.
It contains Twilio voice webhook integration, OpenAI Whisper transcription (if configured),
Hugging Face placeholder, SQLite logging, SMS fallback, nearest-clinic lookup using Nominatim (OpenStreetMap),
a simple Flask dashboard, Dockerfile and docker-compose for easy deployment.

**IMPORTANT:** This project will make real network/API calls when you provide real API keys.
Fill `.env` from `.env.example` before running.

## Quick Start (Live Mode)
1. Copy `.env.example` -> `.env` and fill your API keys: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, OPENAI_API_KEY
2. Build & run with Docker (recommended):
   ```bash
   docker-compose build
   docker-compose up
   ```
   or run locally:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   export FLASK_APP=app.py
   flask run --host=0.0.0.0 --port=5000
   ```
3. Expose to the internet using `ngrok` or deploy to a cloud provider, and set your Twilio phone number's Voice webhook URL to:
   `https://<your-host>/voice`

## What we added in Live Mode
- Real Twilio SMS fallback using Twilio REST API
- SQLite logging of consultations (`data/consultations.db`)
- Simple nearest-clinic lookup using Nominatim (geopy)
- Dashboard at `/dashboard` showing stored consultations
- Dockerfile + docker-compose for quick deployment
- `requirements.txt` with needed packages

## Safety & Legal
This is **not** a medical device. Do not use for clinical decision-making. Use only for prototyping and demo.
