"""Parallel English/Hindi templates for every dynamically-generated sentence
the rules engine produces (rationale, warnings, explanations, trade-off
summaries, cost comparisons, MAP gas guidance, disclaimers, ML agreement
notes).

WHY REAL PARALLEL TEMPLATES, NOT MACHINE TRANSLATION AT REQUEST TIME: the
English sentences are built by choosing between different phrasings based on
which rule branch fired (e.g. "suits a high-fat commodity" vs. "suits this
commodity"). Translating the already-assembled English string at request
time would (a) cost a network call or a heavy local model per sentence, (b)
risk mistranslating the numbers/units embedded in the sentence, and (c)
produce stiff, literal Hindi. Instead, each template below is authored
directly in Hindi for the same logical branch the English one covers — same
underlying logic (which branch fires, which numbers appear), independently
natural phrasing per language. This mirrors exactly how the English
sentences themselves were hand-written in engine/recommender.py, just in a
second language.

Hindi register: plain, everyday Hindi appropriate for farmers and small food
businesses — not formal/Sanskritized. Technical terms with no common Hindi
equivalent (WVTR, OTR, pH, INR, material/commodity category ids) are kept as
literal tokens, same as how an English-speaking food-science text would keep
them; only the surrounding sentence structure is translated, per the same
"numbers, units, and names stay as-is" rule used for material/commodity IDs
elsewhere in this project.

Usage: `t("moisture_fit_rationale", lang, wvtr=12.3, moisture=90, target=40)`.
Falls back to English if `lang` isn't a recognized locale or a key is
somehow missing — never raises and never returns blank text to a user.
"""

from __future__ import annotations

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "hi")


def _lang_or_default(lang: str | None) -> str:
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


# ---------------------------------------------------------------------------
# Small enum-style word lookups — respiration class, cost tier, category
# names, etc. appear *inside* the sentence templates below (e.g. "this
# commodity's 'high' respiration rate"). Translating the template but
# leaving these words in English would produce mixed-language sentences,
# which defeats the point — so every enum value referenced by a template
# gets its own small translated word list here.
# ---------------------------------------------------------------------------

RESPIRATION_CLASS_WORD = {
    "low": {"en": "low", "hi": "हल्की"},
    "moderate": {"en": "moderate", "hi": "मध्यम"},
    "high": {"en": "high", "hi": "तेज़"},
    "very_high": {"en": "very high", "hi": "बहुत तेज़"},
}

COST_TIER_WORD = {
    "low": {"en": "Low", "hi": "कम"},
    "medium": {"en": "Medium", "hi": "मध्यम"},
    "high": {"en": "High", "hi": "उच्च"},
}

# Lowercase variant of COST_TIER_WORD, for use inside a parenthetical like
# "(high cost tolerance)" rather than as a standalone capitalized label.
COST_TOLERANCE_WORD = {
    "low": {"en": "low", "hi": "कम"},
    "medium": {"en": "medium", "hi": "मध्यम"},
    "high": {"en": "high", "hi": "उच्च"},
}

# The user-facing budget-tier vocabulary /recommend/detailed actually accepts
# (economy/standard/premium) — distinct from COST_TIER_WORD, which is the
# internal low/medium/high vocabulary those map to for scoring purposes. Used
# to show the REQUESTED value literally, alongside what it maps to internally,
# rather than silently displaying the internal mapping as if it were the input.
DETAILED_BUDGET_TIER_WORD = {
    "economy": {"en": "Economy", "hi": "किफ़ायती"},
    "standard": {"en": "Standard", "hi": "सामान्य"},
    "premium": {"en": "Premium", "hi": "प्रीमियम"},
}

OTR_REASON_WORD = {
    "high-fat": {"en": "high-fat", "hi": "अधिक वसा"},
    "category": {"en": "category", "hi": "श्रेणी"},
    "default": {"en": "default", "hi": "सामान्य"},
}

COMMODITY_CATEGORY_WORD = {
    "fresh_fruit": {"en": "fresh fruit", "hi": "ताज़ा फल"},
    "fresh_vegetable": {"en": "fresh vegetable", "hi": "ताज़ी सब्ज़ी"},
    "dairy": {"en": "dairy", "hi": "डेयरी"},
    "dry_goods_grains": {"en": "dry goods/grains", "hi": "सूखा अनाज/दाल"},
    "spices": {"en": "spices", "hi": "मसाले"},
    "meat_fish": {"en": "meat/fish", "hi": "मांस/मछली"},
    "bakery": {"en": "bakery", "hi": "बेकरी"},
    "nuts_dried_fruits": {"en": "nuts/dried fruits", "hi": "मेवे/सूखे मेवे"},
    "beverages": {"en": "beverages", "hi": "पेय पदार्थ"},
    "frozen_foods": {"en": "frozen foods", "hi": "जमे हुए खाद्य पदार्थ"},
    "ready_to_eat_snacks": {"en": "ready-to-eat snacks", "hi": "तैयार नाश्ता/स्नैक्स"},
}

MATERIAL_CATEGORY_WORD = {
    "flexible_film": {"en": "flexible film", "hi": "लचीली फिल्म"},
    "flexible_film_or_rigid": {"en": "flexible film or rigid", "hi": "लचीली फिल्म या कठोर"},
    "rigid_or_film": {"en": "rigid or film", "hi": "कठोर या फिल्म"},
    "flexible_film_laminate": {"en": "flexible film laminate", "hi": "लचीली फिल्म लैमिनेट"},
    "rigid": {"en": "rigid", "hi": "कठोर"},
    "rigid_paper": {"en": "rigid paper", "hi": "कठोर कागज़/पेपरबोर्ड"},
}


def word(table: dict[str, dict[str, str]], value: str | None, lang: str) -> str:
    """Looks up an enum-style value in one of the WORD tables above. Falls
    back to the raw value (underscores -> spaces) if not found, so an
    unrecognized/future enum value never crashes or renders blank."""
    lang = _lang_or_default(lang)
    entry = table.get(value or "")
    if entry:
        return entry.get(lang, entry["en"])
    return (value or "").replace("_", " ")


# ---------------------------------------------------------------------------
# Sentence templates: key -> {"en": ..., "hi": ...}. Values use str.format()
# placeholders — callers pass already-formatted numbers (e.g. f"{x:.0f}")
# as keyword arguments, same as the original f-strings did, so number
# formatting itself is locale-independent (Hindi readers of this app are
# already used to Latin-numeral technical specs like WVTR/OTR values).
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, dict[str, str]] = {
    # -- moisture_fit --
    "moisture_fit_rationale": {
        "en": "Moisture barrier (WVTR ~{wvtr} g/m2/day) fits a {moisture} moisture commodity (target <= {target} g/m2/day).",
        "hi": "नमी-रोधक क्षमता (WVTR ~{wvtr} g/m2/day) {moisture} नमी वाले उत्पाद के लिए उपयुक्त है (आवश्यक मानक <= {target} g/m2/day)।",
    },
    "moisture_fit_warning": {
        "en": "WVTR (~{wvtr} g/m2/day) is higher than ideal (target <= {target}) for this commodity's moisture content.",
        "hi": "इस उत्पाद की नमी के हिसाब से WVTR (~{wvtr} g/m2/day) आदर्श मानक (<= {target}) से अधिक है।",
    },
    "moisture_property_known": {
        "en": "Moisture content ~{moisture}",
        "hi": "नमी की मात्रा ~{moisture}",
    },
    "moisture_property_unknown": {
        "en": "Moisture content unknown",
        "hi": "नमी की मात्रा अज्ञात है",
    },
    "moisture_packaging_property": {
        "en": "WVTR ~{wvtr} g/m2/day (target <= {target} g/m2/day)",
        "hi": "WVTR ~{wvtr} g/m2/day (आवश्यक मानक <= {target} g/m2/day)",
    },
    "moisture_explanation_ok": {
        "en": "Meets the moisture-tightness target for this commodity.",
        "hi": "इस उत्पाद के लिए नमी-रोधक मानक को पूरा करता है।",
    },
    "moisture_explanation_not_ok": {
        "en": "Wetter (more moisture-permeable) than the target for this commodity.",
        "hi": "इस उत्पाद के लिए तय मानक से अधिक नमी-पारगम्य है।",
    },
    # -- oxygen_fit --
    "oxygen_rationale_high_fat": {
        "en": "Oxygen barrier (OTR ~{otr} cm3/m2/day) suits a high-fat commodity (target <= {target} cm3/m2/day/atm).",
        "hi": "ऑक्सीजन-रोधक क्षमता (OTR ~{otr} cm3/m2/day) अधिक वसा वाले उत्पाद के लिए उपयुक्त है (आवश्यक मानक <= {target} cm3/m2/day/atm)।",
    },
    "oxygen_rationale_general": {
        "en": "Oxygen barrier (OTR ~{otr} cm3/m2/day) suits this commodity (target <= {target} cm3/m2/day/atm).",
        "hi": "ऑक्सीजन-रोधक क्षमता (OTR ~{otr} cm3/m2/day) इस उत्पाद के लिए उपयुक्त है (आवश्यक मानक <= {target} cm3/m2/day/atm)।",
    },
    "oxygen_warning_high_fat": {
        "en": "OTR (~{otr} cm3/m2/day) is higher than ideal for a high-fat commodity ({fat} fat) — increases oxidative rancidity risk.",
        "hi": "अधिक वसा ({fat} वसा) वाले इस उत्पाद के लिए OTR (~{otr} cm3/m2/day) आदर्श मानक से अधिक है — इससे ऑक्सीकरण (रैंसिडिटी) का खतरा बढ़ता है।",
    },
    "oxygen_warning_category": {
        "en": "OTR (~{otr} cm3/m2/day) is higher than ideal for this commodity's category ({category}) — risks aroma loss or reduced freshness even though fat content alone wouldn't flag it.",
        "hi": "इस उत्पाद की श्रेणी ({category}) के लिए OTR (~{otr} cm3/m2/day) आदर्श मानक से अधिक है — भले ही वसा की मात्रा अकेले चिंताजनक न लगे, फिर भी सुगंध या ताज़गी में कमी का खतरा है।",
    },
    "oxygen_property_known": {
        "en": "Fat/oil content ~{fat}",
        "hi": "वसा/तेल की मात्रा ~{fat}",
    },
    "oxygen_property_unknown": {
        "en": "Fat/oil content unknown",
        "hi": "वसा/तेल की मात्रा अज्ञात है",
    },
    "otr_value": {
        "en": "OTR ~{otr} cm3/m2/day/atm",
        "hi": "OTR ~{otr} cm3/m2/day/atm",
    },
    "target_suffix": {
        "en": " (target <= {target})",
        "hi": " (आवश्यक मानक <= {target})",
    },
    "oxygen_explanation_not_applicable": {
        "en": "Governed by respiration/breathability instead of a rancidity-style barrier target for actively-respiring produce.",
        "hi": "सक्रिय रूप से सांस लेने वाले ताज़े उत्पाद के लिए यह रैंसिडिटी-प्रकार के बैरियर मानक की बजाय श्वसन/वायु-पारगम्यता पर निर्भर करता है।",
    },
    "oxygen_explanation_ok": {
        "en": "Meets the oxygen-barrier target for this commodity.",
        "hi": "इस उत्पाद के लिए ऑक्सीजन-रोधक मानक को पूरा करता है।",
    },
    "oxygen_explanation_not_ok": {
        "en": "More oxygen-permeable than the target for this commodity ({reason}-driven barrier requirement).",
        "hi": "इस उत्पाद के लिए तय मानक से अधिक ऑक्सीजन-पारगम्य है ({reason} के आधार पर तय बैरियर आवश्यकता)।",
    },
    # -- respiration_fit --
    "respiration_rationale_match": {
        "en": "Breathability (OTR ~{otr}) matches this commodity's '{cls}' respiration rate — reduces condensation/fermentation risk.",
        "hi": "वायु-पारगम्यता (OTR ~{otr}) इस उत्पाद की '{cls}' श्वसन दर से मेल खाती है — इससे नमी जमने और किण्वन (फर्मेंटेशन) का खतरा कम होता है।",
    },
    "respiration_warning_too_tight": {
        "en": "This material is a much stronger oxygen barrier than a '{cls}' respiration produce item needs — risk of moisture condensation, off-odors, or anaerobic fermentation unless the pack is vented or perforated.",
        "hi": "यह सामग्री '{cls}' श्वसन दर वाले उत्पाद की ज़रूरत से कहीं अधिक मज़बूत ऑक्सीजन-रोधक है — अगर पैक में छेद या वेंट न हों तो नमी जमने, बदबू आने या ऑक्सीजन-रहित किण्वन का खतरा है।",
    },
    "respiration_warning_too_loose": {
        "en": "This material is more permeable than typically needed for a '{cls}' respiration item — may dry out faster than necessary.",
        "hi": "यह सामग्री '{cls}' श्वसन दर वाले उत्पाद के लिए सामान्यतः ज़रूरी मात्रा से अधिक पारगम्य है — इससे उत्पाद ज़रूरत से पहले सूख सकता है।",
    },
    "respiration_explanation_match": {
        "en": "Permeability falls within the band this respiration rate needs.",
        "hi": "पारगम्यता इस श्वसन दर के लिए ज़रूरी सीमा के भीतर है।",
    },
    "respiration_explanation_tight": {
        "en": "Tighter barrier than this respiration rate needs; risks condensation/anaerobic spoilage.",
        "hi": "इस श्वसन दर की ज़रूरत से अधिक कसा हुआ बैरियर; नमी जमने या ऑक्सीजन-रहित खराबी का खतरा।",
    },
    "respiration_explanation_loose": {
        "en": "More permeable than this respiration rate strictly needs; may dry out faster.",
        "hi": "इस श्वसन दर की सख्त ज़रूरत से अधिक पारगम्य; उत्पाद जल्दी सूख सकता है।",
    },
    "respiration_property": {
        "en": "Respiration rate class: {cls} (target OTR {min}-{max} cm3/m2/day/atm)",
        "hi": "श्वसन दर श्रेणी: {cls} (आवश्यक OTR {min}-{max} cm3/m2/day/atm)",
    },
    "respiration_property_na": {
        "en": "Not a respiring fresh-produce item",
        "hi": "यह सांस लेने वाला ताज़ा उत्पाद नहीं है",
    },
    "respiration_explanation_na": {
        "en": "This dimension only applies to fresh produce with an active respiration rate.",
        "hi": "यह पहलू केवल सक्रिय श्वसन दर वाले ताज़े उत्पादों पर लागू होता है।",
    },
    # -- respiration_class_packaging_boost --
    "boost_rationale": {
        "en": "Explicitly designed/tagged for produce ventilation — a strong match for this '{cls}' respiration commodity.",
        "hi": "उत्पाद के लिए वायु-संचार हेतु विशेष रूप से डिज़ाइन/चिह्नित — '{cls}' श्वसन दर वाले इस उत्पाद के लिए बेहतरीन विकल्प।",
    },
    "boost_warning": {
        "en": "Not a purpose-built breathable/vented material — a dedicated option (e.g. micro-perforated film or a vented clamshell) would serve this '{cls}' respiration commodity better.",
        "hi": "यह सांस लेने योग्य/वेंटेड सामग्री के रूप में विशेष रूप से नहीं बनाई गई है — '{cls}' श्वसन दर वाले इस उत्पाद के लिए माइक्रो-छिद्रित फिल्म या वेंटेड क्लैमशेल जैसा समर्पित विकल्प बेहतर रहेगा।",
    },
    "boost_property_applicable": {
        "en": "Respiration rate class: {cls}",
        "hi": "श्वसन दर श्रेणी: {cls}",
    },
    "boost_property_na": {
        "en": "Respiration rate not in the boosted class list",
        "hi": "श्वसन दर इस विशेष सूची में शामिल नहीं है",
    },
    "boost_packaging_tagged": {
        "en": "Tagged breathable/vented",
        "hi": "सांस लेने योग्य/वेंटेड के रूप में चिह्नित",
    },
    "boost_packaging_not_tagged": {
        "en": "Not tagged breathable/vented",
        "hi": "सांस लेने योग्य/वेंटेड के रूप में चिह्नित नहीं",
    },
    "boost_explanation_tagged": {
        "en": "Tagged breathable/vented — a strong match for this respiration rate.",
        "hi": "सांस लेने योग्य/वेंटेड के रूप में चिह्नित — इस श्वसन दर के लिए बेहतरीन विकल्प।",
    },
    "boost_explanation_not_tagged": {
        "en": "Not tagged breathable/vented; a purpose-built option would serve this respiration rate better.",
        "hi": "सांस लेने योग्य/वेंटेड के रूप में चिह्नित नहीं; इस श्वसन दर के लिए विशेष रूप से बनाया गया विकल्प बेहतर रहेगा।",
    },
    "boost_explanation_na": {
        "en": "Not applicable — this commodity's respiration rate isn't in the boosted class list.",
        "hi": "लागू नहीं — इस उत्पाद की श्वसन दर इस विशेष सूची में शामिल नहीं है।",
    },
    # -- category_fit --
    "category_rationale": {
        "en": "Material type ({material_cat}) is a common fit for {commodity_cat} products.",
        "hi": "सामग्री का प्रकार ({material_cat}) {commodity_cat} उत्पादों के लिए सामान्यतः उपयुक्त माना जाता है।",
    },
    "category_explanation_match": {
        "en": "Commonly used material type for this commodity category.",
        "hi": "इस उत्पाद श्रेणी के लिए सामान्यतः इस्तेमाल होने वाला सामग्री प्रकार।",
    },
    "category_explanation_no_match": {
        "en": "Not a typical material type for this commodity category, but not ruled out.",
        "hi": "इस उत्पाद श्रेणी के लिए सामान्य सामग्री प्रकार नहीं है, लेकिन इसे खारिज नहीं किया गया।",
    },
    "category_commodity_property": {
        "en": "Commodity category: {category}",
        "hi": "उत्पाद श्रेणी: {category}",
    },
    "category_packaging_property": {
        "en": "Material category: {category}",
        "hi": "सामग्री श्रेणी: {category}",
    },
    # -- cost_fit --
    "cost_commodity_property": {
        "en": "Requested budget tier: {tier}",
        "hi": "चुना गया बजट स्तर: {tier}",
    },
    "cost_commodity_property_mapped": {
        "en": "Requested budget tier: {label} ({tolerance} cost tolerance)",
        "hi": "चुना गया बजट स्तर: {label} ({tolerance} लागत सहनशीलता)",
    },
    "cost_packaging_property": {
        "en": "Material cost tier: {tier}",
        "hi": "सामग्री की लागत स्तर: {tier}",
    },
    "cost_explanation": {
        "en": "{tier}-cost material.",
        "hi": "{tier} लागत वाली सामग्री।",
    },
    # -- sustainability_fit --
    "sustainability_rationale": {
        "en": "Sustainability priority: {rating}.",
        "hi": "स्थिरता (सस्टेनेबिलिटी) प्राथमिकता: {rating}।",
    },
    "sustainability_property_priority": {
        "en": "Sustainability priority requested",
        "hi": "स्थिरता को प्राथमिकता देने का अनुरोध किया गया",
    },
    "sustainability_property_standard": {
        "en": "Standard weighting",
        "hi": "सामान्य भारांक (वेटिंग)",
    },
    "sustainability_explanation": {
        "en": "Recyclability/compostability rating: {rating}.",
        "hi": "पुनर्चक्रण/खाद-योग्यता रेटिंग: {rating}।",
    },
    # -- format_practicality --
    "practicality_warning": {
        "en": "{material_name} is heavier and more fragile in transport/distribution than flexible or rigid-plastic alternatives — a real practicality cost for high-volume retail packaging, separate from its barrier performance.",
        "hi": "{material_name} लचीली या कठोर-प्लास्टिक विकल्पों की तुलना में परिवहन/वितरण में भारी और अधिक नाज़ुक है — यह बड़ी मात्रा में खुदरा पैकेजिंग के लिए एक वास्तविक व्यावहारिक लागत है, जो इसकी बैरियर क्षमता से अलग है।",
    },
    "practicality_commodity_property": {
        "en": "High-volume retail distribution",
        "hi": "बड़ी मात्रा में खुदरा वितरण",
    },
    "practicality_packaging_property": {
        "en": "{material_name} format practicality: {points}/10",
        "hi": "{material_name} फॉर्मेट की व्यावहारिकता: {points}/10",
    },
    "practicality_explanation_good": {
        "en": "Practical format for high-volume retail (lightweight, low breakage risk).",
        "hi": "बड़ी मात्रा में खुदरा बिक्री के लिए व्यावहारिक फॉर्मेट (हल्का, टूटने का कम खतरा)।",
    },
    "practicality_explanation_poor": {
        "en": "Heavier/more fragile format — a real logistics cost at retail volume.",
        "hi": "भारी/अधिक नाज़ुक फॉर्मेट — खुदरा मात्रा में यह एक वास्तविक लॉजिस्टिक्स लागत है।",
    },
    # -- acidic incompatibility --
    "acidic_warning": {
        "en": "Commodity is acidic (pH up to {ph_max}); bare aluminum foil can corrode and react with acidic foods without a protective coating/laminate.",
        "hi": "यह उत्पाद अम्लीय (एसिडिक) है (pH अधिकतम {ph_max} तक); बिना सुरक्षा परत (कोटिंग/लैमिनेट) के सादा एल्युमिनियम फॉयल अम्लीय खाद्य पदार्थों के साथ प्रतिक्रिया कर सकता है और क्षरित हो सकता है।",
    },
    # -- condition-driven warnings --
    "condition_warning_transport": {
        "en": "Expected transport/storage duration ({days} days) exceeds this commodity's typical ambient shelf life ({min}-{max} days) — consider cold chain, active packaging, or a stronger barrier material.",
        "hi": "अनुमानित परिवहन/भंडारण अवधि ({days} दिन) इस उत्पाद की सामान्य कक्ष-तापमान शेल्फ लाइफ ({min}-{max} दिन) से अधिक है — कोल्ड चेन, सक्रिय पैकेजिंग, या अधिक मज़बूत बैरियर सामग्री पर विचार करें।",
    },
    "condition_warning_temperature": {
        "en": "At {temp}C, this commodity's '{cls}' respiration rate will accelerate further — shelf life will likely run shorter than the typical ambient range.",
        "hi": "{temp}°C पर, इस उत्पाद की '{cls}' श्वसन दर और तेज़ हो जाएगी — शेल्फ लाइफ सामान्य कक्ष-तापमान सीमा से कम रहने की संभावना है।",
    },
    # -- MAP gas guidance --
    "map_gas_note_na": {
        "en": "MAP gas guidance only applies to fresh produce with an active respiration rate.",
        "hi": "MAP गैस मार्गदर्शन केवल सक्रिय श्वसन दर वाले ताज़े उत्पादों पर ही लागू होता है।",
    },
    "map_gas_note": {
        "en": (
            "General MAP guidance based on commonly documented gas-mix ranges for produce "
            "grouped by respiration rate class — not commodity-specific lab-tested values. "
            "The actual optimal mix depends on cultivar, temperature, and pack permeability; "
            "validate with real trials before production use."
        ),
        "hi": (
            "यह सामान्य MAP मार्गदर्शन श्वसन दर श्रेणी के अनुसार सामान्यतः दर्ज गैस-मिश्रण सीमाओं पर "
            "आधारित है — यह किसी विशेष उत्पाद के लिए प्रयोगशाला-परीक्षित मान नहीं हैं। वास्तविक इष्टतम "
            "मिश्रण किस्म, तापमान और पैक की पारगम्यता पर निर्भर करता है; उत्पादन में उपयोग से पहले "
            "वास्तविक परीक्षणों से पुष्टि करें।"
        ),
    },
    # -- estimated cost comparison --
    "cost_comparison_reference": {
        "en": "Reference point for the cost comparisons below.",
        "hi": "नीचे दी गई लागत तुलना के लिए आधार बिंदु।",
    },
    "cost_comparison_more": {
        "en": "Approximately {pct}% more expensive than the top pick (estimated).",
        "hi": "शीर्ष विकल्प से लगभग {pct}% अधिक महंगा (अनुमानित)।",
    },
    "cost_comparison_less": {
        "en": "Approximately {pct}% less expensive than the top pick (estimated).",
        "hi": "शीर्ष विकल्प से लगभग {pct}% कम महंगा (अनुमानित)।",
    },
    "cost_comparison_comparable": {
        "en": "Comparable estimated cost to the top pick.",
        "hi": "शीर्ष विकल्प के लगभग बराबर अनुमानित लागत।",
    },
    # -- trade-off summary --
    "trade_off_top_best_fit": {
        "en": "Best overall fit for this commodity's properties",
        "hi": "इस उत्पाद के गुणों के लिए सबसे उपयुक्त समग्र विकल्प",
    },
    "trade_off_top_cost_tier": {
        "en": "{tier}-cost",
        "hi": "{tier} लागत",
    },
    "trade_off_top_good_recyclability": {
        "en": "good recyclability",
        "hi": "अच्छी पुनर्चक्रण क्षमता",
    },
    "trade_off_cheaper": {
        "en": "cheaper than top pick",
        "hi": "शीर्ष विकल्प से सस्ता",
    },
    "trade_off_higher_cost": {
        "en": "higher cost than top pick",
        "hi": "शीर्ष विकल्प से महंगा",
    },
    "trade_off_shelf_life_more": {
        "en": "+{delta} days estimated shelf life vs. top pick",
        "hi": "शीर्ष विकल्प की तुलना में +{delta} दिन अधिक अनुमानित शेल्फ लाइफ",
    },
    "trade_off_shelf_life_less": {
        "en": "{delta} days estimated shelf life vs. top pick",
        "hi": "शीर्ष विकल्प की तुलना में {delta} दिन अनुमानित शेल्फ लाइफ",
    },
    "trade_off_more_sustainable": {
        "en": "more recyclable/sustainable than top pick",
        "hi": "शीर्ष विकल्प से अधिक पुनर्चक्रण-योग्य/टिकाऊ",
    },
    "trade_off_less_sustainable": {
        "en": "less recyclable/sustainable than top pick",
        "hi": "शीर्ष विकल्प से कम पुनर्चक्रण-योग्य/टिकाऊ",
    },
    "trade_off_comparable": {
        "en": "comparable overall fit to the top pick",
        "hi": "शीर्ष विकल्प जैसा ही समग्र रूप से उपयुक्त",
    },
    # -- static disclaimers --
    "regulatory_note": {
        "en": (
            "This recommendation is based on barrier, permeability, cost, and sustainability "
            "performance only. It does not constitute food-safety or regulatory compliance "
            "verification (e.g. FSSAI food-contact material approval, or any other jurisdiction's "
            "equivalent). Independently confirm regulatory compliance for your specific commodity, "
            "packaging format, and market before production use."
        ),
        "hi": (
            "यह सिफ़ारिश केवल बैरियर, पारगम्यता, लागत और स्थिरता प्रदर्शन पर आधारित है। यह खाद्य-सुरक्षा "
            "या नियामक अनुपालन प्रमाणन नहीं है (जैसे FSSAI खाद्य-संपर्क सामग्री स्वीकृति, या किसी अन्य "
            "क्षेत्राधिकार की समकक्ष प्रक्रिया)। उत्पादन में उपयोग से पहले अपने विशेष उत्पाद, पैकेजिंग प्रारूप "
            "और बाज़ार के लिए नियामक अनुपालन की स्वतंत्र रूप से पुष्टि करें।"
        ),
    },
    # -- Government scheme linkage note (engine/government_scheme.py) --
    # Deliberately never claims THIS recommendation is confirmed eligible —
    # only that this category of scheme exists and may apply, with actual
    # eligibility determined case-by-case by the reader's own State Nodal
    # Agency. See tests/test_government_scheme.py for the literal check
    # that "eligible"/"qualifies" never appear without a "may"/"verify"
    # qualifier nearby.
    "government_scheme_note": {
        "en": (
            "Packaging equipment upgrades may be eligible for support under the Ministry of Food "
            "Processing Industries' PM-FME scheme's credit-linked capital subsidy (35% of eligible "
            "project cost, up to ₹10 lakh for individual micro-enterprises), and its separate "
            "branding/marketing support component. Eligible expenditure categories are determined "
            "case-by-case by your State Nodal Agency — verify eligibility before applying."
        ),
        "hi": (
            "पैकेजिंग उपकरण अपग्रेड खाद्य प्रसंस्करण उद्योग मंत्रालय की PM-FME योजना की क्रेडिट-लिंक्ड पूंजी "
            "सब्सिडी (पात्र परियोजना लागत का 35%, व्यक्तिगत सूक्ष्म उद्यमों के लिए अधिकतम ₹10 लाख तक), और "
            "उसके अलग ब्रांडिंग/मार्केटिंग सहायता घटक के तहत सहायता के लिए पात्र हो सकते हैं। पात्र व्यय "
            "श्रेणियां आपकी राज्य नोडल एजेंसी द्वारा केस-दर-केस आधार पर तय की जाती हैं — आवेदन करने से पहले "
            "पात्रता सत्यापित करें।"
        ),
    },
    "disclaimer_basic": {
        "en": (
            "Generated from heuristic rules and typical literature ranges, not lab testing. "
            "Validate top candidates with real shelf-life trials before production use."
        ),
        "hi": (
            "यह सुझाव सामान्य नियमों (ह्यूरिस्टिक्स) और सामान्य संदर्भ आंकड़ों पर आधारित है, प्रयोगशाला "
            "परीक्षण पर नहीं। उत्पादन में उपयोग से पहले शीर्ष विकल्पों की वास्तविक शेल्फ-लाइफ परीक्षणों "
            "से पुष्टि करें।"
        ),
    },
    "disclaimer_detailed": {
        "en": (
            "Generated from heuristic rules and typical literature ranges, not lab testing. "
            "Validate top candidates — including the MAP gas guidance — with real shelf-life trials "
            "before production use."
        ),
        "hi": (
            "यह सुझाव सामान्य नियमों (ह्यूरिस्टिक्स) और सामान्य संदर्भ आंकड़ों पर आधारित है, प्रयोगशाला "
            "परीक्षण पर नहीं। उत्पादन में उपयोग से पहले शीर्ष विकल्पों की — MAP गैस मार्गदर्शन सहित — "
            "वास्तविक शेल्फ-लाइफ परीक्षणों से पुष्टि करें।"
        ),
    },
    # -- ML agreement --
    "ml_agreement_agrees": {
        "en": "Our rules engine and ML model agree on this recommendation.",
        "hi": "हमारा नियम-आधारित इंजन और ML मॉडल दोनों इस सिफ़ारिश पर सहमत हैं।",
    },
    "ml_agreement_disagrees": {
        "en": (
            "Our ML model would have ranked '{material_name}' more highly than the rules engine's "
            "top pick — worth a second look, not necessarily a red flag."
        ),
        "hi": (
            "हमारे ML मॉडल ने '{material_name}' को नियम-आधारित इंजन के शीर्ष विकल्प से अधिक रेटिंग दी "
            "होती — यह दोबारा जांचने लायक है, ज़रूरी नहीं कि यह कोई गंभीर समस्या हो।"
        ),
    },
    # -- compliance flags (engine/compliance_check.py) — general_reference (e.g. "FSSAI
    # Packaging & Labelling Regulations") deliberately stays English in both languages,
    # since it's a regulatory body/framework proper noun, not a sentence to translate. --
    "compliance_disclaimer": {
        "en": (
            "These are general informational flags based on commonly known packaging regulations, "
            "not a certified legal compliance verification. Always confirm actual regulatory "
            "compliance with a qualified expert or the relevant authority before production use."
        ),
        "hi": (
            "ये सामान्य रूप से ज्ञात पैकेजिंग नियमों पर आधारित सामान्य सूचनात्मक संकेत हैं, प्रमाणित "
            "कानूनी अनुपालन सत्यापन नहीं। उत्पादन में उपयोग से पहले हमेशा किसी योग्य विशेषज्ञ या "
            "संबंधित प्राधिकरण से वास्तविक नियामक अनुपालन की पुष्टि करें।"
        ),
    },
    "compliance_food_contact_layer_verification": {
        "en": (
            "This material is typically used as a barrier or structural layer WITHIN a multi-layer "
            "laminate, rather than being the innermost food-contact layer itself (that role is usually "
            "filled by a separate polyolefin sealant layer). Confirm the actual food-contact (innermost) "
            "layer of your final laminate structure is independently certified food-grade — a barrier "
            "layer's own properties don't automatically make the whole laminate food-contact-safe."
        ),
        "hi": (
            "यह सामग्री आमतौर पर मल्टी-लेयर लैमिनेट के भीतर एक बैरियर या संरचनात्मक परत के रूप में "
            "इस्तेमाल होती है, न कि खुद सबसे भीतरी खाद्य-संपर्क परत के रूप में (यह भूमिका आमतौर पर एक "
            "अलग पॉलीओलिफिन सीलेंट परत निभाती है)। सुनिश्चित करें कि आपकी अंतिम लैमिनेट संरचना की असली "
            "खाद्य-संपर्क (सबसे भीतरी) परत स्वतंत्र रूप से खाद्य-ग्रेड प्रमाणित है — केवल बैरियर परत के "
            "गुण पूरे लैमिनेट को खाद्य-संपर्क के लिए सुरक्षित नहीं बना देते।"
        ),
    },
    "compliance_acidic_food_bare_foil_caution": {
        "en": (
            "This commodity is acidic and the recommended material includes an aluminum foil layer. "
            "Bare/uncoated aluminum foil can corrode and react with acidic foods — confirm the "
            "food-contact side of the laminate has an intact protective coating, not exposed bare foil."
        ),
        "hi": (
            "यह उत्पाद अम्लीय (एसिडिक) है और सुझाई गई सामग्री में एल्युमिनियम फॉयल की परत शामिल है। "
            "बिना कोटिंग वाला सादा एल्युमिनियम फॉयल अम्लीय खाद्य पदार्थों के साथ प्रतिक्रिया कर सकता है "
            "और क्षरित हो सकता है — सुनिश्चित करें कि लैमिनेट का खाद्य-संपर्क वाला हिस्सा एक सुरक्षित "
            "कोटिंग से ढका है, न कि खुला सादा फॉयल।"
        ),
    },
    "compliance_resin_identification_code_labeling": {
        "en": (
            "Plastic packaging is generally expected to carry the resin identification code (the "
            "numbered chasing-arrows symbol, 1-7) to support correct consumer/recycler sorting. "
            "Confirm this marking is included on the final printed pack."
        ),
        "hi": (
            "प्लास्टिक पैकेजिंग पर आमतौर पर रेज़िन पहचान कोड (1-7 अंकों वाला तीर-चिह्न) होना अपेक्षित "
            "है, ताकि उपभोक्ता/रीसाइक्लर सही तरीके से छांट सकें। सुनिश्चित करें कि यह चिह्न अंतिम छपे "
            "हुए पैक पर मौजूद है।"
        ),
    },
    "compliance_opaque_pack_labeling_reminder": {
        "en": (
            "This material's typical commercial format is opaque or fully printed over, so the product "
            "itself won't be visible to the end consumer. Make sure all mandatory pack declarations "
            "(net quantity, MRP, manufacturing/expiry date, FSSAI license number) are clearly printed "
            "on the pack, since visual inspection of the product isn't possible as a fallback."
        ),
        "hi": (
            "इस सामग्री का सामान्य व्यावसायिक रूप अपारदर्शी या पूरी तरह छपा हुआ होता है, इसलिए उत्पाद "
            "खुद अंतिम उपभोक्ता को दिखाई नहीं देता। सुनिश्चित करें कि सभी अनिवार्य घोषणाएं (शुद्ध मात्रा, "
            "MRP, निर्माण/समाप्ति तिथि, FSSAI लाइसेंस नंबर) पैक पर स्पष्ट रूप से छपी हों, क्योंकि उत्पाद "
            "को देखकर जांचना यहां संभव नहीं है।"
        ),
    },
    "compliance_single_use_plastic_general_caution": {
        "en": (
            "Thin flexible plastic film formats like this one are the category most commonly discussed "
            "under evolving single-use-plastic restrictions in India. Specific banned-item lists and "
            "thickness thresholds vary by state and change over time — confirm current applicability "
            "for your exact format/gauge before finalizing, rather than assuming this is unaffected."
        ),
        "hi": (
            "इस जैसी पतली लचीली प्लास्टिक फिल्म भारत में बदलते सिंगल-यूज़-प्लास्टिक प्रतिबंधों के तहत "
            "सबसे अधिक चर्चा में रहने वाली श्रेणी है। प्रतिबंधित वस्तुओं की सूची और मोटाई की सीमाएं "
            "राज्य के अनुसार अलग-अलग होती हैं और समय के साथ बदलती रहती हैं — अंतिम रूप देने से पहले "
            "अपने ठीक फॉर्मेट/मोटाई पर वर्तमान लागू नियम की पुष्टि करें, यह मान लेने के बजाय कि इस पर "
            "कोई असर नहीं है।"
        ),
    },
    "compliance_epr_recyclability_complexity": {
        "en": (
            "Multi-layer/multi-material laminate formats like this one are widely noted as harder to "
            "mechanically recycle than a single-polymer package, which can complicate meeting Extended "
            "Producer Responsibility (EPR) recyclability expectations. This doesn't mean the material "
            "is non-compliant — it means the EPR/recyclability story for this format needs to be worked "
            "out explicitly rather than assumed."
        ),
        "hi": (
            "इस जैसे मल्टी-लेयर/मल्टी-मैटीरियल लैमिनेट फॉर्मेट को सिंगल-पॉलीमर पैकेज की तुलना में "
            "यांत्रिक रूप से पुनर्चक्रित करना अधिक कठिन माना जाता है, जिससे एक्सटेंडेड प्रोड्यूसर "
            "रिस्पॉन्सिबिलिटी (EPR) की पुनर्चक्रण अपेक्षाओं को पूरा करना जटिल हो सकता है। इसका मतलब यह "
            "नहीं कि सामग्री अनुपालन में नहीं है — बल्कि इसका मतलब है कि इस फॉर्मेट के लिए EPR/पुनर्चक्रण "
            "की योजना स्पष्ट रूप से तय की जानी चाहिए, मान ली नहीं जानी चाहिए।"
        ),
    },
    "compliance_compostable_certification_note": {
        "en": (
            "This material is industrially compostable, which requires access to a municipal/industrial "
            "composting facility — it will NOT break down correctly via standard curbside recycling or "
            "uncontrolled home composting, and shouldn't be described to consumers as generically "
            "'recyclable'. Confirm compostability certification against the relevant BIS "
            "compostable-plastics standard for your specific supplier's material before making any "
            "compostability/EPR claim on the pack."
        ),
        "hi": (
            "यह सामग्री औद्योगिक रूप से खाद-योग्य (कंपोस्टेबल) है, जिसके लिए नगरपालिका/औद्योगिक "
            "कंपोस्टिंग सुविधा की ज़रूरत होती है — यह सामान्य कर्बसाइड रीसाइक्लिंग या अनियंत्रित घरेलू "
            "कंपोस्टिंग से सही तरीके से नहीं टूटेगी, और उपभोक्ताओं को इसे सामान्य रूप से "
            "'पुनर्चक्रण-योग्य' नहीं बताना चाहिए। पैक पर कोई भी कंपोस्टेबिलिटी/EPR दावा करने से पहले "
            "अपने सप्लायर की विशेष सामग्री के लिए संबंधित BIS कंपोस्टेबल-प्लास्टिक मानक के अनुसार "
            "प्रमाणन की पुष्टि करें।"
        ),
    },
    "compliance_microwave_safety_verification_note": {
        "en": (
            "This material is sometimes used for microwave-safe containers, but microwave suitability "
            "depends on the exact formulation, additives, and wall thickness of a specific product — it "
            "isn't a property of the base resin alone. Independently test and, if applicable, label "
            "microwave suitability rather than assuming it from the material choice."
        ),
        "hi": (
            "यह सामग्री कभी-कभी माइक्रोवेव-सुरक्षित कंटेनरों के लिए इस्तेमाल होती है, लेकिन माइक्रोवेव "
            "उपयुक्तता किसी विशेष उत्पाद के ठीक फॉर्मूलेशन, एडिटिव्स और दीवार की मोटाई पर निर्भर करती है "
            "— यह केवल आधार रेज़िन का गुण नहीं है। सामग्री के चुनाव से मान लेने के बजाय माइक्रोवेव "
            "उपयुक्तता का स्वतंत्र परीक्षण करें और ज़रूरत हो तो उसे स्पष्ट रूप से लेबल करें।"
        ),
    },
    "compliance_imported_material_fssai_verification": {
        "en": (
            "This material is commonly import-dependent in the Indian market. Imported food-contact "
            "packaging materials still need to independently meet FSSAI food-contact material safety "
            "requirements — a certification or approval from the country of origin isn't automatically "
            "equivalent or sufficient on its own."
        ),
        "hi": (
            "यह सामग्री भारतीय बाज़ार में सामान्यतः आयात पर निर्भर है। आयातित खाद्य-संपर्क पैकेजिंग "
            "सामग्रियों को भी स्वतंत्र रूप से FSSAI की खाद्य-संपर्क सुरक्षा आवश्यकताओं को पूरा करना "
            "ज़रूरी है — मूल देश से मिला प्रमाणन या अनुमोदन अपने आप में समकक्ष या पर्याप्त नहीं माना जा "
            "सकता।"
        ),
    },
    "compliance_fresh_produce_labeling_exemption_note": {
        "en": (
            "Fresh, unprocessed produce sold in breathable/vented packaging can fall under different "
            "(often lighter) labeling expectations than sealed/processed food under general FSSAI "
            "packaging rules. Verify whether this specific product qualifies for any fresh-produce "
            "labeling treatment rather than assuming standard processed-food labeling requirements "
            "apply unchanged."
        ),
        "hi": (
            "सांस लेने योग्य/वेंटेड पैकेजिंग में बिका ताज़ा, अप्रसंस्कृत उत्पाद सामान्य FSSAI पैकेजिंग "
            "नियमों के तहत सीलबंद/प्रसंस्कृत खाद्य पदार्थों से अलग (अक्सर हल्की) लेबलिंग अपेक्षाओं के "
            "दायरे में आ सकता है। यह मान लेने के बजाय कि मानक प्रसंस्कृत-खाद्य लेबलिंग आवश्यकताएं बिना "
            "बदलाव के लागू होती हैं, जांचें कि क्या यह विशेष उत्पाद किसी ताज़ा-उत्पाद लेबलिंग व्यवहार के "
            "योग्य है।"
        ),
    },
    # -- Q10 temperature-adjusted shelf-life prediction (engine/shelf_life.py) --
    "shelf_life_explanation_warmer": {
        "en": (
            "At {temp}C (warmer than the {reference}C this commodity's typical shelf life assumes), "
            "spoilage is predicted to accelerate — roughly {days} days instead of the usual {typical} days."
        ),
        "hi": (
            "{temp}°C पर ({reference}°C से अधिक गर्म, जिसे इस उत्पाद की सामान्य शेल्फ लाइफ आधार मानती है), "
            "खराब होने की गति तेज़ होने का अनुमान है — सामान्य {typical} दिनों के बजाय लगभग {days} दिन।"
        ),
    },
    "shelf_life_explanation_cooler": {
        "en": (
            "At {temp}C (cooler than the {reference}C this commodity's typical shelf life assumes), "
            "spoilage is predicted to slow down — roughly {days} days instead of the usual {typical} days."
        ),
        "hi": (
            "{temp}°C पर ({reference}°C से ठंडा, जिसे इस उत्पाद की सामान्य शेल्फ लाइफ आधार मानती है), "
            "खराब होने की गति धीमी होने का अनुमान है — सामान्य {typical} दिनों के बजाय लगभग {days} दिन।"
        ),
    },
    "shelf_life_explanation_equal": {
        "en": (
            "At {temp}C, matching the {reference}C this commodity's typical shelf life already assumes, "
            "the predicted shelf life is the same as the typical figure: {days} days."
        ),
        "hi": (
            "{temp}°C पर, जो इस उत्पाद की सामान्य शेल्फ लाइफ द्वारा पहले से मानी गई {reference}°C से मेल "
            "खाता है, अनुमानित शेल्फ लाइफ सामान्य आंकड़े जितनी ही है: {days} दिन।"
        ),
    },
    "shelf_life_clamped_suffix": {
        "en": (
            " This estimate was capped to stay within a plausible range — the raw temperature-kinetics "
            "calculation suggested a more extreme figure."
        ),
        "hi": (
            " इस अनुमान को एक व्यावहारिक सीमा के भीतर रखने के लिए सीमित किया गया है — कच्ची "
            "तापमान-कैनेटिक्स गणना ने इससे अधिक चरम आंकड़ा सुझाया था।"
        ),
    },
    "shelf_life_disclaimer": {
        "en": (
            "This is a temperature-kinetics estimate using category-typical Q10 values (a well-established "
            "food-science method for modeling how temperature affects spoilage rate), not a certified or "
            "lab-validated shelf-life claim for this specific commodity. Treat it as directional, not exact."
        ),
        "hi": (
            "यह श्रेणी-स्तरीय सामान्य Q10 मानों का उपयोग करते हुए एक तापमान-कैनेटिक्स अनुमान है (तापमान "
            "खराब होने की दर को कैसे प्रभावित करता है, इसे मॉडल करने की एक सुस्थापित खाद्य-विज्ञान विधि) — "
            "यह इस विशेष उत्पाद के लिए प्रमाणित या प्रयोगशाला-सत्यापित शेल्फ-लाइफ दावा नहीं है। इसे "
            "दिशासूचक मानें, सटीक नहीं।"
        ),
    },
    # -- Cold-chain temperature-excursion re-recommendation (engine/cold_chain.py) --
    "cold_chain_action_urgent": {
        "en": "Urgent: sell or use within about {hours} hours.",
        "hi": "तुरंत ध्यान दें: लगभग {hours} घंटों के भीतर बेचें या उपयोग करें।",
    },
    "cold_chain_action_expired": {
        "en": "Remaining shelf life has already elapsed at the logged excursion temperature — do not sell; discard or use immediately at your own discretion.",
        "hi": "दर्ज की गई घटना के तापमान पर बची हुई शेल्फ लाइफ पहले ही समाप्त हो चुकी है — न बेचें; अपने विवेक से तुरंत उपयोग करें या हटा दें।",
    },
    "cold_chain_action_ok": {
        "en": "No action needed — remaining shelf life is still within a normal range.",
        "hi": "कोई कार्रवाई ज़रूरी नहीं — बची हुई शेल्फ लाइफ अभी भी सामान्य दायरे में है।",
    },
    "cold_chain_explanation": {
        "en": (
            "This excursion reached {temp}C for {duration} hours. At {temp}C, the same temperature-kinetics "
            "model used elsewhere in this app predicts about {predicted} days of shelf life from here — "
            "subtracting the {duration} hours already elapsed at that temperature leaves an estimated "
            "{remaining} days remaining."
        ),
        "hi": (
            "यह घटना {temp}°C पर {duration} घंटों तक रही। {temp}°C पर, इस ऐप में कहीं और उपयोग किया जाने वाला "
            "वही तापमान-कैनेटिक्स मॉडल यहां से लगभग {predicted} दिनों की शेल्फ लाइफ का अनुमान लगाता है — उस "
            "तापमान पर पहले से बीत चुके {duration} घंटों को घटाने पर अनुमानित रूप से {remaining} दिन शेष रहते हैं।"
        ),
    },
    "cold_chain_disclaimer": {
        "en": (
            "This re-estimates remaining shelf life by treating the logged excursion temperature as the new "
            "storage condition for the remaining window — the same Q10 method used elsewhere in this app, "
            "not a lab-validated cold-chain audit. Manually logged, not sensor-verified."
        ),
        "hi": (
            "यह बची हुई शेल्फ लाइफ का पुनः अनुमान लगाता है, दर्ज की गई घटना के तापमान को बची हुई अवधि के लिए "
            "नई भंडारण स्थिति मानकर — यह इस ऐप में कहीं और उपयोग की जाने वाली उसी Q10 विधि का उपयोग करता है, "
            "कोई प्रयोगशाला-सत्यापित कोल्ड-चेन ऑडिट नहीं। मैन्युअल रूप से दर्ज, सेंसर-सत्यापित नहीं।"
        ),
    },
}


def t(key: str, lang: str | None, **kwargs) -> str:
    """Looks up TEMPLATES[key][lang] and formats it with kwargs. Falls back
    to English if lang is unsupported, and to the key itself (never a
    crash) if the key doesn't exist — defensive the same way the rest of
    this engine treats missing/unexpected data."""
    lang = _lang_or_default(lang)
    entry = TEMPLATES.get(key)
    if entry is None:
        return key
    template = entry.get(lang, entry["en"])
    return template.format(**kwargs)
