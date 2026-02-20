from google import genai
import json
import re

client = genai.Client(api_key="AIzaSyDGzTJliA2YQd9c7UGO4CG1y0j6-Pkwmow")

def analyze_transcript(transcript: str):

    prompt = f"""
    You are an Enterprise Conversation Intelligence Engine.

    Analyze this transcript:
    \"\"\"
    {transcript}
    \"\"\"

    Return ONLY valid JSON with:
    - language
    - summary
    - customer_sentiment
    - primary_intent
    - compliance_violations
    - agent_score
    """

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[prompt]
    )

    raw = response.text
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)

    if json_match:
        return json.loads(json_match.group())
    else:
        return {"error": "Invalid JSON returned"}