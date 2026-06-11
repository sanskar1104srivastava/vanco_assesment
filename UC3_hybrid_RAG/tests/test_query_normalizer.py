from backend.query_normalizer import normalize_query


def test_normalize_coulomb_law_typo():
    normalized = normalize_query("what is coloumbs law?")

    assert "coulomb" in normalized.lower()
    assert "coloumb" not in normalized.lower()
    assert "coulomb's law" in normalized.lower()
