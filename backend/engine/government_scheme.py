"""Lightweight, informational note about a real central government scheme
that may apply to packaging equipment upgrades — same "informational flag,
not a certification" spirit as engine/compliance_check.py, but simpler:
this note is unconditional (every /recommend/detailed response involves a
packaging material recommendation, so it always applies) rather than
triggered by rule matching against a (commodity, material) pair.

Deliberately does NOT claim this specific recommendation is confirmed
eligible for the PM-FME scheme — only that this category of central
government support exists and may apply, with actual eligibility
determined case-by-case by the reader's own State Nodal Agency. See
tests/test_government_scheme.py for the literal check that no unqualified
"eligible"/"qualifies" claim appears in either language.
"""

from engine.i18n_strings import t


def government_scheme_note(lang: str = "en") -> str:
    return t("government_scheme_note", lang)
