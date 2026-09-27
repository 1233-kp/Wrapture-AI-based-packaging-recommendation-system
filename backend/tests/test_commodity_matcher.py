"""Unit tests for backend/engine/commodity_matcher.py.

These load the real embedding model (no mocking) since the whole point is
verifying genuine embedding-based matching quality — the first test in the
module pays the one-time model load cost, subsequent tests reuse the cached
model/embeddings via the module-level cache in commodity_matcher.py. No
network access needed — the model files are bundled in
models/embedding_cache/ (see engine/embedding_model.py).
"""

from engine.commodity_matcher import LOW_CONFIDENCE_SIMILARITY_THRESHOLD, match_commodities


def test_unrelated_query_triggers_low_confidence():
    """A query with no sensible commodity match at all should land well below
    the threshold and be flagged low_confidence_match."""
    result = match_commodities("a computer motherboard")
    assert result["low_confidence_match"] is True
    assert result["matches"][0]["similarity_percent"] < LOW_CONFIDENCE_SIMILARITY_THRESHOLD * 100


def test_gibberish_query_triggers_low_confidence():
    result = match_commodities("asdkjfh qwerty random nonsense gibberish")
    assert result["low_confidence_match"] is True


def test_returns_top_3_matches_by_default():
    result = match_commodities("dragon fruit")
    assert len(result["matches"]) == 3
    scores = [m["similarity_percent"] for m in result["matches"]]
    assert scores == sorted(scores, reverse=True)


def test_dragon_fruit_ranks_fresh_fruit_highly():
    """We don't have dragon fruit in the database, but the closest matches
    should still cluster in a sensible category (fresh fruit), not something
    unrelated like spices or meat."""
    result = match_commodities("dragon fruit")
    assert result["matches"][0]["category"] == "fresh_fruit"


def test_kiwi_fruit_ranks_fresh_fruit_highly():
    result = match_commodities("kiwi fruit")
    assert result["matches"][0]["category"] == "fresh_fruit"


def test_stone_fruit_description_ranks_fresh_fruit_highly():
    result = match_commodities("a soft, ripe stone fruit like a peach")
    assert result["matches"][0]["category"] == "fresh_fruit"


def test_spice_description_ranks_spices_highly():
    result = match_commodities("aromatic ground spice powder used in curry")
    assert result["matches"][0]["category"] == "spices"


def test_leafy_green_description_ranks_spinach_top():
    result = match_commodities("a leafy salad green")
    assert result["matches"][0]["commodity_id"] == "spinach"


def test_near_exact_phrasing_of_existing_commodity_is_high_confidence():
    """When the free-text query essentially just re-describes an existing
    commodity in different words, that should clear the confidence threshold
    — this is the case the threshold is meant to let through."""
    result = match_commodities("raw whole chicken")
    assert result["matches"][0]["commodity_id"] == "chicken_fresh"
    assert result["low_confidence_match"] is False


def test_matches_include_borrowed_properties():
    result = match_commodities("kiwi fruit")
    top = result["matches"][0]
    props = top["properties"]
    assert props["moisture_content_percent"] is not None
    assert "min" in props["moisture_content_percent"]
    assert "max" in props["moisture_content_percent"]
    assert props["confidence"] in {"low", "medium", "high"}


def test_threshold_is_configurable_per_call():
    # A very high threshold should force low_confidence_match=True even for a
    # normally-confident query; a threshold of 0 should never flag it.
    strict = match_commodities("raw whole chicken", threshold=0.99)
    lenient = match_commodities("raw whole chicken", threshold=0.0)
    assert strict["low_confidence_match"] is True
    assert lenient["low_confidence_match"] is False
