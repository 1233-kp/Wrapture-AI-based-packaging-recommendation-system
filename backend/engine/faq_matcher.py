"""Free-text question -> best-matching FAQ answer, via the same local
embedding approach as engine/commodity_matcher.py (same shared model, see
engine/embedding_model.py).

This is template matching, not a generative chatbot: a query only ever
resolves to one of the existing, hand-written answers in data/faq.json, or
an honest "no good match" result — nothing is generated. Deliberately does
NOT touch recommend()/recommend_detailed() or commodity_matcher.py's own
matching logic.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine.embedding_model import get_shared_model

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 0-1 cosine similarity. FAQ questions are short and varied in phrasing, so
# this is tuned independently of commodity_matcher's own threshold — see
# tests/test_faq_matcher.py for how this value was picked.
LOW_CONFIDENCE_SIMILARITY_THRESHOLD = 0.45

_faq_embeddings = None  # numpy array, shape (n_faqs, embedding_dim)


@lru_cache
def list_faqs() -> list[dict]:
    with open(DATA_DIR / "faq.json", encoding="utf-8") as f:
        return json.load(f)["faqs"]


def load_faq_embeddings() -> None:
    """Eagerly loads the model and computes+caches embeddings for every FAQ
    question. Called once from main.py's startup event, same pattern as
    commodity_matcher.load_model_and_embeddings()."""
    global _faq_embeddings

    model = get_shared_model()
    texts = [faq["question"] for faq in list_faqs()]
    _faq_embeddings = model.encode(texts, normalize_embeddings=True)


def _ensure_loaded() -> None:
    if _faq_embeddings is None:
        load_faq_embeddings()


def match_faq(query: str, threshold: float = LOW_CONFIDENCE_SIMILARITY_THRESHOLD) -> dict[str, Any]:
    """Embeds `query` and returns the single best-matching FAQ by cosine
    similarity, or an honest no-match result if nothing clears the threshold.

    Both the query and FAQ-question embeddings are L2-normalized, so a plain
    dot product IS the cosine similarity — no separate normalization step.
    """
    _ensure_loaded()
    model = get_shared_model()
    faqs = list_faqs()

    query_vec = model.encode([query], normalize_embeddings=True)[0]
    similarities = _faq_embeddings @ query_vec

    best_idx = int(similarities.argmax())
    best_similarity = float(similarities[best_idx])
    matched = best_similarity >= threshold

    return {
        "query": query,
        "matched": matched,
        "faq": faqs[best_idx] if matched else None,
        "similarity_percent": round(best_similarity * 100, 1),
        "threshold": threshold,
    }
