import pytest
from datetime import datetime, timedelta

import database
from library_service import (
    add_book_to_catalog,
    calculate_late_fee_for_book
)

# four unit tests for the calculate_late_fee_for_book function

def test_late_fee_not_overdue():
    """Book returned on or before due date should have $0 fee and 0 days overdue."""
    
    #add a book, borrow it, then return BEFORE due date
    ok, _ = add_book_to_catalog("On Time", "Author", "1010101010101", 1)
    assert ok is True
    book = database.get_book_by_isbn("1010101010101")
    assert book is not None

    borrow_date = datetime.now() - timedelta(days=5)     # due in 9 days
    due_date = borrow_date + timedelta(days=14)
    assert database.insert_borrow_record("123456", book["id"], borrow_date, due_date) is True
    assert database.update_book_availability(book["id"], -1) is True
    # Return today (still before due)
    assert database.update_borrow_record_return_date("123456", book["id"], datetime.now()) is True
    assert database.update_book_availability(book["id"], +1) is True

  
    result = calculate_late_fee_for_book("123456", book["id"])


    assert isinstance(result, dict)
    assert result["fee_amount"] == 0.00
    assert result["days_overdue"] == 0


def test_late_fee_within_first_week():
    """5 days overdue should charge $0.50 per day = $2.50."""
    #add a book and backdate borrow so it's 5 days overdue today
    ok, _ = add_book_to_catalog("Fee A", "Author", "2020202020202", 1)
    assert ok is True
    book = database.get_book_by_isbn("2020202020202")
    assert book is not None

    borrow_date = datetime.now() - timedelta(days=19)    # 14 + 5
    due_date = borrow_date + timedelta(days=14)
    assert database.insert_borrow_record("123456", book["id"], borrow_date, due_date) is True
    assert database.update_book_availability(book["id"], -1) is True


    result = calculate_late_fee_for_book("123456", book["id"])

    assert isinstance(result, dict)
    assert result["days_overdue"] == 5
    assert result["fee_amount"] == 2.50


def test_late_fee_beyond_one_week():
    """10 days overdue: 7 days * $0.50 + 3 days * $1.00 = $6.50."""
    # 10 days overdue today
    ok, _ = add_book_to_catalog("Fee B", "Author", "3030303030303", 1)
    assert ok is True
    book = database.get_book_by_isbn("3030303030303")
    assert book is not None

    borrow_date = datetime.now() - timedelta(days=24)    # 14 + 10
    due_date = borrow_date + timedelta(days=14)
    assert database.insert_borrow_record("123456", book["id"], borrow_date, due_date) is True
    assert database.update_book_availability(book["id"], -1) is True


    result = calculate_late_fee_for_book("123456", book["id"])

 
    assert isinstance(result, dict)
    assert result["days_overdue"] == 10
    assert result["fee_amount"] == 6.50  # 7*0.50 + 3*1.00


def test_late_fee_cap_maximum():
    """Fees should not exceed $15.00 regardless of overdue days."""
    # very overdue (well past the cap)
    ok, _ = add_book_to_catalog("Fee C", "Author", "4040404040404", 1)
    assert ok is True
    book = database.get_book_by_isbn("4040404040404")
    assert book is not None

    borrow_date = datetime.now() - timedelta(days=74)    # 14 + 60 -> 60 overdue
    due_date = borrow_date + timedelta(days=14)
    assert database.insert_borrow_record("123456", book["id"], borrow_date, due_date) is True
    assert database.update_book_availability(book["id"], -1) is True


    result = calculate_late_fee_for_book("123456", book["id"])

    assert isinstance(result, dict)
    assert result["days_overdue"] >= 60
    assert result["fee_amount"] == 15.00  # capped
