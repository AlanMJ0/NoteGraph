# Gemini API client
import json
import time
from google import genai
from google.genai import errors as genai_errors
from src import config

# Lazily initialized — we only create the client on first actual API call,
# not at import time. This prevents a bad API key or missing package from
# causing a confusing crash in whatever file happened to import this module.
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def generate_text(prompt,model=None,system_instruction=" "):
    if model is None:
        model=config.MODEL_FAST

    client = _get_client()
    attempt=0
    while attempt<config.MAX_RETRIES:
        try:
            if system_instruction:
                response=client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"system_instruction":system_instruction},
                )
            else:
                response=client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
            return response.text

        except genai_errors.ServerError:
            wait_seconds=config.BASE_BACKOFF_SECONDS*(2**attempt)
            print("Gemini server error, retrying in", wait_seconds, "seconds")
            time.sleep(wait_seconds)
            attempt+=1

    raise RuntimeError("Gemini call failed after ", attempt, "retries")

def generate_json(prompt, model=None, system_instruction=" "):
    if model is None:
        model=config.MODEL_STRONG

    client = _get_client()
    attempt=0
    while attempt<config.MAX_RETRIES:
        try:
            if system_instruction:
                response=client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"system_instruction":system_instruction,
                    "response_mime_type": "application/json",},
                )
            else:
                response=client.models.generate_content(
                    model=model,
                    contents=prompt,
                )    
            raw_text=response.text

            cleaned_text=raw_text.strip()
            if cleaned_text.startswith("```"):
                cleaned_text=cleaned_text.strip("`")
                cleaned_text=cleaned_text.replace("json","",1).strip()

            return json.loads(cleaned_text)

        except genai_errors.ServerError:
            wait_seconds=config.BASE_BACKOFF_SECONDS*(2**attempt)
            print("Gemini server error, retrying in ", wait_seconds, "seconds")
            time.sleep(wait_seconds)
            attempt+=1
    raise RuntimeError("Gemini call failed after", attempt, "tries")


if __name__=="__main__":
    result=generate_text("say hello in five words")
    print(result)





                
