import pytest
from library_service import add_book_to_catalog, get_catalog_view

#after feedback from A1, this file has been added

def test_catalog_displays_added_book_with_borrow_action():
    """R2 positive: catalog shows required fields and 'Borrow' for available book."""
    #follow arrange, act, asssert structure
    success, msg = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 3)
    assert success is True
    assert "added" in msg.lower()

    rows = get_catalog_view()

    assert isinstance(rows, list) and len(rows) >= 1
    row = next(r for r in rows if r["title"] == "Test Book")

    for key in ("book_id", "title", "author", "isbn", "available_copies", "total_copies", "actions"):
        assert key in row

    assert row["author"] == "Test Author"
    assert row["isbn"] == "1234567890123"
    assert row["total_copies"] == 3
    assert row["available_copies"] == 3

    #borrow should be available when copies > 0
    assert isinstance(row["actions"], str)
    assert "borrow" in row["actions"].lower()
