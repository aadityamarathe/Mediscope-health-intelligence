"""
train_classifier.py
───────────────────
Trains a TF-IDF + Logistic Regression classifier to distinguish
disease-outbreak articles from irrelevant ones.

Auto-labels raw_articles from MongoDB using a deterministic heuristic,
then saves the fitted vectorizer and model as .pkl files so that
relevance.py can load them at runtime.

Usage:
    python -m backend.nlp.train_classifier
"""

import os
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# joblib is scikit-learn's recommended serialiser for models
import joblib

# ── Reuse the project's existing MongoDB connection ────────────────
from ..database.mongo_connection import get_db

# ── Directory where .pkl artefacts will be saved ───────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# ── Named diseases for auto-labelling ─────────────────────────────
# Includes common synonyms (flu, tb, coronavirus, lassa) so RSS titles
# that use shorthand are still caught.
SPECIFIC_DISEASES = {
    "cholera", "dengue", "malaria", "covid", "ebola", "influenza",
    "tuberculosis", "hepatitis", "typhoid", "measles", "zika",
    "monkeypox", "polio", "mpox", "hiv", "plague", "rabies",
    "lassa", "marburg", "nipah", "chikungunya", "diphtheria",
    "coronavirus", "flu", "tb",
}

# ── Epidemiological signal words ───────────────────────────────────
# Broader than before: "disease", "virus", "infection", "pandemic",
# "alert", "surveillance" are all legitimate public-health signals.
SIGNAL_WORDS = {
    "outbreak", "epidemic", "cases", "deaths", "confirmed",
    "infected", "reported", "spread", "disease", "virus",
    "infection", "pandemic", "alert", "surveillance",
}


def _combine_text(article: dict) -> str:
    """Merge title + description (or content) into a single input string."""
    title = article.get("title") or ""
    # Some documents use 'description', others use 'content'
    body = article.get("description") or article.get("content") or ""
    return f"{title} {body}".strip()


def _auto_label(text: str) -> int:
    """
    Looser labelling heuristic — positive if the article mentions ANY
    known disease name OR ANY epidemiological signal word.

    Rationale: on a small corpus (≤ 300 articles) the stricter AND-logic
    produced far too few positives (~2/80), making stratified splitting
    impossible.  The OR-logic yields a more balanced class distribution
    while still being grounded in public-health vocabulary.
    """
    text_lower = text.lower()

    # A single named disease mention is sufficient evidence
    has_disease = any(d in text_lower for d in SPECIFIC_DISEASES)

    # OR a single epidemiological signal word is sufficient
    has_signal = any(s in text_lower for s in SIGNAL_WORDS)

    # Label positive (1) if either condition holds
    return 1 if (has_disease or has_signal) else 0


def train():
    """Main training routine.  Callable programmatically or via __main__."""

    # ── 1. Load articles from MongoDB ──────────────────────────────
    db = get_db()
    cursor = db["raw_articles"].find(
        {},
        # Only fetch the fields we need to keep memory low
        {"title": 1, "description": 1, "content": 1, "_id": 0},
    )
    articles = list(cursor)

    if not articles:
        print("[ERROR] No documents found in raw_articles. Cannot train.")
        sys.exit(1)

    print(f"[INFO] Loaded {len(articles)} articles from raw_articles.")

    # ── 2. Build texts + auto-labels ───────────────────────────────
    texts = []
    labels = []

    for article in articles:
        combined = _combine_text(article)
        if not combined:
            # Skip empty documents — they add noise
            continue
        texts.append(combined)
        labels.append(_auto_label(combined))

    if not texts:
        print("[ERROR] All articles were empty. Cannot train.")
        sys.exit(1)

    # Quick sanity check: how many positive vs negative?
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    print(f"[INFO] Auto-labelled → positive (outbreak): {n_pos}  |  negative: {n_neg}")

    if n_pos == 0 or n_neg == 0:
        print("[ERROR] Only one class present. Need both positives and negatives.")
        sys.exit(1)

    # ── 3. Vectorise with TF-IDF ───────────────────────────────────
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),       # Use unigrams and bigrams for richer features
        max_features=5000,        # Cap vocabulary size to avoid overfitting on small data
        stop_words="english",     # Remove common English stop-words
    )
    X = vectorizer.fit_transform(texts)

    # ── 4. Train / test split ──────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels,
        test_size=0.2,
        random_state=42,          # Reproducible splits
        stratify=labels,          # Keep class ratio identical in both sets
    )

    print(f"[INFO] Train size: {X_train.shape[0]}  |  Test size: {X_test.shape[0]}")

    # ── 5. Fit Logistic Regression ─────────────────────────────────
    model = LogisticRegression(
        class_weight="balanced",  # Up-weight the minority class automatically
        max_iter=1000,            # Extra iterations for convergence on small data
        random_state=42,
    )
    model.fit(X_train, y_train)

    # ── 6. Evaluate on test set ────────────────────────────────────
    y_pred = model.predict(X_test)

    print("\n" + "=" * 55)
    print("  Classification Report")
    print("=" * 55)
    print(classification_report(
        y_test, y_pred,
        target_names=["irrelevant (0)", "outbreak  (1)"],
    ))

    # ── 7. Save model + vectorizer ─────────────────────────────────
    os.makedirs(MODELS_DIR, exist_ok=True)

    classifier_path = os.path.join(MODELS_DIR, "classifier.pkl")
    vectorizer_path = os.path.join(MODELS_DIR, "vectorizer.pkl")

    joblib.dump(model, classifier_path)
    joblib.dump(vectorizer, vectorizer_path)

    print(f"[OK] Classifier saved  → {classifier_path}")
    print(f"[OK] Vectorizer saved  → {vectorizer_path}")
    print("[OK] Training complete. relevance.py will load the model on next import.")


# ── Standalone entry-point ─────────────────────────────────────────
# Run with:  python -m backend.nlp.train_classifier
if __name__ == "__main__":
    train()
