import os
import joblib
import re

from groq import Groq


# ============================================================
# 1. LOAD YOUR SAVED ML MODEL
# ============================================================

MODEL_PATH = r"/kaggle/input/datasets/sirivennelakyatham/ml-logistic-regression/model.joblib"
VECTORIZER_PATH = r"/kaggle/input/datasets/sirivennelakyatham/ml-logistic-regression/tfidf_vectorizer.joblib"

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

ML_THRESHOLD = 0.5


# ============================================================
# 2. RULE ENGINE — INFORMATIONAL ONLY
# ============================================================

STANDALONE_RULES = {
    "Instruction Override": [
        r"\bignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?\b",
        r"\bforget\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?\b",
        r"\bdisregard\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?\b",
        r"\boverride\s+(the\s+)?(previous|system|original)\s+instructions?\b",
    ],

    "System Prompt Extraction": [
        r"\breveal\s+(your\s+)?(system|hidden)\s+(prompt|instructions?)\b",
        r"\bshow\s+(me\s+)?(your\s+)?(system|hidden)\s+(prompt|instructions?)\b",
        r"\bwhat\s+is\s+your\s+system\s+prompt\b",
    ],

    "Safety Bypass": [
        r"\bbypass\s+(your\s+)?(safety|security|restrictions?|filters?)\b",
        r"\bdisable\s+(your\s+)?(safety|security|restrictions?|filters?)\b",
        r"\bwithout\s+(any\s+)?restrictions?\b",
        r"\brestrictions?\s+(are\s+)?(disabled|removed|suspended)\b",
    ],

    "Jailbreak / Policy Evasion": [
        r"\bdo\s+anything\s+now\b",
        r"\bjailbreak(ed|ing)?\b",
        r"\buncensored\s+mode\b",
        r"\bdeveloper\s+mode\b",
        r"\bunrestricted\s+mode\b",
    ],
}


def clean_text(text):
    return text.lower().strip()


def has_any(text, patterns):
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def rule_score(text_clean):
    fired = [
        name
        for name, patterns in STANDALONE_RULES.items()
        if has_any(text_clean, patterns)
    ]

    return len(fired), fired


# ============================================================
# 3. DETECTOR
# ============================================================

def detect_prompt(text):

    cleaned = clean_text(text)

    # ML prediction
    probability = float(
        model.predict_proba(
            vectorizer.transform([cleaned])
        )[0, 1]
    )

    label = (
        "malicious"
        if probability >= ML_THRESHOLD
        else "benign"
    )

    # Rules are informational ONLY
    _, rule_flags = rule_score(cleaned)

    confidence = (
        probability
        if label == "malicious"
        else 1 - probability
    )

    return {
        "label": label,
        "malicious_probability": probability,
        "confidence": confidence,
        "rule_flags": rule_flags
    }


# ============================================================
# 4. GROQ LLM
# ============================================================

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def ask_llm(prompt):

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


# ============================================================
# 5. FINAL SYSTEM
# ============================================================

def process_prompt(prompt):

    result = detect_prompt(prompt)

    # UNSAFE → BLOCK
    if result["label"] == "malicious":

        return {
            "allowed": False,
            "detector": result,
            "response": None
        }

    # SAFE → SEND TO LLM
    response = ask_llm(prompt)

    return {
        "allowed": True,
        "detector": result,
        "response": response
    }