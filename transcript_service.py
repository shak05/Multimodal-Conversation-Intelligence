import requests
import base64
import json
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"


def _build_endpoint(api_key: str) -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"


def get_transcript(audio_file_path: str) -> str:
    """Transcribe an audio file using Gemini generateContent REST endpoint.

    Returns the transcript text extracted from the API response:
    result["candidates"][0]["content"]["parts"][0]["text"]

    Raises:
        FileNotFoundError: if the audio file doesn't exist.
        RuntimeError: for missing API key, request failures, or unexpected responses.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not found in environment. Set it in .env or env vars.")

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    with open(audio_file_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "You are an Enterprise Conversation Intelligence Engine.\n\n"
        "From this audio:\n"
        "1. Detect language.\n"
        "2. Perform speaker diarization (Agent and Customer).\n\n"
        "Return the transcript text labeled with speakers (Agent/Customer) as plain text."
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]},
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "audio/mpeg",
                            "data": audio_b64,
                        }
                    }
                ]
            },
        ]
    }

    headers = {"Content-Type": "application/json"}
    endpoint = _build_endpoint(GEMINI_API_KEY)

    try:
        resp = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=60)
    except requests.RequestException as e:
        raise RuntimeError(f"Request to Gemini API failed: {e}")

    if resp.status_code != 200:
        # Include body to aid debugging, but keep message concise
        raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError("Failed to parse JSON response from Gemini API")

    try:
        transcript = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected response format from Gemini API: {e}. Full response: {json.dumps(data)[:1000]}")

    return transcript


__all__ = ["get_transcript"]