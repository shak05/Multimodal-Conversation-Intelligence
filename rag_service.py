"""Simple RAG (retrieval) service for banking policies.

Provides `retrieve_policies(transcript: str) -> str` which reads
`policies.txt` and returns relevant policy chunks based on keywords.

Keyword rules:
- "fraud" -> return fraud policy chunk
- "refund" -> return refund SLA policy chunk
- "rbi" or "legal" -> return escalation policy chunk
- no match -> return a general compliance rule

The implementation uses simple keyword matching over policy chunks
separated by blank lines. Basic error handling is included for missing
policy file.
"""
from typing import List
import os


def _load_policy_chunks(filepath: str) -> List[str]:
    """Load policy file and split into non-empty chunks separated by blank lines."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Split on two or more newlines to get paragraphs/sections
    raw_chunks = [c.strip() for c in text.split("\n\n")]
    chunks = [c for c in raw_chunks if c]
    return chunks


def _find_chunk_by_keywords(chunks: List[str], keywords: List[str]) -> str:
    """Return the first chunk that contains any of the keywords (case-insensitive)."""
    lower_keywords = [k.lower() for k in keywords]
    for chunk in chunks:
        low = chunk.lower()
        for kw in lower_keywords:
            if kw in low:
                return chunk
    return ""


def retrieve_policies(transcript: str, filepath: str = "policies.txt") -> str:
    """Retrieve relevant policy text for the given transcript.

    Args:
        transcript: The conversation transcript to query against.
        filepath: Path to `policies.txt` (defaults to workspace root).

    Returns:
        A formatted string containing the selected policy chunk(s) or an
        explanatory error/default message if no matching policy is found.
    """
    if not os.path.exists(filepath):
        return (
            "Error: policies.txt not found. Please add a policies.txt file "
            "with policy sections (separated by blank lines)."
        )

    try:
        chunks = _load_policy_chunks(filepath)
    except Exception as e:
        return f"Error reading policies file: {e}"

    transcript_low = transcript.lower()
    selected: List[str] = []

    # Fraud
    if "fraud" in transcript_low:
        fraud = _find_chunk_by_keywords(chunks, ["fraud"]) or "Fraud policy not found in policies.txt."
        selected.append("--- Fraud Policy ---\n" + fraud)

    # Refund
    if "refund" in transcript_low:
        refund = _find_chunk_by_keywords(chunks, ["refund", "refund sla", "refund policy"]) or (
            "Refund SLA policy not found in policies.txt."
        )
        selected.append("--- Refund / SLA Policy ---\n" + refund)

    # RBI / Legal / Escalation
    if "rbi" in transcript_low or "legal" in transcript_low:
        esc = _find_chunk_by_keywords(chunks, ["rbi", "legal", "escalation"]) or (
            "Escalation policy (RBI/Legal) not found in policies.txt."
        )
        selected.append("--- Escalation / RBI / Legal Policy ---\n" + esc)

    # If no specific policy matched, provide a general compliance rule
    if not selected:
        general = _find_chunk_by_keywords(chunks, ["compliance", "general", "policy"]) or (
            chunks[0] if chunks else "No policies available in policies.txt."
        )
        selected.append("--- General Compliance Rule ---\n" + general)

    # Join selected chunks into a single formatted string
    return "\n\n".join(selected)


__all__ = ["retrieve_policies"]
