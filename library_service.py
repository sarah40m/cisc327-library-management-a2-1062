"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import database 

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = database.get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = database.insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."


def get_catalog_view() -> List[Dict]:
    """
    R2: Build the catalog rows from DB.
    Fields: book_id, title, author, isbn, available_copies, total_copies, actions
    'actions' includes 'Borrow' only if available_copies > 0.
    """
    rows: List[Dict] = []
    for b in database.get_all_books():
        rows.append({
            "book_id": b["id"],
            "title": b["title"],
            "author": b["author"],
            "isbn": b["isbn"],
            "available_copies": b["available_copies"],
            "total_copies": b["total_copies"],
            "actions": "Borrow" if b["available_copies"] > 0 else "",
        })
    return rows



def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = database.get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = database.get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = database.insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = database.update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'



def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    R4: Accept patron_id & book_id, verify active borrow, set return_date,
    increment availability, and include any late fee in the message.
    Enforces: patron_id 6 digits, available_copies cannot exceed total.
    """
    pid = str(patron_id or "")
    if not (pid.isdigit() and len(pid) == 6):
        return False, "Invalid patron ID (must be 6 digits)."

    book = database.get_book_by_id(int(book_id))
    if not book:
        return False, "Book not found."

    #verify an active borrow exists for this patron & book
    conn = database.get_db_connection()
    rec = conn.execute(
        "SELECT id FROM borrow_records WHERE patron_id=? AND book_id=? AND return_date IS NULL",
        (pid, int(book_id)),
    ).fetchone()
    conn.close()
    if not rec:
        return False, "No active borrow record for this patron and book."

    #guards against exceeding total copies (spec constraint)
    if book["available_copies"] >= book["total_copies"]:
        return False, "Available copies cannot exceed total copies."

    #record return date
    if not database.update_borrow_record_return_date(pid, int(book_id), datetime.now()):
        return False, "Could not update return date."

    #increment availability (+1)
    if not database.update_book_availability(int(book_id), +1):
        return False, "Could not update book availability."

    #late fee (R5 policy)
    fee_info = calculate_late_fee_for_book(pid, int(book_id))
    fee = float(fee_info.get("fee_amount", 0.0))

    msg = "Book returned successfully."
    if fee > 0:
        msg += f" Late fee: ${fee:.2f}"
    return True, msg


def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    R5: Late fee where due = borrow_date + 14 days.
    $0.50/day for first 7 overdue days, then $1.00/day; cap $15.00.
    Returns {'fee_amount': float(2dp), 'days_overdue': int}.
    """
    conn = database.get_db_connection()
    r = conn.execute(
        """
        SELECT borrow_date, due_date, return_date
        FROM borrow_records
        WHERE patron_id=? AND book_id=?
        ORDER BY borrow_date DESC
        LIMIT 1
        """,
        (str(patron_id), int(book_id)),
    ).fetchone()
    conn.close()

    if not r:
        return {"fee_amount": 0.00, "days_overdue": 0}

    due = datetime.fromisoformat(r["due_date"])
    #if returned, compute based on return_date, otherwise use now
    stop = datetime.fromisoformat(r["return_date"]) if r["return_date"] else datetime.now()

    days_overdue = max(0, (stop.date() - due.date()).days)
    fee = 0.50 * min(days_overdue, 7) + 1.00 * max(days_overdue - 7, 0)
    fee = min(15.00, fee)

    return {"fee_amount": round(fee, 2), "days_overdue": int(days_overdue)}


def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    R6: Search with parameters q=search_term and type in {title, author, isbn}.
    - title/author: partial, case-insensitive
    - isbn: exact match
    Returns rows in the same shape as catalog rows (R2).
    """
    term = (search_term or "").strip()
    stype = (search_type or "").strip().lower()

    books = database.get_all_books()
    if stype == "isbn":
        books = [b for b in books if b["isbn"] == term]
    elif stype == "title":
        books = [b for b in books if term.lower() in b["title"].lower()]
    elif stype == "author":
        books = [b for b in books if term.lower() in b["author"].lower()]
    else:
        return []

    rows: List[Dict] = []
    for b in books:
        rows.append({
            "book_id": b["id"],
            "title": b["title"],
            "author": b["author"],
            "isbn": b["isbn"],
            "available_copies": b["available_copies"],
            "total_copies": b["total_copies"],
            "actions": "Borrow" if b["available_copies"] > 0 else "",
        })
    return rows


def get_patron_status_report(patron_id: str) -> Dict:
    """
    R7: Report for a patron including:
      - current loans with due dates
      - total late fees owed (sum over current loans)
      - number of books currently borrowed
      - borrowing history (all records)
    Monetary values are 2 decimals as per constraints.
    """
    pid = str(patron_id)

    #current loans (database.get_patron_borrowed_books returns datetimes)
    current = database.get_patron_borrowed_books(pid)
    current_rows = [{
        "book_id": b["book_id"],
        "title": b["title"],
        "due_date": b["due_date"].strftime("%Y-%m-%d"),
    } for b in current]

    #total late fees across current loans only
    total_fee = 0.0
    for b in current:
        info = calculate_late_fee_for_book(pid, b["book_id"])
        total_fee += float(info["fee_amount"])

    #full borrowing history (returned + current)
    conn = database.get_db_connection()
    rows = conn.execute(
        """
        SELECT br.book_id, b.title, br.borrow_date, br.return_date
        FROM borrow_records br
        JOIN books b ON b.id = br.book_id
        WHERE br.patron_id=?
        ORDER BY br.borrow_date
        """,
        (pid,),
    ).fetchall()
    conn.close()

    history = [{
        "book_id": r["book_id"],
        "title": r["title"],
        "borrow_date": r["borrow_date"][:10],
        "return_date": r["return_date"][:10] if r["return_date"] else None,
    } for r in rows]

    return {
        "current_loans": current_rows,
        "total_late_fees": round(total_fee, 2),
        "borrowed_count": len(current_rows),
        "history": history,
    }

