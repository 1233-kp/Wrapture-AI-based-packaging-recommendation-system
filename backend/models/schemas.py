from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

BudgetTier = Literal["low", "medium", "high"]
DetailedBudgetTier = Literal["economy", "standard", "premium"]
FitLevel = Literal["good", "partial", "poor", "not_applicable"]
ConfidenceLevel = Literal["low", "medium", "high"]
Lang = Literal["en", "hi"]


class RecommendRequest(BaseModel):
    commodity_id: str = Field(
        ...,
        description="id or name of a commodity from /backend/data/commodities.json, e.g. 'banana' or 'Banana'.",
        examples=["banana"],
    )
    budget_tier: BudgetTier = Field(
        default="medium",
        description="How much packaging cost matters relative to performance.",
    )
    prioritize_sustainability: bool = Field(
        default=False,
        description="If true, recyclability/compostability is weighted more heavily than the default.",
    )
    expected_transport_days: float | None = Field(
        default=None,
        ge=0,
        description="Optional: expected time in transit/storage before the product reaches the end consumer.",
    )
    ambient_temperature_c: float | None = Field(
        default=None,
        description="Optional: expected ambient storage/transport temperature in Celsius.",
    )
    lang: Lang = Field(
        default="en",
        description="Response language for all dynamically-generated text (rationale, warnings, "
        "disclaimers). Commodity/material IDs and raw enum fields (e.g. cost_tier) are unaffected — "
        "see name_hi/material_name_hi for translated display names.",
    )


class CommoditySummary(BaseModel):
    id: str
    name: str
    name_hi: str | None = Field(
        default=None, description="Hindi display name, from commodities.json's display_name_hi. Null if not set."
    )
    category: str
    confidence: str


class MaterialRecommendation(BaseModel):
    material_id: str
    material_name: str
    material_name_hi: str | None = Field(
        default=None,
        description="Hindi display name, from packaging_materials.json's display_name_hi. Null if not set.",
    )
    score: float = Field(..., description="0-100 fit score; higher is a better match.")
    cost_tier: str
    recyclability_rating: str
    rationale: list[str]
    warnings: list[str] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    commodity: CommoditySummary
    recommendations: list[MaterialRecommendation]
    disclaimer: str = Field(
        ..., description="Generated from heuristic rules, not lab testing — in the response's requested language."
    )


class DetailedRecommendRequest(BaseModel):
    commodity_id: str = Field(
        ...,
        description="id or name of a commodity from /backend/data/commodities.json, e.g. 'banana' or 'Banana'.",
        examples=["banana"],
    )
    budget_tier: DetailedBudgetTier = Field(
        default="standard",
        description="economy = cost matters most, premium = cost matters least relative to fit.",
    )
    prioritize_sustainability: bool = Field(
        default=False,
        description="If true, re-ranks so recyclability/compostability carries much more weight.",
    )
    expected_transport_days: float | None = Field(
        default=None,
        ge=0,
        description="Optional: expected time in transit/storage before the product reaches the end consumer.",
    )
    ambient_temperature_c: float | None = Field(
        default=None,
        description="Optional: expected ambient storage/transport temperature in Celsius.",
    )
    lang: Lang = Field(
        default="en",
        description="Response language for all dynamically-generated text (rationale, warnings, "
        "trade_off_summary, cost_comparison_note, MAP gas guidance, disclaimers, ML agreement note). "
        "Commodity/material IDs and raw enum fields (e.g. cost_tier) are unaffected — see "
        "name_hi/material_name_hi for translated display names.",
    )


class MatchBreakdownItem(BaseModel):
    dimension: str = Field(..., description="Which scoring dimension this entry covers, e.g. 'moisture_barrier'.")
    commodity_property: str
    packaging_property: str
    fit: FitLevel
    weight: float = Field(..., description="Weight this dimension carried in the overall score.")
    explanation: str


class MapGasGuidance(BaseModel):
    applicable: bool = Field(..., description="False for non-produce commodities without a respiration rate.")
    respiration_rate_class: str | None
    o2_percent: dict[str, float] | None
    co2_percent: dict[str, float] | None
    n2_percent: dict[str, float] | None
    note: str


class DetailedMaterialRecommendation(BaseModel):
    material_id: str
    material_name: str
    material_name_hi: str | None = Field(
        default=None,
        description="Hindi display name, from packaging_materials.json's display_name_hi. Null if not set.",
    )
    score: float = Field(..., description="0-100 overall fit score; higher is a better match.")
    sustainability_score: float = Field(..., description="0-100 recyclability/compostability score.")
    cost_tier: str
    recyclability_rating: str
    material_confidence: ConfidenceLevel = Field(
        ..., description="Confidence level of this material's own spec data."
    )
    overall_confidence: ConfidenceLevel = Field(
        ..., description="Weaker of the commodity's and material's confidence levels — drives an 'estimated' badge."
    )
    estimated_shelf_life_days: float | None = Field(
        default=None,
        description="Heuristic estimate only, not lab-tested — how close this pairing likely gets to the "
        "commodity's typical ambient shelf life.",
    )
    trade_off_summary: str = Field(..., description="Short, explicit trade-off statement vs. the top-ranked pick.")
    match_breakdown: list[MatchBreakdownItem]
    rationale: list[str]
    warnings: list[str] = Field(default_factory=list)
    ml_confidence_score: float | None = Field(
        default=None,
        description="0-100 score from a supervised ML model trained to approximate the rules engine's "
        "scoring pattern (see /backend/training) — a corroborating second signal, not the ranking driver. "
        "Null if no model is loaded.",
    )
    estimated_cost_per_unit_inr: dict[str, float] | None = Field(
        default=None,
        description="Rough estimated cost (INR) to package 1 kg of this commodity in this material — "
        "material price (data/packaging_materials.json) times a category-level packaging-weight estimate "
        "(rules.json), times a per-material weight_multiplier correcting for format/density differences "
        "(e.g. glass uses more material mass per kg of product than a thin film). Informational only: has "
        "no effect on ranking or on budget_tier's scoring influence. Not a quote — see "
        "packaging_materials.json's cost_confidence/weight_multiplier_confidence per material for the "
        "known limitations of this estimate. Null if no cost data is available.",
    )
    cost_comparison_note: str | None = Field(
        default=None,
        description="Short delta-style comparison of this option's estimated cost against the top pick's, "
        "same reasoning pattern as trade_off_summary. Null if cost data is unavailable for either option.",
    )
    compliance_notes: list["ComplianceNote"] = Field(
        default_factory=list,
        description="Informational regulatory-consideration flags from the small rule set in "
        "data/compliance_rules.json (see engine/compliance_check.py) — NOT a certified compliance "
        "verification, and has zero effect on score/ranking. Commonly empty (e.g. glass currently "
        "triggers none of the rules); see compliance_disclaimer, present whenever any option has "
        "at least one note.",
    )


class ComplianceNote(BaseModel):
    rule_id: str
    description: str
    confidence: ConfidenceLevel
    general_reference: str = Field(
        ..., description="General regulatory area/framework this flag relates to — never a specific "
        "clause/section number we aren't confident is both correct and current."
    )


class MlAgreement(BaseModel):
    agrees: bool = Field(..., description="Whether the ML model's top pick (among the shown options) matches the rules engine's #1.")
    ml_top_pick_material_id: str
    note: str = Field(..., description="Plain-language summary of whether the two signals agree.")


class ShelfLifePrediction(BaseModel):
    predicted_shelf_life_days: float = Field(
        ..., description="typical_ambient_shelf_life_days midpoint, adjusted via Q10 for the supplied storage temperature."
    )
    shelf_life_confidence: ConfidenceLevel = Field(
        ..., description="Always 'medium' currently — category-level literature-typical Q10, not measured per-commodity kinetic data."
    )
    explanation: str = Field(..., description="Short, localized explanation of the direction/magnitude of the adjustment.")
    was_clamped: bool = Field(
        ..., description="True if the raw Q10 calculation was capped to stay within a plausible range (see data/shelf_life_rules.json's clamp config)."
    )
    disclaimer: str = Field(
        ..., description="States plainly this is a temperature-kinetics estimate, not a certified or lab-validated shelf-life claim."
    )


class DetailedRecommendResponse(BaseModel):
    commodity: CommoditySummary
    recommendations: list[DetailedMaterialRecommendation]
    map_gas_guidance: MapGasGuidance
    regulatory_note: str = Field(
        ..., description="Static disclaimer: scoring covers barrier/cost/sustainability fit only — not food-safety or regulatory compliance verification."
    )
    government_scheme_note: str = Field(
        ...,
        description="Informational note that packaging equipment upgrades may be eligible for PM-FME scheme "
        "support — always present (every recommendation involves a packaging material), distinct from "
        "compliance_notes/compliance_disclaimer. Never claims this specific recommendation is confirmed "
        "eligible, only that this category of scheme exists and may apply — see engine/government_scheme.py.",
    )
    ml_agreement: MlAgreement | None = Field(
        default=None,
        description="Whether the corroborating ML model agrees with the rules engine's top pick among the shown options. Null if no model is loaded.",
    )
    disclaimer: str = Field(
        ..., description="Generated from heuristic rules, not lab testing — in the response's requested language."
    )
    compliance_disclaimer: str | None = Field(
        default=None,
        description="Present (non-null) only when at least one shown option has non-empty compliance_notes. "
        "Always accompanies compliance_notes when they're non-empty — see ComplianceNote.",
    )
    shelf_life_prediction: ShelfLifePrediction | None = Field(
        default=None,
        description="Q10 temperature-coefficient shelf-life prediction, adjusting the commodity's typical "
        "shelf life for the supplied storage temperature. Material-independent (same for every option in "
        "this response), so it's a single top-level field. Null whenever ambient_temperature_c wasn't "
        "supplied in the request — never a fabricated default.",
    )


# ---------------------------------------------------------------------------
# reports
# ---------------------------------------------------------------------------


class ReportCreateRequest(BaseModel):
    commodity_name: str = Field(..., description="Human-readable commodity name, e.g. 'Banana'.")
    input_conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Whatever request parameters produced this recommendation (budget tier, "
        "sustainability toggle, transport days, temperature, etc.) — stored as-is for the record.",
    )
    recommendation: dict[str, Any] = Field(
        ...,
        description="The recommendation payload to persist — normally the JSON body returned by "
        "POST /recommend/detailed, so /reports/{id}/export has everything it needs.",
    )


FeedbackOutcome = Literal["spoiled_early", "as_expected", "lasted_longer"]


class Report(BaseModel):
    id: UUID
    user_id: UUID
    commodity_name: str
    input_conditions: dict[str, Any]
    recommendation: dict[str, Any]
    created_at: datetime
    feedback_outcome: FeedbackOutcome | None = Field(
        default=None,
        description="Optional user-submitted 'was this accurate?' outcome — pure data capture, "
        "nothing reads this to retrain or auto-adjust future recommendations.",
    )
    feedback_submitted_at: datetime | None = None


class ReportListResponse(BaseModel):
    reports: list[Report]
    total: int
    limit: int
    offset: int


class ReportFeedbackRequest(BaseModel):
    outcome: FeedbackOutcome


class PublicReportView(BaseModel):
    """Deliberately narrow — this is what GET /reports/{id}/public and the QR
    code on an exported report expose to anyone, with no account required.
    No user_id, no email, nothing about who generated the report."""

    trace_id: str = Field(..., description="Short human-readable traceability id, e.g. 'PSA-4F2A9C1B'.")
    commodity_name: str
    material_name: str
    otr_cm3_m2_day_atm: dict[str, float] | None
    wvtr_g_m2_day: dict[str, float] | None
    thickness_range_micron: dict[str, float] | None
    sustainability_score: float
    generated_at: datetime


# ---------------------------------------------------------------------------
# cold-chain excursion re-recommendation (manual entry, not IoT/sensor)
# ---------------------------------------------------------------------------


class ColdChainExcursionRequest(BaseModel):
    temperature_reached_c: float = Field(
        ..., description="The temperature the product actually reached during the excursion, in Celsius."
    )
    duration_hours: float = Field(
        ..., ge=0, le=720, description="How long the product was at/near that temperature."
    )
    lang: Lang = Field(default="en", description="Response language for action_message/explanation/disclaimer.")


class ColdChainEvent(BaseModel):
    """One logged excursion — a new, append-only record, never a rewrite of
    the report or of an earlier logged event."""

    id: UUID
    report_id: UUID
    temperature_reached_c: float
    duration_hours: float
    remaining_shelf_life_days: float
    action_urgent: bool
    created_at: datetime


class ColdChainExcursionResponse(BaseModel):
    event: ColdChainEvent
    action_message: str = Field(..., description="Plain-language action suggestion, e.g. 'sell within X hours'.")
    explanation: str
    disclaimer: str


class ColdChainEventListResponse(BaseModel):
    events: list[ColdChainEvent]


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------


class ProfileResponse(BaseModel):
    user_id: UUID
    display_name: str | None
    avatar_url: str | None
    preferred_budget_tier: BudgetTier | None
    prioritize_sustainability: bool
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    """All fields optional — PATCH semantics, only supplied fields are changed."""

    display_name: str | None = None
    avatar_url: str | None = None
    preferred_budget_tier: BudgetTier | None = None
    prioritize_sustainability: bool | None = None


# ---------------------------------------------------------------------------
# commodities
# ---------------------------------------------------------------------------


class CommodityListResponse(BaseModel):
    commodities: list[CommoditySummary]


# ---------------------------------------------------------------------------
# packaging materials (reference library)
# ---------------------------------------------------------------------------


class MaterialSummary(BaseModel):
    """The subset of a packaging_materials.json record safe and useful to
    expose as a standalone reference page — the same fields already used
    elsewhere in scoring and reports, no internal-only fields like the cost
    confidence notes or weight multiplier used by the scoring engine."""

    id: str
    name: str
    name_hi: str | None = Field(
        default=None, description="Hindi display name, from packaging_materials.json's display_name_hi. Null if not set."
    )
    category: str
    otr_cm3_m2_day_atm: dict[str, float] | None
    wvtr_g_m2_day: dict[str, float] | None
    thickness_range_micron: dict[str, float] | None
    cost_tier: str
    estimated_cost_per_kg_inr: dict[str, float] | None
    recyclability_rating: str
    typical_use_cases: list[str]
    confidence: str


class MaterialListResponse(BaseModel):
    materials: list[MaterialSummary]


# ---------------------------------------------------------------------------
# commodity matching (free-text -> closest existing commodity, ML fallback)
# ---------------------------------------------------------------------------


class CommodityMatchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Free-text description of a commodity not in the dropdown, e.g. 'dragon fruit' or "
        "'a soft, ripe stone fruit like a peach'.",
        examples=["dragon fruit"],
    )


class CommodityBorrowedProperties(BaseModel):
    moisture_content_percent: dict[str, float] | None
    fat_content_percent: dict[str, float] | None
    ph_range: dict[str, float] | None
    respiration_rate_class: str | None
    typical_ambient_shelf_life_days: dict[str, float] | None
    confidence: ConfidenceLevel


class CommodityMatch(BaseModel):
    commodity_id: str
    commodity_name: str
    commodity_name_hi: str | None = Field(default=None, description="Hindi display name. Null if not set.")
    category: str
    similarity_percent: float = Field(..., description="Cosine similarity to the query, 0-100.")
    properties: CommodityBorrowedProperties = Field(
        ..., description="This existing commodity's properties — what would be borrowed if selected."
    )


class CommodityMatchResponse(BaseModel):
    query: str
    matches: list[CommodityMatch]
    low_confidence_match: bool = Field(
        ...,
        description="True when even the top match's similarity is below the confidence threshold — "
        "the frontend should warn more strongly that this is a rough estimate.",
    )
    threshold: float = Field(..., description="The similarity threshold (0-1) used to set low_confidence_match.")


# ---------------------------------------------------------------------------
# logistics (source -> destination transport-distance estimation)
# ---------------------------------------------------------------------------

LocationSource = Literal["live", "offline"]
TransportSourceUsed = Literal["live_geocoding", "offline_fallback"]


class TransportEstimateRequest(BaseModel):
    source: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Free-text origin location, e.g. 'Nashik' or 'Nashik, Maharashtra'.",
        examples=["Nashik"],
    )
    destination: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Free-text destination location, e.g. 'Delhi'.",
        examples=["Delhi"],
    )


class ResolvedVia(BaseModel):
    source: LocationSource
    destination: LocationSource


class TransportEstimateResponse(BaseModel):
    distance_km: float = Field(..., description="Haversine (straight-line) distance — NOT a road route.")
    estimated_transport_days: float = Field(
        ..., description="Rough planning estimate from distance_km via rules.json's logistics config."
    )
    source_used: TransportSourceUsed = Field(
        ...,
        description="'live_geocoding' only if BOTH locations resolved via live Nominatim lookup; "
        "'offline_fallback' if either fell back to the static major_cities_india.json table.",
    )
    resolved_via: ResolvedVia = Field(..., description="Per-location resolution path, for transparency.")
    disclaimer: str = Field(
        ..., description="Wording adapts to source_used — always makes clear this is a straight-line estimate."
    )


class LocationNotFoundResponse(BaseModel):
    """Shape of the 422 error body raised when a location resolves on neither path."""

    message: str
    unresolved_location: str
    suggestions: list[str] = Field(..., description="A few example cities from the offline table to try instead.")


# ---------------------------------------------------------------------------
# FAQ (static content + free-text template-matching assistant)
# ---------------------------------------------------------------------------


class FaqItem(BaseModel):
    id: str
    question: str
    question_hi: str | None = Field(default=None, description="Hindi translation. Null if not set.")
    answer: str
    answer_hi: str | None = Field(default=None, description="Hindi translation. Null if not set.")


class FaqListResponse(BaseModel):
    faqs: list[FaqItem]


class FaqMatchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Free-text question for the FAQ assistant.",
        examples=["Is this free to use?"],
    )


class FaqMatchResponse(BaseModel):
    query: str
    matched: bool = Field(..., description="Whether the best-matching FAQ cleared the similarity threshold.")
    faq: FaqItem | None = Field(
        default=None,
        description="The matched FAQ's existing, hand-written content — never a generated answer. "
        "Null when nothing cleared the threshold; the caller should show an honest fallback, not a guess.",
    )
    similarity_percent: float = Field(..., description="Cosine similarity of the best match, 0-100.")
    threshold: float = Field(..., description="The similarity threshold (0-1) used to decide `matched`.")
