"""Free-text -> closest-existing-commodity matching, via local embeddings.
Purely additive fallback for commodities not in our commodities database
(see data/commodities.json for the current count).

Deliberately does NOT touch recommend()/recommend_detailed() or their scoring logic —
a "match" only ever resolves to picking one of the existing commodity_ids that engine
already knows how to score. This module's job stops at "which existing commodity is
this free-text description most like," nothing more.

Model: all-MiniLM-L6-v2, run via fastembed/onnxruntime (see engine/embedding_model.py
for why, not sentence-transformers/torch). Small (~90MB), runs fully locally on CPU, no
API key, no per-request network call. Model files are bundled in models/embedding_cache/
— no download or network access needed at startup, on this machine or in production.
"""

from functools import lru_cache
from typing import Any

from engine.embedding_model import get_shared_model
from engine.recommender import list_commodities

# 0-1 cosine similarity. Below this, even the "best" match is treated as a rough
# guess rather than a real match — see run_evaluation-style testing notes in
# tests/test_commodity_matcher.py for how this value was picked.
LOW_CONFIDENCE_SIMILARITY_THRESHOLD = 0.5

_commodity_texts: list[str] = []
_commodity_records: list[dict] = []
_commodity_embeddings = None  # numpy array, shape (n_commodities, embedding_dim)


def _midpoint_text(range_dict: dict | None, unit: str) -> str:
    if not range_dict:
        return ""
    mid = (range_dict["min"] + range_dict["max"]) / 2
    return f"{mid:g}{unit}"


def _describe_commodity(commodity: dict) -> str:
    """Combined text representation for embedding — name + category + a short
    description of key properties, so semantically similar commodities actually
    cluster together instead of only matching on the bare name string."""
    parts = [commodity["name"], commodity["category"].replace("_", " ")]

    moisture = _midpoint_text(commodity.get("moisture_content_percent"), "% moisture")
    if moisture:
        parts.append(moisture)

    fat = _midpoint_text(commodity.get("fat_content_percent"), "% fat")
    if fat:
        parts.append(fat)

    respiration = commodity.get("respiration_rate_class")
    if respiration:
        parts.append(f"{respiration.replace('_', ' ')} respiration rate")

    shelf_life = commodity.get("typical_ambient_shelf_life_days")
    if shelf_life:
        mid = (shelf_life["min"] + shelf_life["max"]) / 2
        parts.append(f"{'short' if mid < 5 else 'long'} ambient shelf life (~{mid:g} days)")

    if commodity.get("notes"):
        parts.append(commodity["notes"])

    return ", ".join(parts)


def load_model_and_embeddings() -> None:
    """Eagerly loads the model and computes+caches embeddings for all existing
    commodities. Called once from main.py's startup event so the cost is paid at
    boot, not on the first user request."""
    global _commodity_texts, _commodity_records, _commodity_embeddings

    model = get_shared_model()
    _commodity_records = list_commodities()
    _commodity_texts = [_describe_commodity(c) for c in _commodity_records]
    _commodity_embeddings = model.encode(_commodity_texts, normalize_embeddings=True)


def _ensure_loaded() -> None:
    if _commodity_embeddings is None:
        load_model_and_embeddings()


def _to_properties(commodity: dict) -> dict[str, Any]:
    return {
        "moisture_content_percent": commodity.get("moisture_content_percent"),
        "fat_content_percent": commodity.get("fat_content_percent"),
        "ph_range": commodity.get("ph_range"),
        "respiration_rate_class": commodity.get("respiration_rate_class"),
        "typical_ambient_shelf_life_days": commodity.get("typical_ambient_shelf_life_days"),
        "confidence": commodity.get("confidence", "medium"),
    }


def match_commodities(
    query: str, top_n: int = 3, threshold: float = LOW_CONFIDENCE_SIMILARITY_THRESHOLD
) -> dict[str, Any]:
    """Embeds `query` and returns the top_n existing commodities by cosine similarity.

    Both the query and commodity embeddings are L2-normalized (normalize_embeddings=True),
    so a plain dot product IS the cosine similarity — no separate normalization step needed.
    """
    _ensure_loaded()
    model = get_shared_model()

    query_vec = model.encode([query], normalize_embeddings=True)[0]
    similarities = _commodity_embeddings @ query_vec  # dot product == cosine similarity here

    ranked = sorted(
        zip(_commodity_records, similarities),
        key=lambda pair: pair[1],
        reverse=True,
    )
    top = ranked[:top_n]

    matches = [
        {
            "commodity_id": commodity["id"],
            "commodity_name": commodity["name"],
            "commodity_name_hi": commodity.get("display_name_hi"),
            "category": commodity["category"],
            "similarity_percent": round(float(sim) * 100, 1),
            "properties": _to_properties(commodity),
        }
        for commodity, sim in top
    ]

    top_similarity = float(top[0][1]) if top else 0.0
    return {
        "query": query,
        "matches": matches,
        "low_confidence_match": top_similarity < threshold,
        "threshold": threshold,
    }
