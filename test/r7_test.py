import pytest
from datetime import datetime, timedelta

import database
from library_service import add_book_to_catalog, get_catalog_view, get_patron_status_report

#after feedback from A1, this file has been added
#this section could also be referred to as f7_test

def test_patron_status_report_current_loans_fees_count_and_history():
    """R7 positive: report includes current loans (with due dates), total fees, count, and history."""
    patron = "123456"

    #arrange: add two books
    ok, _ = add_book_to_catalog("Clean Code", "Robert C. Martin", "9780132350884", 2)
    assert ok is True
    ok, _ = add_book_to_catalog("Effective Python", "Brett Slatkin", "9780134034287", 1)
    assert ok is True

    #look up book ids
    b1 = database.get_book_by_isbn("9780132350884")  # will be current overdue
    b2 = database.get_book_by_isbn("9780134034287")  # will be borrowed+returned (history)
    assert b1 and b2

    #seed ONE overdue current loan:
    borrow_date_overdue = datetime.now() - timedelta(days=20)   # borrowed 20 days ago
    due_date_overdue = borrow_date_overdue + timedelta(days=14) # due 6 days ago -> 6 * $0.50 = $3.00
    assert database.insert_borrow_record(patron, b1["id"], borrow_date_overdue, due_date_overdue)
    assert database.update_book_availability(b1["id"], -1)

    #seed ONE historical loan, borrowed and returned on time
    borrow_date_hist = datetime.now() - timedelta(days=10)
    due_date_hist = borrow_date_hist + timedelta(days=14)
    assert database.insert_borrow_record(patron, b2["id"], borrow_date_hist, due_date_hist)
    #return before due date
    assert database.update_borrow_record_return_date(patron, b2["id"], borrow_date_hist + timedelta(days=5))
    #no availability change needed if your return flow does it; ensure available is correct
    assert database.update_book_availability(b2["id"], +1)

    #follow the arrange, act, assert structure
    report = get_patron_status_report(patron)

    for key in ("current_loans", "total_late_fees", "borrowed_count", "history"):
        assert key in report

    #borrowed count should reflect only current (unreturned) loans
    assert isinstance(report["borrowed_count"], int)
    assert report["borrowed_count"] == 1

    #the current loans contain our overdue b1 with a due date
    assert isinstance(report["current_loans"], list) and len(report["current_loans"]) == 1
    curr = report["current_loans"][0]
    assert curr["book_id"] == b1["id"]
    assert "due_date" in curr
    #allow date as ISO string 'YYYY-MM-DD...' or already formatted, this is a basic check
    assert str(curr["due_date"])[:4].isdigit()

    #total late fees should include the 6 overdue days at $0.50 = $3.00 (within rounding)
    fee = float(report["total_late_fees"]) if not isinstance(report["total_late_fees"], (int, float)) else report["total_late_fees"]
    assert round(fee, 2) == 3.00

    #the history should at least include the returned b2 record
    assert isinstance(report["history"], list) and len(report["history"]) >= 1
    hist_ids = [h.get("book_id") for h in report["history"]]
    assert b2["id"] in hist_ids



def test_patron_status_no_loans_returns_empty_zero():
    """R7 negative: patron with no loans should get zeros and empty lists."""
    patron = "000111"

    report = get_patron_status_report(patron)
    
    assert report["borrowed_count"] == 0
    assert float(report["total_late_fees"]) == 0.00
    assert isinstance(report["current_loans"], list) and len(report["current_loans"]) == 0
    assert isinstance(report["history"], list) and len(report["history"]) == 0


def test_patron_status_multiple_current_loans_fee_sum_and_count():
    """R7 positive: two current overdue loans; fees should sum and count should be 2."""
    patron = "123457"


    ok, _ = add_book_to_catalog("Overdue Five", "Tester", "9012345678901", 1)
    assert ok is True
    ok, _ = add_book_to_catalog("Overdue Ten", "Tester", "9012345678902", 1)
    assert ok is True
    b1 = database.get_book_by_isbn("9012345678901")
    b2 = database.get_book_by_isbn("9012345678902")
    assert b1 and b2

    #5 days overdue today -> $2.50
    borrow_1 = datetime.now() - timedelta(days=19)   # 14 + 5
    due_1 = borrow_1 + timedelta(days=14)
    assert database.insert_borrow_record(patron, b1["id"], borrow_1, due_1)
    assert database.update_book_availability(b1["id"], -1)

    #10 days overdue today -> $6.50
    borrow_2 = datetime.now() - timedelta(days=24)   # 14 + 10
    due_2 = borrow_2 + timedelta(days=14)
    assert database.insert_borrow_record(patron, b2["id"], borrow_2, due_2)
    assert database.update_book_availability(b2["id"], -1)

    report = get_patron_status_report(patron)

    assert report["borrowed_count"] == 2
    assert len(report["current_loans"]) == 2
    ids = {row["book_id"] for row in report["current_loans"]}
    assert b1["id"] in ids and b2["id"] in ids
    assert round(float(report["total_late_fees"]), 2) == 9.00  # 2.50 + 6.50


def test_patron_status_history_dates_are_strings():
    """R7 format: history returns date strings 'YYYY-MM-DD' for borrow/return."""
    patron = "123458"

    #add one book, borrow and return next day (on time)
    ok, _ = add_book_to_catalog("History Book", "Tester", "9012345678903", 1)
    assert ok is True
    b = database.get_book_by_isbn("9012345678903")
    assert b

    borrow_date = datetime.now() - timedelta(days=5)
    due_date = borrow_date + timedelta(days=14)
    assert database.insert_borrow_record(patron, b["id"], borrow_date, due_date)
    ret_date = borrow_date + timedelta(days=1)
    assert database.update_borrow_record_return_date(patron, b["id"], ret_date)
    assert database.update_book_availability(b["id"], +1)

    report = get_patron_status_report(patron)

    assert report["borrowed_count"] == 0
    assert float(report["total_late_fees"]) == 0.00
    assert len(report["history"]) == 1
    h = report["history"][0]
    # dates are strings like 'YYYY-MM-DD'
    assert isinstance(h["borrow_date"], str) and len(h["borrow_date"]) == 10
    assert h["borrow_date"].count("-") == 2
    assert (h["return_date"] is None) or (isinstance(h["return_date"], str) and len(h["return_date"]) == 10)
