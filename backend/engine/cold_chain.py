"""Cold-chain temperature-excursion re-recommendation.

Manual entry only — no IoT/sensor integration. A user logs a temperature
excursion (temperature reached + duration) against one of their own saved
reports, and this recalculates the remaining shelf life by reusing the
existing Q10 model in engine/shelf_life.py verbatim, on the real commodity
record — it does not duplicate or modify that math, only calls it with the
excursion temperature. Deliberately does not touch engine/recommender.py's
scoring/ranking or engine/shelf_life.py itself.
"""

from __future__ import annotations

from typing import Any

from engine.i18n_strings import t
from engine.recommender import find_commodity
from engine.shelf_life import predict_shelf_life

# Below this many remaining hours, the action suggestion becomes urgent
# ("sell within X hours") instead of "no action needed". A single, simple
# cutoff by design — see the feature request this was built for.
URGENT_THRESHOLD_HOURS = 24.0


def recalculate_after_excursion(
    report: dict[str, Any],
    temperature_reached_c: float,
    duration_hours: float,
    lang: str = "en",
) -> dict[str, Any] | None:
    """Returns {remaining_shelf_life_days, remaining_shelf_life_hours,
    action_urgent, action_message, explanation, disclaimer} for one logged
    excursion against `report` (a full reports-table row, as returned by
    get_report()) — or None if there isn't enough data on the report to
    compute this (commodity not identifiable, or no Q10 config for its
    category — same "never fabricate" cases predict_shelf_life() itself
    already handles).

    The excursion temperature is treated as the new effective storage
    condition for the commodity's shelf life going forward: predict_shelf_life()
    is called once, on the real commodity record, at the excursion
    temperature — reusing exactly the same Q10 formula, reference
    temperature, and clamping every other shelf-life prediction in this app
    uses, not a synthetic or re-derived baseline. The excursion's own
    duration is then subtracted, since that time has already elapsed under
    the excursion condition.
    """
    recommendation = report.get("recommendation") or {}
    commodity_summary = recommendation.get("commodity") or {}
    commodity_id = commodity_summary.get("id")
    if not commodity_id:
        return None

    commodity = find_commodity(commodity_id)
    if commodity is None:
        return None

    temp_adjusted = predict_shelf_life(commodity, temperature_reached_c, lang)
    if temp_adjusted is None:
        return None

    predicted_at_excursion_temp = temp_adjusted["predicted_shelf_life_days"]
    remaining_days = round(max(0.0, predicted_at_excursion_temp - duration_hours / 24), 2)
    remaining_hours = round(remaining_days * 24, 1)

    action_urgent = remaining_hours < URGENT_THRESHOLD_HOURS
    if remaining_hours <= 0:
        action_message = t("cold_chain_action_expired", lang)
    elif action_urgent:
        action_message = t("cold_chain_action_urgent", lang, hours=remaining_hours)
    else:
        action_message = t("cold_chain_action_ok", lang)

    explanation = t(
        "cold_chain_explanation",
        lang,
        temp=f"{temperature_reached_c:g}",
        duration=f"{duration_hours:g}",
        predicted=predicted_at_excursion_temp,
        remaining=remaining_days,
    )

    return {
        "remaining_shelf_life_days": remaining_days,
        "remaining_shelf_life_hours": remaining_hours,
        "action_urgent": action_urgent,
        "action_message": action_message,
        "explanation": explanation,
        "disclaimer": t("cold_chain_disclaimer", lang),
    }
