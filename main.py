import json

from analysis_survey import analyze_transcript
from transcript_service import get_transcript
from rag_service import retrieve_policies


def main():
    """CLI workflow: transcribe → retrieve policies → analyze → print JSON."""
    print("Processing audio...")
    
    try:
        transcript = get_transcript("files/audio.mpeg")
    except FileNotFoundError:
        print("Error: audio.mpeg not found.")
        return
    except Exception as e:
        print(f"Transcription failed: {e}")
        return
    
    # Retrieve relevant banking policies (RAG)
    try:
        policies = retrieve_policies(transcript)
        if isinstance(policies, str) and policies.startswith("Error:"):
            print("Warning: failed to load policies; proceeding without policies.")
            policies = ""
    except Exception as e:
        print(f"Policy retrieval failed: {e}")
        policies = ""
    
    # Analyze transcript with policies
    try:
        result = analyze_transcript(transcript, policies)
    except Exception as e:
        print(f"Analysis failed: {e}")
        return
    
    print("Analysis complete.")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()