from backend.ingest import _update_headings


def test_chapter_pending_does_not_accept_body_text():
    chapter, section = _update_headings(
        "CHAPTER 1\n"
        "This is a normal sentence that should not become a chapter heading.\n"
        "It has body text over multiple lines.\n",
        "Previous Chapter",
        "Previous Section",
    )

    assert chapter == "Previous Chapter"
    assert section == "Previous Section"


def test_chapter_and_section_accept_heading_shaped_lines():
    chapter, section = _update_headings(
        "CHAPTER 1\n"
        "ELECTRIC CHARGES AND FIELDS\n"
        "1.2 ELECTRIC CHARGE\n",
        "Unknown Chapter",
        "Unknown Section",
    )

    assert chapter == "Electric Charges And Fields"
    assert section == "1.2 Electric Charge"
