import joblib
import re


# ============================================================
# LOAD FINAL SAVED DETECTOR
# ============================================================

detector = joblib.load("final_detector.joblib")

MODEL = detector["model"]
VECTORIZER = detector["vectorizer"]
THRESHOLD = detector["threshold"]
RULES = detector["standalone_rules"]


# ============================================================
# RULE ENGINE — INFORMATIONAL ONLY
# ============================================================

def get_rule_flags(text):

    flags = []

    for name, patterns in RULES.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(name)
                break

    return flags


# ============================================================
# FINAL DETECTOR
# ============================================================

def detect(text):

    probability = float(
        MODEL.predict_proba(
            VECTORIZER.transform([text])
        )[0, 1]
    )

    if probability >= THRESHOLD:
        label = "malicious"
        confidence = probability
    else:
        label = "benign"
        confidence = 1 - probability

    rule_flags = get_rule_flags(text)

    return {
        "label": label,
        "malicious_probability": probability,
        "confidence": confidence,
        "rule_flags": rule_flags
    }