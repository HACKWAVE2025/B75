import requests, os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")

def download_file(url, dest_folder='/tmp'):
    """Download a Twilio recording with authentication."""
    os.makedirs(dest_folder, exist_ok=True)

    # Generate local file name
    local_filename = os.path.join(
        dest_folder,
        os.path.basename(urlparse(url).path) or 'recording.wav'
    )

    # ✅ Authenticate with Twilio
    with requests.get(url, stream=True, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return local_filename
