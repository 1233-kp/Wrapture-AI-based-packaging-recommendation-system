"""Standalone packaging-material lookup by id.

Deliberately separate from engine/recommender.py (which is off-limits for this
feature) — duplicates its small `_materials()` JSON-loading pattern rather than
importing a private symbol from it, so the recommendation engine itself is
never touched.
"""

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache
def _materials() -> list[dict]:
    with open(DATA_DIR / "packaging_materials.json", encoding="utf-8") as f:
        return json.load(f)["materials"]


def find_material(material_id: str) -> dict | None:
    for material in _materials():
        if material["id"] == material_id:
            return material
    return None


def list_materials() -> list[dict]:
    return _materials()
