from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import Dict, Any, List, Optional

from transcript_service import get_transcript
from rag_service import retrieve_policies
from analysis_survey import analyze_transcript
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from risk_engine import compute_risk_score

# Directory containing selectable audio files
FILES_DIR = "files"


app = FastAPI(title="Banking Conversation Intelligence API")

app.mount("/static", StaticFiles(directory="frontend"), name="static")
@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")
# Allow cross-origin requests (adjust origins for production)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
	return {"status": "ok"}


@app.get("/files")
def list_files() -> Dict[str, List[str]]:
	"""List audio files available in the FILES_DIR directory."""
	if not os.path.exists(FILES_DIR) or not os.path.isdir(FILES_DIR):
		raise HTTPException(status_code=404, detail=f"Files directory not found: {FILES_DIR}")

	allowed_ext = {".mp3", ".mpeg", ".wav"}
	files = []
	try:
		for fname in os.listdir(FILES_DIR):
			if os.path.splitext(fname)[1].lower() in allowed_ext:
				files.append(fname)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")

	return {"files": sorted(files)}


class ClientConfig(BaseModel):
    domain: str = "banking"
    risk_threshold: int = 70
    compliance_triggers: Optional[List[str]] = [
        "RBI complaint",
        "legal action",
        "fraud allegation"
    ]

class AnalyzeRequest(BaseModel):
    filename: str
    client_config: Optional[ClientConfig] = ClientConfig()


@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> Dict[str, Any]:
	"""Analyze an audio file selected from the server-side `files/` directory.

	Expected body: { "filename": "call123.mp3" }
	"""
	filename = req.filename
	# Prevent path traversal
	if os.path.basename(filename) != filename:
		raise HTTPException(status_code=400, detail="Invalid filename")

	file_path = os.path.join(FILES_DIR, filename)
	if not os.path.exists(file_path):
		raise HTTPException(status_code=404, detail=f"File not found: {filename}")

	try:
		transcript = get_transcript(file_path)
	except FileNotFoundError:
		raise HTTPException(status_code=400, detail="Audio file not found for transcription")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Transcription error: {e}")

	try:
		policies = retrieve_policies(transcript)
		if isinstance(policies, str) and policies.startswith("Error:"):
			policies = ""
	except Exception:
		policies = ""

	try:
		result = analyze_transcript(transcript, policies, req.client_config.dict())
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Analysis error: {e}")

	# ---- Deterministic Risk Scoring Layer ----
	try:
		risk_data = compute_risk_score(result, req.client_config.dict())
		result["risk_analysis"] = risk_data
	except Exception:
		result["risk_analysis"] = {
			"risk_score": 0,
			"risk_band": "low",
			"risk_reasoning": ["Risk computation failed"]
		}

	return result


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="0.0.0.0", port=8000)

