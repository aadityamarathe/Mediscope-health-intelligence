"""
relevance.py
────────────
Determines whether a news article is relevant to disease-outbreak surveillance.

Strategy:
  1. If a trained TF-IDF + Logistic Regression model exists in ./models/,
     use it for prediction (predict_proba → confidence).
  2. If the model files have not been generated yet (first run, or training
     hasn't happened), fall back silently to the original keyword heuristic
     so the pipeline never crashes.

The public interface is unchanged:
  is_relevant_article(text) → {"is_relevant": bool, "confidence": float}
  is_model_loaded()         → bool
"""

import os
import joblib

# ── Paths to the serialised model artefacts ────────────────────────
_MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
_CLASSIFIER_PATH = os.path.join(_MODELS_DIR, "classifier.pkl")
_VECTORIZER_PATH = os.path.join(_MODELS_DIR, "vectorizer.pkl")

# ── Try to load model + vectorizer at import time ──────────────────
# If the files don't exist yet we set them to None and fall back to
# the keyword method — no crash, no log spam.
_classifier = None
_vectorizer = None

try:
    if os.path.isfile(_CLASSIFIER_PATH) and os.path.isfile(_VECTORIZER_PATH):
        _classifier = joblib.load(_CLASSIFIER_PATH)
        _vectorizer = joblib.load(_VECTORIZER_PATH)
except Exception:
    # Corrupt / incompatible pickle → fall back silently
    _classifier = None
    _vectorizer = None

# ── Keyword-based fallback (original implementation) ───────────────
KEYWORDS = [
    # diseases
    "cholera", "dengue", "malaria", "covid", "ebola",
    "influenza", "tuberculosis", "hepatitis", "typhoid",
    "measles", "zika", "monkeypox", "polio",

    # synonyms
    "tb", "flu", "coronavirus",

    # symptoms / signals
    "fever", "infection", "virus", "outbreak",
    "epidemic", "pandemic", "cases", "deaths"
]


def _keyword_relevance(text: str) -> dict:
    """Original keyword-matching heuristic.  Used only when no model is loaded."""
    if not text:
        return {"is_relevant": False, "confidence": 0.0}

    text_lower = text.lower()
    count = sum(1 for k in KEYWORDS if k in text_lower)

    is_relevant = count >= 1
    # Cap confidence at 1.0; three matching keywords → full confidence
    confidence = min(count / 3, 1.0)

    return {"is_relevant": is_relevant, "confidence": confidence}


def _model_relevance(text: str) -> dict:
    """ML-based prediction using the trained TF-IDF + Logistic Regression model."""
    # Transform the input text with the same vectorizer used during training
    X = _vectorizer.transform([text])

    # predict_proba returns [[prob_class_0, prob_class_1]]
    proba = _classifier.predict_proba(X)[0]

    # Class 1 = outbreak article; its probability is our confidence score
    confidence = float(proba[1])

    # Threshold at 0.5 — the natural decision boundary for logistic regression
    is_relevant = confidence >= 0.5

    return {"is_relevant": is_relevant, "confidence": round(confidence, 4)}


# ── Public API ─────────────────────────────────────────────────────

def is_relevant_article(text: str) -> dict:
    """
    Assess whether *text* describes a disease outbreak.

    Returns:
        {"is_relevant": bool, "confidence": float}   (identical to original)

    Uses the ML classifier when available, otherwise falls back to
    the keyword heuristic.
    """
    if not text:
        return {"is_relevant": False, "confidence": 0.0}

    # Prefer the trained model; fall back to keywords if not available
    if _classifier is not None and _vectorizer is not None:
        return _model_relevance(text)

    return _keyword_relevance(text)


def is_model_loaded() -> bool:
    """Return True if the ML classifier and vectorizer are loaded and ready."""
    return _classifier is not None and _vectorizer is not None