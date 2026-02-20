from analysis_survey import analyze_transcript

transcript = """
Agent: Hello, how can I help you?
Customer: I see an unauthorized transaction.
"""

result = analyze_transcript(transcript)

print(result)