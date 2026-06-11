"""Query normalization for common spelling and OCR variants."""

from __future__ import annotations

import re


REPLACEMENTS = {
    "coloumb": "coulomb",
    "coloumbs": "coulomb",
    "coulombs": "coulomb",
    "couloumb": "coulomb",
    "couloumbs": "coulomb",
}


def normalize_query(query: str) -> str:
    """Normalize common user typos while preserving the original question elsewhere."""
    normalized = query
    for wrong, right in REPLACEMENTS.items():
        normalized = re.sub(rf"\b{re.escape(wrong)}\b", right, normalized, flags=re.IGNORECASE)

    if re.search(r"\bcoulomb\b", normalized, flags=re.IGNORECASE) and re.search(
        r"\blaw\b", normalized, flags=re.IGNORECASE
    ):
        if "coulomb's law" not in normalized.lower() and "coulomb's" not in normalized.lower():
            normalized = f"{normalized} Coulomb's law"

    return re.sub(r"\s+", " ", normalized).strip()
