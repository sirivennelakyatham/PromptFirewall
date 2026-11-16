import os

from groq import Groq
from final_detector import detect


MODEL_NAME = "openai/gpt-oss-20b"


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your environment "
            "or Streamlit secrets."
        )

    return Groq(api_key=api_key)


def process_prompt(prompt: str) -> dict:
    """
    Complete security + LLM pipeline.

    1. Detect malicious prompt using ML + rules.
    2. Block malicious prompts.
    3. Send benign prompts to GPT-OSS-20B through Groq.
    """

    result = detect(prompt)

    is_malicious = result["label"].lower() == "malicious"

    if is_malicious:
        return {
            "label": result["label"],
            "malicious_probability": result["malicious_probability"],
            "confidence": result["confidence"],
            "rule_flags": result["rule_flags"],
            "blocked": True,
            "llm_response": None,
            "model": MODEL_NAME,
        }

    try:
        client = get_groq_client()

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )

        llm_response = response.choices[0].message.content

        return {
            "label": result["label"],
            "malicious_probability": result["malicious_probability"],
            "confidence": result["confidence"],
            "rule_flags": result["rule_flags"],
            "blocked": False,
            "llm_response": llm_response,
            "model": MODEL_NAME,
        }

    except Exception as e:
        return {
            "label": result["label"],
            "malicious_probability": result["malicious_probability"],
            "confidence": result["confidence"],
            "rule_flags": result["rule_flags"],
            "blocked": False,
            "llm_response": None,
            "model": MODEL_NAME,
            "error": str(e),
        }