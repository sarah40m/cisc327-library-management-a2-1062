import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
from library_service import (
    add_book_to_catalog,
    get_catalog_view,
    borrow_book_by_patron,
    return_book_by_patron,
    calculate_late_fee_for_book,
    search_books_in_catalog,
    get_patron_status_report,
)

# --- Mocking Fixtures and Helpers ---

PATRON_ID = "123456"

# Helper for consistent datetime mocking
def mock_datetime(target_date: datetime):
    """Returns a class that mocks datetime.now()."""
    class MockDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return target_date
    return MockDatetime

# --- R1: add_book_to_catalog Tests (Book Catalog Management) ---

@patch("database.insert_book")
@patch("database.get_book_by_isbn")
def test_r1_1_successful_addition(mock_get_by_isbn, mock_insert):
    """Test adding a book with valid input (R1)."""
    # Simulate DB state: Book does not exist, insertion succeeds
    mock_get_by_isbn.return_value = None
    mock_insert.return_value = True
    
    title = "Test Book"
    success, message = add_book_to_catalog(title, "Test Author", "9781234567890", 5)
    
    assert success is True
    assert f'Book "{title}" has been successfully added' in message
    mock_insert.assert_called_once()

@pytest.mark.parametrize("title, author, isbn, copies, expected_msg", [
    ("", "Author", "9780000000001", 1, "Title is required."),
    ("A" * 201, "Author", "9780000000003", 1, "Title must be less than 200 characters."),
    ("Title", "Author", "1234567890", 1, "ISBN must be exactly 13 digits."),
    ("Title", "Author", "9780000000006", 0, "Total copies must be a positive integer."),
])
@patch("database.get_book_by_isbn")
def test_r1_input_validation_failures(mock_get_by_isbn, title, author, isbn, copies, expected_msg):
    """Test various input constraint checks."""
    mock_get_by_isbn.return_value = None
    success, message = add_book_to_catalog(title, author, isbn, copies)
    assert success is False
    assert message == expected_msg

@patch("database.get_book_by_isbn")
def test_r1_duplicate_isbn_failure(mock_get_by_isbn):
    """Test constraint check: Duplicate ISBN."""
    # Simulate DB state: Book already exists
    mock_get_by_isbn.return_value = {"id": 1}
    success, message = add_book_to_catalog("Title", "Author", "9781476740177", 1)
    assert success is False
    assert message == "A book with this ISBN already exists."

# --------------------------------------------------------------------------------------

# --- R2: get_catalog_view Tests ---

@patch("database.get_all_books")
def test_r2_catalog_view_mixed_availability(mock_get_all_books):
    """Test catalog view formatting including the 'actions' field (R2)."""
    mock_books = [
        {"id": 1, "title": "Available", "author": "A", "isbn": "1", "available_copies": 5, "total_copies": 5},
        {"id": 2, "title": "Unavailable", "author": "B", "isbn": "2", "available_copies": 0, "total_copies": 3},
    ]
    mock_get_all_books.return_value = mock_books
    
    view = get_catalog_view()
    
    assert len(view) == 2
    assert view[0]["title"] == "Available"
    assert view[0]["actions"] == "Borrow"
    assert view[1]["title"] == "Unavailable"
    assert view[1]["actions"] == ""

# --------------------------------------------------------------------------------------

# --- R3: borrow_book_by_patron Tests ---

MOCK_BOOK_AVAILABLE = {"id": 1, "title": "Title A", "available_copies": 3}

@patch("database.update_book_availability")
@patch("database.insert_borrow_record")
@patch("database.get_patron_borrow_count")
@patch("database.get_book_by_id")
@patch('library_service.datetime', mock_datetime(datetime(2025, 10, 12))) 
def test_r3_1_successful_borrow(mock_get_book, mock_get_count, mock_insert_borrow, mock_update_avail):
    """Test successful book borrowing (R3)."""
    # Simulate success state
    mock_get_book.return_value = MOCK_BOOK_AVAILABLE
    mock_get_count.return_value = 2 # Under limit
    mock_insert_borrow.return_value = True
    mock_update_avail.return_value = True

    success, message = borrow_book_by_patron(PATRON_ID, 1)
    
    assert success is True
    # Verify due date calculation (14 days later)
    assert "Due date: 2025-10-26" in message
    mock_update_avail.assert_called_once_with(1, -1)

@patch("database.get_patron_borrow_count")
@patch("database.get_book_by_id")
def test_r3_6_max_borrow_limit_reached(mock_get_book, mock_get_count):
    """Test failure when patron reaches the 5-book limit (R3)."""
    mock_get_book.return_value = MOCK_BOOK_AVAILABLE
    mock_get_count.return_value = 5
    
    success, message = borrow_book_by_patron("654321", 1)
    
    assert success is False
    assert "maximum borrowing limit of 5 books" in message

# --------------------------------------------------------------------------------------

# --- R4: return_book_by_patron Tests ---

MOCK_BOOK_RETURNABLE = {"id": 10, "title": "Return Book", "total_copies": 5, "available_copies": 3}

@patch("library_service.calculate_late_fee_for_book")
@patch("database.update_book_availability")
@patch("database.update_borrow_record_return_date")
@patch("database.get_db_connection")
@patch("database.get_book_by_id")
def test_r4_1_successful_on_time_return(mock_get_book, mock_get_conn, mock_update_ret_date, mock_update_avail, mock_fee_calc):
    """Test successful on-time book return (R4)."""
    mock_get_book.return_value = MOCK_BOOK_RETURNABLE
    
    # Mock connection: Active borrow found
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchone.return_value = {"id": 1}
    mock_get_conn.return_value = mock_conn

    mock_update_ret_date.return_value = True
    mock_update_avail.return_value = True
    mock_fee_calc.return_value = {"fee_amount": 0.00, "days_overdue": 0}
    
    success, message = return_book_by_patron(PATRON_ID, 10)
    
    assert success is True
    assert message == "Book returned successfully."
    mock_update_avail.assert_called_once_with(10, +1)

@patch("library_service.calculate_late_fee_for_book")
@patch("database.get_db_connection")
@patch("database.get_book_by_id")
def test_r4_2_successful_late_return_with_fee(mock_get_book, mock_get_conn, mock_fee_calc):
    """Test successful late return with fee message (R4)."""
    mock_get_book.return_value = MOCK_BOOK_RETURNABLE
    
    # Mock connection: Active borrow found
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchone.return_value = {"id": 2}
    mock_get_conn.return_value = mock_conn
    
    # Mock fee to trigger the fee message
    mock_fee_calc.return_value = {"fee_amount": 2.50, "days_overdue": 5}
    
    with patch("database.update_borrow_record_return_date", return_value=True), \
         patch("database.update_book_availability", return_value=True):
        
        success, message = return_book_by_patron("222222", 10)
        
        assert success is True
        assert message == "Book returned successfully. Late fee: $2.50"

@patch("database.get_db_connection")
@patch("database.get_book_by_id")
def test_r4_6_copies_maxed_failure(mock_get_book, mock_get_conn):
    """Test failure when available copies would exceed total copies (R4 constraint)."""
    mock_get_book.return_value = {"id": 40, "total_copies": 5, "available_copies": 5}
    
    # Mock connection: Active borrow found
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchone.return_value = {"id": 4}
    mock_get_conn.return_value = mock_conn
    
    success, message = return_book_by_patron("444444", 40)
    
    assert success is False
    assert "Available copies cannot exceed total copies" in message

# --------------------------------------------------------------------------------------

# --- R5: calculate_late_fee_for_book Tests ---

@pytest.mark.parametrize("due_date_str, stop_date, expected_days, expected_fee", [
    # On-time/Early return
    ("2025-10-15", datetime(2025, 10, 14), 0, 0.00),
    # 5 days late @ $0.50
    ("2025-10-15", datetime(2025, 10, 20), 5, 2.50),
    # 10 days late (7*0.5 + 3*1.0 = $6.50)
    ("2025-10-15", datetime(2025, 10, 25), 10, 6.50),
    # 45 days late, capped at $15.00
    ("2025-10-15", datetime(2025, 11, 29), 45, 15.00),
])
@patch("database.get_db_connection")
def test_r5_fee_calculation(mock_get_conn, due_date_str, stop_date, expected_days, expected_fee):
    """Test late fee calculation based on R5 policy."""
    borrow_date_str = (datetime.fromisoformat(due_date_str) - timedelta(days=14)).isoformat()
    
    # Determine if we should mock return_date (for returned books) or datetime.now() (for current loans)
    is_current_loan = stop_date.date() > datetime.fromisoformat(due_date_str).date()
    return_date_db = None if is_current_loan else stop_date.isoformat()
    
    mock_record = {"borrow_date": borrow_date_str, "due_date": due_date_str, "return_date": return_date_db}
    
    # Mock connection: returns the mock borrow record
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchone.return_value = mock_record
    mock_get_conn.return_value = mock_conn

    # Use context manager to mock datetime.now() if calculating fee for a current loan
    if is_current_loan:
        with patch('library_service.datetime', mock_datetime(stop_date)):
            result = calculate_late_fee_for_book(PATRON_ID, 1)
    else:
        result = calculate_late_fee_for_book(PATRON_ID, 1)
    
    assert result["days_overdue"] == expected_days
    assert result["fee_amount"] == expected_fee

# --------------------------------------------------------------------------------------

# --- R6: search_books_in_catalog Tests ---

MOCK_CATALOG = [
    {"id": 1, "title": "The Lord of the Rings", "author": "J.R.R. Tolkien", "isbn": "9781234567890", "available_copies": 2, "total_copies": 5},
    {"id": 2, "title": "Harry Potter", "author": "J.K. Rowling", "isbn": "9781111111111", "available_copies": 0, "total_copies": 3},
]

@patch("database.get_all_books")
@pytest.mark.parametrize("search_term, search_type, expected_count, expected_titles", [
    ("lord", "title", 1, ["The Lord of the Rings"]),
    ("tolkien", "author", 1, ["The Lord of the Rings"]),
    ("9781234567890", "isbn", 1, ["The Lord of the Rings"]),
    ("Zyzzyva", "title", 0, []),
    ("", "title", 0, []),
    ("test", "genre", 0, []), # Invalid type returns empty
])
def test_r6_search_functionality(mock_get_all_books, search_term, search_type, expected_count, expected_titles):
    """Test search by title, author, and ISBN (R6)."""
    mock_get_all_books.return_value = MOCK_CATALOG
    results = search_books_in_catalog(search_term, search_type)
    
    assert len(results) == expected_count
    actual_titles = [r["title"] for r in results]
    assert sorted(actual_titles) == sorted(expected_titles)
    
    if expected_count > 0:
        # Check that R2 formatting is maintained
        assert "actions" in results[0]

# --------------------------------------------------------------------------------------

# --- R7: get_patron_status_report Tests ---

MOCK_CURRENT_LOANS = [
    {"book_id": 1, "title": "Book A", "due_date": datetime(2025, 10, 20)}, 
]
MOCK_FULL_HISTORY = [
    {"book_id": 3, "title": "Book C", "borrow_date": "2025-01-01 10:00:00", "return_date": "2025-01-15 11:00:00"},
    {"book_id": 1, "title": "Book A", "borrow_date": "2025-10-01 12:00:00", "return_date": None},
]

@patch("database.get_patron_borrowed_books")
@patch("library_service.calculate_late_fee_for_book")
@patch("database.get_db_connection")
@patch('library_service.datetime', mock_datetime(datetime(2025, 10, 28))) 
def test_r7_report_with_loans_and_fees(mock_get_conn, mock_fee_calc, mock_get_current):
    """Test patron status report with active loans and late fees (R7)."""
    mock_get_current.return_value = MOCK_CURRENT_LOANS
    mock_fee_calc.return_value = {"fee_amount": 4.50} # Simulating a $4.50 fee
    
    # Mock connection: returns the full history list
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchall.return_value = MOCK_FULL_HISTORY
    mock_get_conn.return_value = mock_conn
    
    report = get_patron_status_report(PATRON_ID)
    
    assert report["borrowed_count"] == 1
    assert report["total_late_fees"] == 4.50 
    assert len(report["current_loans"]) == 1
    assert report["current_loans"][0]["due_date"] == "2025-10-20"
    assert len(report["history"]) == 2

@patch("database.get_patron_borrowed_books")
@patch("database.get_db_connection")
def test_r7_history_only_report(mock_get_conn, mock_get_current):
    """Test patron report when no books are currently borrowed."""
    mock_get_current.return_value = []
    
    # Mock connection: returns only the returned book
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchall.return_value = MOCK_FULL_HISTORY[:1]
    mock_get_conn.return_value = mock_conn
    
    report = get_patron_status_report("300000")
    
    assert report["borrowed_count"] == 0
    assert report["total_late_fees"] == 0.00
    assert len(report["history"]) == 1