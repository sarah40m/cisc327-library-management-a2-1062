import pytest
from services.library_service import (
    borrow_book_by_patron
)

# five unit tests for the borrow_book_by_patron function

def test_borrow_invalid_patron_id_too_short():
    """Reject patron IDs that aren't exactly 6 digits (too short)."""
    success, message = borrow_book_by_patron("1234", 1)
    assert success is False
    assert "invalid patron id" in message.lower()

def test_borrow_invalid_patron_id_non_numeric():
    """Reject patron IDs that contain non-digits."""
    success, message = borrow_book_by_patron("12ab56", 1)
    assert success is False
    assert "invalid patron id" in message.lower()

def test_borrow_invalid_patron_id_empty():
    """Reject empty patron ID."""
    success, message = borrow_book_by_patron("", 1)
    assert success is False
    assert "invalid patron id" in message.lower()

def test_borrow_book_not_found_negative_id():
    """Invalid book_id should return 'Book not found.'"""
    success, message = borrow_book_by_patron("123456", -1)
    assert success is False
    assert "book not found" in message.lower()

def test_borrow_book_id_wrong_type():
    """Noninteger book_id should be treated as not found."""
    success, message = borrow_book_by_patron("123456", "notaint")  
    assert success is False
    assert "book not found" in message.lower()