import pytest
from services.library_service import (
    get_patron_status_report
)

# four unit tests for the get_patron_status_report function

def test_patron_status_has_required_keys():
    """Report must include current loans, total fees, count, and history."""
    report = get_patron_status_report("123456")
    assert isinstance(report, dict)
    for key in ("current_loans", "total_late_fees", "borrowed_count", "history"):
        assert key in report

def test_patron_status_value_types():
    """Types: lists for loans/history, int count, numeric fees."""
    report = get_patron_status_report("123456")
    assert isinstance(report["current_loans"], list)
    assert isinstance(report["history"], list)
    assert isinstance(report["borrowed_count"], int)
    assert isinstance(report["total_late_fees"], (int, float))

def test_borrowed_count_matches_current_loans_len():
    """Borrowed count should equal the number of current loan entries."""
    report = get_patron_status_report("123456")
    assert report["borrowed_count"] == len(report["current_loans"])

def test_current_loans_entries_have_required_fields():
    """Each current loan should include book_id, title, and due_date."""
    report = get_patron_status_report("123456")
    for loan in report["current_loans"]:
        assert "book_id" in loan
        assert "title" in loan
        assert "due_date" in loan  #ex. YYYY-MM-DD