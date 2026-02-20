import requests
import base64
import json

MODEL_NAME = "gemini-2.5-flash"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# Read and encode the audio file
with open("audio.mpeg", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode("utf-8")

prompt = """
You are an Enterprise Conversation Intelligence Engine.
\n\nFrom this audio:
1. Detect language.
2. Perform speaker diarization (Agent and Customer).
"""

payload = {
    "contents": [
        {"parts": [{"text": prompt}]},
        {"parts": [{
            "inlineData": {
                "mimeType": "audio/mpeg",
                "data": audio_b64
            }
        }]}]
}

headers = {"Content-Type": "application/json"}

response = requests.post(ENDPOINT, headers=headers, data=json.dumps(payload))
print(response.json())