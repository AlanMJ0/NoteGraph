from src import config, gemini_client

def extract_concept(question: str) -> str:

    EXTRACT_CONCEPT="""act as a technical concept extractor, return only a JSON object with a single key "concept"
    keep the value concise (e.g., "Dynamic Programming" instead of "What should I learn before Dynamic
    Programming?"), and return the original question if no clear technical topic exists."""

    prompt=f"Question:{question}"

    if not question or not question.strip():
        return question
    try:
        result=gemini_client.generate_json(
        prompt=prompt,
        model=config.MODEL_STRONG,
        system_instruction=EXTRACT_CONCEPT)

        if isinstance(result,dict) and "concept" in result:
            extracted=result["concept"]
            if isinstance(extracted,str) and extracted.strip():
                return extracted
      
    except Exception as e:
        print("concept extractor failed")
    return question
            
    
if __name__ == "__main__":
    sample_questions = [
        "What should I learn before Dynamic Programming?",
        "How does QuickSort work?",
        "What is the time complexity of binary search?",
    ]

    for q in sample_questions:
        print(f"Q: {q}")
        print(f"Concept: {extract_concept(q)}\n")