# ML ranker — training, validation, and honest limits

This directory trains a supervised model that **complements** the rules
engine (`backend/engine/recommender.py`) with a second, corroborating score.
It does not replace it. If you only read one section, read
["What this does and doesn't prove"](#what-this-does-and-doesnt-prove) below.

## Files

| File | Purpose |
|---|---|
| `features.py` | The **single** feature-encoding function, shared by training and live inference. No train/serve skew is possible because there is exactly one function that turns `(commodity, material, conditions)` into a feature vector. |
| `generate_training_data.py` | Builds the synthetic dataset. Run first. |
| `train_model.py` | GroupKFold CV, trains the final model, evaluates against the reference set, saves everything to `/backend/models/`. Run second. |
| `data/training_data.csv` | Generated dataset (not hand-written; regenerate with the script above). |

Outputs land in `/backend/models/`:
- `material_ranker.joblib` — the trained model, loaded at request time by `engine/ml_ranker.py`.
- `model_metrics.json` — everything below, in machine-readable form.

To regenerate everything from scratch:

```bash
cd backend
python -m training.generate_training_data
python -m training.train_model
```

## Dataset: size and provenance

**20,800 rows, synthetic, anchored to our 80 real commodities.**

*(Retrained after the dataset grew from 30 → 80 commodities across 11
categories — see the [retraining history](#retraining-history) section
below for what changed and why the numbers moved.)*

We do not have 20,800 real commodities. What we have is 80 — the same 80 in
`backend/data/commodities.json`, the same ones the rules engine and the
hand-curated reference set (`backend/evaluation/`) already use. Each of the
80 is an "anchor." For each anchor we generate 20 synthetic *variations* —
the anchor's moisture/fat/pH/shelf-life perturbed within a plausible band
around its own stated range (see `generate_training_data.py` for the exact
perturbation logic), paired with a randomly drawn budget tier and
sustainability-priority flag. Each of those 1,600 (80 × 20) synthetic
commodity-instances is scored against all 13 real packaging materials,
giving 20,800 rows.

**The label for every row comes from the rules engine's own
`_score_material()`** — the exact function that powers real recommendations
today. We think this is a legitimate way to generate training labels, for a
specific reason, not just a convenient one: the rules engine is a
*deterministic formula* encoding real food-packaging-science heuristics
(moisture ⇄ WVTR target, respiration class ⇄ OTR band, fat content ⇄
oxidative-rancidity sensitivity, and so on — see the extensive comments in
`engine/recommender.py`). Calling that formula across a much wider,
*continuous* input space than the 80 fixed points it was tuned against is a
way of teaching a model the **pattern** the formula encodes, not 80
memorized answers. This is the same idea behind generating training data
from any deterministic simulator or expert system: you're distilling a known
function, not inventing new ground truth.

**What this is not**: independent, lab-verified ground truth. The model's
ceiling is bounded by how well it approximates the rules engine — it cannot
discover packaging science the rules engine doesn't already encode. If the
rules engine has a systematic gap (and it does — see
`evaluation/run_evaluation.py`'s documented mismatches for
fish/shrimp/bread/cake), a model trained on its labels will reproduce that
same gap, not fix it. We confirmed this directly: 4 of the ML model's 8
reference-set mismatches are the *exact same 4 commodities* the rules engine
itself gets wrong. That's expected, and it's evidence the model learned the
real pattern rather than noise — but it's also a reminder that this whole
approach can only be as good as the rules engine it's distilling. The other
4 mismatches are a different, new phenomenon specific to the larger dataset
— see [retraining history](#retraining-history).

## Validation methodology

### 1. GroupKFold cross-validation (the rigorous test)

**Grouped by `base_commodity_id`** — the real anchor a synthetic row
descends from, never the synthetic row's own id. A plain random K-Fold
would let different synthetic variations of the same commodity (e.g. two
different perturbed "tomato" rows) land on both sides of a train/test split.
Since both variations share the same category and a similar
moisture/fat/pH neighborhood, and both labels come from the same formula,
a model could score deceptively well on the test fold just by having
implicitly "seen tomato before" — that's target leakage, not genuine
generalization.

GroupKFold makes that structurally impossible: all 260 rows descended from a
given real commodity go entirely into one fold. A test fold's commodities
are ones the model has never seen in any form during that fold's training.
5 folds, 16 held-out commodities per fold.

**Results** (see `model_metrics.json` → `group_kfold_cv` for the exact
numbers from the last training run):

| Fold | Test commodities | R² | MAE |
|---|---|---|---|
| 0 | 16 | 0.950 | 1.662 |
| 1 | 16 | 0.966 | 1.074 |
| 2 | 16 | 0.973 | 0.987 |
| 3 | 16 | 0.978 | 0.934 |
| 4 | 16 | 0.972 | 1.015 |
| **Average** | | **0.968** | **1.134** |

MAE is in points on the rules engine's own 0-100 score scale — so the model
is typically within about 1.1 points of what the rules engine would have
scored, on commodities it never trained on in any form. Both R² and MAE
improved substantially over the 30-commodity run (was avg R²=0.906,
MAE=2.13) — more distinct anchors gives the model more of the underlying
moisture/fat/pH/OTR/WVTR relationship to actually learn from, rather than a
sparser set of points it can more easily overfit around. Fold-to-fold
variance also shrank (0.950-0.978 now vs. 0.80-0.95 before) — no fold is the
conspicuously hard one anymore.

### 2. Independent check: the hand-curated reference set

The GroupKFold numbers measure how well the model reproduces the rules
engine's *formula*. They don't tell you whether the rules engine's formula
is itself good food-packaging judgment. For that, we have a second,
independent signal: the same reference set (`evaluation/reference_cases.py`,
50 cases as of this writing — grown from 35 alongside the dataset
expansion) used to validate the rules engine — real commodities, expected
materials grounded in general food-packaging consensus, authored separately
from the rules engine's code.

We ran the **final** trained model (trained on all 20,800 rows) against all
50 cases, using each case's real, exact commodity data:

- **Top-1 agreement: 84.0%**
- **Top-3 agreement: 98.0%**

This is a real drop from the 30-commodity model's 88.6%/97.1% on the
(smaller, 35-case) reference set — see
[retraining history](#retraining-history) for what's actually behind that
drop; it isn't the rules engine getting worse (it's now at 92.0%/98.0% on
the same 50-case set, improved by an unrelated rule fix — see
`evaluation/run_evaluation.py`), it's the ML model's own approximation error
showing up more on razor-thin scoring margins now that more commodities
share tighter regions of the feature space. **Be explicit about the limit
here regardless**: this is agreement with our own hand-curated judgment, run
through the same rules engine the labels came from. It is our best available
proxy for real-world validity given what we have access to — it is not
independent lab validation, and we're not claiming it is.

One methodological note: this reference-set check runs the final model
(trained on synthetic variations of all 80 anchors) on those anchors'
**exact, real, unperturbed** property values — not synthetic data, but also
not a commodity the model has never encountered in any form, unlike the
GroupKFold test folds. Don't read the 84.0%/98.0% numbers as a replacement
for the GroupKFold generalization numbers; they answer a different question
("does the model's output still look sensible on real inputs?") and both are
reported for that reason.

## Feature importances

From the final model's `feature_importances_` (see `model_metrics.json` →
`feature_importances` for the full ranked list):

| Feature | Importance |
|---|---|
| `material_wvtr` | 0.254 |
| `commodity_respiration_ord` | 0.227 |
| `material_otr` | 0.112 |
| `material_category_flexible_film_or_rigid` | 0.108 |
| `commodity_fat_pct` | 0.050 |
| `commodity_moisture_pct` | 0.046 |
| `material_thickness` | 0.036 |
| `commodity_ph` | 0.025 |
| `commodity_category_meat_fish` | 0.017 |
| `budget_tier_ord` | 0.013 |

Same core dimensions dominate as before the retrain (barrier properties,
respiration, material category), which is reassuring — the larger dataset
didn't change *what* the model considers important, just sharpened it.
`material_wvtr` and `commodity_respiration_ord` swapped order at the top
(both still clearly dominant, ~0.25 and ~0.23) — not a meaningful shift,
just noise between two features that were already close.
`commodity_category_meat_fish` newly cracks the top 10, plausibly reflecting
the `moisture_sensitive_categories` rule fix (see below): meat_fish now
behaves distinctly from other categories in the moisture-fit calculation, so
the model has a real reason to use that one-hot column. One honest caveat,
unchanged from before: `material_thickness` isn't referenced anywhere in the
rules engine's actual scoring formula, yet it shows nonzero importance —
almost certainly incidental correlation with cost tier or material category
rather than a genuine causal signal. Feature importance from a tree ensemble
reflects what the model found useful for prediction, which isn't
automatically the same as what's causally meaningful.

## Retraining history

**2026-09: retrained for the 30 → 80 commodity dataset expansion.**

Two prerequisite fixes were needed before retraining, both purely additive:

1. `training/features.py`'s `COMMODITY_CATEGORIES` one-hot list was
   hardcoded to the original 7 categories. The 4 new categories
   (`nuts_dried_fruits`, `beverages`, `frozen_foods`, `ready_to_eat_snacks`)
   would have silently encoded as an all-zero category vector for 20 of the
   80 commodities, losing that signal entirely. Added the 4 new categories
   as new one-hot columns (27 → 31 features total) before regenerating data.
2. The rules engine itself got a fix first (`moisture_sensitive_categories`
   in `rules.json`, for the `dried_fish` moisture-fit gap — see the git
   history / commit for that change), so the retrained model's labels
   reflect the corrected rules engine, not the old one.

**GroupKFold generalization improved substantially**: avg R² 0.906 → 0.968,
avg MAE 2.13 → 1.13. More distinct real anchors gives the model a richer
signal to learn the actual moisture/fat/OTR/WVTR relationships from, rather
than a sparser set of points it can fit more loosely around.

**Reference-set top-1 agreement dropped**: 88.6% (35 cases, old model) →
84.0% (50 cases, new model). Investigated this rather than just reporting
it. The 50-case mismatch list has 8 entries; 4 are the same rules-engine
disagreements as before (fish, shrimp, bread, cake — the ML model inherits
whatever the rules engine itself gets "wrong" against the reference set, as
expected). The other 4 are new: `chicken_default`, `fish_fillet_default`,
`prawns_default`, `minced_meat_default` — cases where the **rules engine
itself is correct** (picks `metalized_film`, matching the reference set),
but the retrained ML model's own top prediction is `aluminum_foil_laminate`
instead.

Root cause: on these commodities, the rules engine's own scores for
`metalized_film` (92.7) and `aluminum_foil_laminate` (90.5) are only 2.2
points apart — well inside the model's own GroupKFold MAE of ~1.1. The
model predicts `metalized_film` at 89.1 (a 3.6-point miss) and
`aluminum_foil_laminate` at 90.1 (a 0.4-point miss), which is enough
approximation noise to flip a narrow true margin. This is not a new bug in
the integration — `/recommend/detailed`'s ranking is still driven entirely
by the rules engine's own score (confirmed unaffected: `chicken_fresh`
still ranks `metalized_film` top-1 with `score=92.7`, unchanged). It's the
ML model's approximation error becoming visible on a close call, and it's
exactly what `ml_agreement` exists to surface honestly rather than hide:
these 4 cases now correctly show `"agrees": false` with a note that reads
"worth a second look, not necessarily a red flag" — not a silent
contradiction of the rules engine's ranking. A larger, more crowded
commodity set has more of these close three-way-tie scoring regions than a
sparser 30-commodity one did, so seeing a few more of them here is a
reasonable, expected trade-off for the much stronger generalization numbers
above — not a regression to chase down and eliminate.

**Pearson correlation sanity check**, now run over all 80 commodities × 13
materials (1,040 pairs, was 12 commodities × 13 = 156): r = 0.979, MAE =
0.797 (was r = 0.997, MAE = 0.516 on the narrower 12-commodity sample).
Still a strong pass — the drop is consistent with the same close-margin
phenomenon above showing up across a wider, more varied sample, not a sign
the model stopped tracking the rules engine.

## What this does and doesn't prove

**Does**: show that a supervised model can learn a close approximation of
the rules engine's scoring pattern, validated with a methodology (GroupKFold
by commodity identity) that specifically guards against the most common way
this kind of exercise goes wrong — training on and testing against
variations of the same underlying commodity and calling that "generalization."

**Does not**: prove the underlying food-packaging judgments are correct in
an absolute, lab-verified sense. Both the rules engine and this model
ultimately encode the same team's understanding of packaging science,
documented and reasoned through in `engine/recommender.py`'s comments and
cross-checked against a small hand-curated reference set — not against
real shelf-life trials. Treat `ml_confidence_score` and `ml_agreement`
in the API response exactly as they're framed there: a corroborating
signal that the rules engine's pick is *internally consistent* with the
broader pattern it encodes, not an independent scientific endorsement.
