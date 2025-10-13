import pytest
from library_service import (
    add_book_to_catalog,
    search_books_in_catalog,
)

# four unit tests for the search_books_in_catalog function

def test_search_by_title_partial_match():
    """Search by title should return results for partial matches, being case-insensitive."""
    # seed
    add_book_to_catalog("Harry Potter and the Philosopher's Stone", "J.K. Rowling", "7777777777777", 2)
    add_book_to_catalog("Clean Code", "Robert C. Martin", "8888888888888", 1)

    results = search_books_in_catalog("harry", "title")
    assert isinstance(results, list)
    assert any("harry" in book["title"].lower() for book in results)


def test_search_by_author_partial_match():
    """Search by author should return results for partial matches, being case-insensitive."""
    # seed
    add_book_to_catalog("Chamber of Secrets", "J.K. Rowling", "9999999999999", 1)
    add_book_to_catalog("Effective Python", "Brett Slatkin", "1234567890123", 1)

    results = search_books_in_catalog("rowling", "author")
    assert isinstance(results, list)
    assert any("rowling" in book["author"].lower() for book in results)


def test_search_by_isbn_exact_match():
    """Search by ISBN should return results only on exact match."""
    # seed
    add_book_to_catalog("Exact Match Book", "Author A", "1010101010101", 1)
    add_book_to_catalog("Different Book", "Author B", "2020202020202", 1)

    results = search_books_in_catalog("1010101010101", "isbn")
    assert isinstance(results, list)
    assert all(book["isbn"] == "1010101010101" for book in results)


def test_search_no_results():
    """Searching with a term not in catalog should return empty list."""
    # seed something unrelated
    add_book_to_catalog("Clean Architecture", "Robert C. Martin", "3030303030303", 1)

    results = search_books_in_catalog("nonexistentbook", "title")
    assert isinstance(results, list)
    assert len(results) == 0
