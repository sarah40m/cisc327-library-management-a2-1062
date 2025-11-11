import pytest
from datetime import datetime, timedelta

import database
from services.library_service import (
    add_book_to_catalog,
    return_book_by_patron,
)

# four unit tests for the return_book_by_patron function

def test_return_invalid_patron_id():
    """Return should reject a patron ID that isn't exactly 6 digits."""
    # Arrange: create a real book so book_id is valid
    ok, _ = add_book_to_catalog("Any Book", "Anon", "1010101010101", 1)
    assert ok is True
    book = database.get_book_by_isbn("1010101010101")
    assert book is not None

    # Act
    success, message = return_book_by_patron("12a45", book["id"])

    # Assert
    assert success is False
    assert "invalid" in message.lower() and "patron" in message.lower()


def test_return_book_not_found():
    """Return should fail when the provided book_id does not exist."""
    # Act
    success, message = return_book_by_patron("123456", -1)

    # Assert
    assert success is False
    assert "book not found" in message.lower()


def test_return_no_active_loan():
    """Return should fail when the patron has no active loan for this book."""
    # Arrange: create a real book but DO NOT borrow it
    ok, _ = add_book_to_catalog("Unborrowed", "Anon", "2020202020202", 1)
    assert ok is True
    book = database.get_book_by_isbn("2020202020202")
    assert book is not None

    # Act
    success, message = return_book_by_patron("123456", book["id"])

    # Assert
    assert success is False
    msg = message.lower()
    assert ("no active" in msg and "borrow" in msg) or ("not currently borrowed" in msg)


def test_return_success():
    """Returning a borrowed book should succeed and mention 'returned' or 'success'."""
    # Arrange: create a book and seed an ACTIVE borrow
    ok, _ = add_book_to_catalog("Borrowed", "Anon", "3030303030303", 1)
    assert ok is True
    book = database.get_book_by_isbn("3030303030303")
    assert book is not None

    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    assert database.insert_borrow_record("123456", book["id"], borrow_date, due_date) is True
    assert database.update_book_availability(book["id"], -1) is True

    # Sanity: available is now 0
    before = database.get_book_by_id(book["id"])
    assert before["available_copies"] == 0

    # Act
    success, message = return_book_by_patron("123456", book["id"])

    # Assert
    assert success is True
    assert ("return" in message.lower()) or ("success" in message.lower())

    # And availability incremented back
    after = database.get_book_by_id(book["id"])
    assert after["available_copies"] == 1
