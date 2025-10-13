import pytest
from library_service import (
    add_book_to_catalog
)

def test_add_book_valid_input():
    """Test adding a book with valid input."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    
    assert success == True
    assert "successfully added" in message.lower()

def test_add_book_invalid_isbn_too_short():
    """Test adding a book with ISBN too short."""
    success, message = add_book_to_catalog("Test Book", "Test Author", "123456789", 5)
    
    assert success == False
    assert "13 digits" in message

# four additional unit tests for the add_book_to_catalog function

def test_add_book_missing_title():
    """Test adding a book with no title."""
    success, message = add_book_to_catalog("", "Any Author", "1234567890123", 3)

    assert success is False
    assert "title is required" in message.lower()


def test_add_book_author_missing():
    """Test adding a book with no author."""
    success, message = add_book_to_catalog("Some Title", "", "1234567890123", 2)

    assert success is False
    assert "author is required" in message.lower()


def test_add_book_title_too_long():
    """Test adding a book with a title longer than 200 characters."""
    long_title = "S" * 201
    success, message = add_book_to_catalog(long_title, "Author", "1234567890123", 4)

    assert success is False
    assert "less than 200" in message.lower()


def test_add_book_invalid_total_copies():
    """Test adding a book with zero copies."""
    success, message = add_book_to_catalog("Book Title", "Author", "1234567890123", 0)

    assert success is False
    assert "positive integer" in message.lower()

