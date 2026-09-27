"""Unit tests for backend/engine/faq_matcher.py.

Like test_commodity_matcher.py, these load the real embedding model (no
mocking) — the whole point is verifying genuine embedding-based matching
quality, reusing the same shared model as commodity matching (see
engine/embedding_model.py). Every paraphrase test case below was empirically
checked to actually score where asserted before being written, not assumed.
"""

from engine.faq_matcher import LOW_CONFIDENCE_SIMILARITY_THRESHOLD, list_faqs, match_faq


def test_list_faqs_returns_sixteen_items():
    faqs = list_faqs()
    assert len(faqs) == 16
    assert all({"id", "question", "answer"} <= faq.keys() for faq in faqs)


def test_qr_verification_paraphrase_matches():
    result = match_faq("What happens when I scan the QR code on my report?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "qr-verification"


def test_hindi_support_paraphrase_matches():
    result = match_faq("Does the app work in Hindi?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "hindi-support"


def test_commodity_not_listed_paraphrase_matches():
    result = match_faq("My commodity is missing from the dropdown")
    assert result["matched"] is True
    assert result["faq"]["id"] == "commodity-not-listed"


def test_commodities_supported_paraphrase_matches():
    """Regression test: this used to incorrectly match commodity-not-listed
    (a different question) because both share the word 'commodity' — see
    the reworded commodities-supported/commodity-not-listed questions in
    data/faq.json."""
    result = match_faq("What commodities we have?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "commodities-supported"


def test_commodities_supported_alt_phrasing_matches():
    result = match_faq("What commodities does the app support?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "commodities-supported"


def test_materials_supported_paraphrase_matches():
    """Regression test: there was previously no dedicated FAQ answering
    'what materials do you support' at all."""
    result = match_faq("What materials are supported?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "materials-supported"


def test_materials_supported_alt_phrasing_matches():
    result = match_faq("Which packaging materials do you support?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "materials-supported"


def test_commodities_and_materials_questions_never_cross_match():
    """The two most confusable pairs in the FAQ set — commodities vs.
    materials, and "what's supported" vs. "mine isn't listed" — should
    never resolve to each other, even though they share vocabulary."""
    commodities = match_faq("What commodities we have?")
    materials = match_faq("What materials are supported?")
    not_listed = match_faq("My commodity is missing from the dropdown")

    assert commodities["faq"]["id"] == "commodities-supported"
    assert materials["faq"]["id"] == "materials-supported"
    assert not_listed["faq"]["id"] == "commodity-not-listed"


def test_data_privacy_paraphrase_matches():
    result = match_faq("Who can view my saved recommendations?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "data-privacy"


def test_pdf_export_paraphrase_matches():
    result = match_faq("Can I get a PDF of my recommendation?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "pdf-export"


def test_sustainability_score_paraphrase_matches():
    result = match_faq("How do you calculate the sustainability score?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "sustainability-score"


def test_accuracy_paraphrase_matches():
    result = match_faq("How accurate are the predictions?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "accuracy"


def test_compliance_paraphrase_matches():
    result = match_faq("Are the compliance warnings legally binding?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "compliance-flags"


def test_confidence_levels_paraphrase_matches():
    result = match_faq("What does low confidence mean?")
    assert result["matched"] is True
    assert result["faq"]["id"] == "confidence-levels"


def test_near_exact_phrasing_is_high_confidence():
    """Restating an existing FAQ question almost verbatim should be a very
    high-similarity match, not just barely over the threshold."""
    result = match_faq("Is Wrapture accurate?")
    assert result["faq"]["id"] == "accuracy"
    assert result["similarity_percent"] > 75


def test_clearly_out_of_scope_question_falls_back():
    """A question with no relationship to anything in the FAQ should not
    return a confident-sounding wrong answer — it should fall back."""
    result = match_faq("What is the capital of France?")
    assert result["matched"] is False
    assert result["faq"] is None
    assert result["similarity_percent"] < LOW_CONFIDENCE_SIMILARITY_THRESHOLD * 100


def test_gibberish_question_falls_back():
    result = match_faq("asdkjfh qwerty random nonsense gibberish")
    assert result["matched"] is False
    assert result["faq"] is None


def test_unrelated_request_falls_back_rather_than_guessing():
    """A free-form request unrelated to the app (not even phrased as a
    question) should also fall back, not be force-matched to the nearest
    FAQ by default."""
    result = match_faq("Write me a poem about cats")
    assert result["matched"] is False
    assert result["faq"] is None


def test_similarity_score_reflects_match_strength():
    """A near-exact phrasing should score much higher than a looser,
    still-correct paraphrase — similarity_percent is meant to convey real
    confidence (so the frontend can show a borderline match as uncertain),
    not just clear or not clear a binary threshold."""
    strong = match_faq("Is Wrapture accurate?")
    looser = match_faq("How accurate are the predictions?")
    assert strong["faq"]["id"] == looser["faq"]["id"] == "accuracy"
    assert strong["similarity_percent"] > looser["similarity_percent"]


def test_threshold_is_configurable_per_call():
    strict = match_faq("Is this free to use?", threshold=0.99)
    lenient = match_faq("Is this free to use?", threshold=0.0)
    assert strict["matched"] is False
    assert lenient["matched"] is True
