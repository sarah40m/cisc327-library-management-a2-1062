# Assignment 1

**Name:** Sarah Mohammad 
**Student ID:** 20391062 
**Group Number:** 3 

---

## Function Implementation Report

| Function Name             | Implementation Status | What’s Missing                                                                 |
|----------------------------|-----------------------|--------------------------------------------------------------------------------|
| add_book_to_catalog        | Complete              | –                                                                              |
| borrow_book_by_patron      | Complete              | –                                                                              |
| return_book_by_patron      | Incomplete            | Must verify the book was borrowed by the patron, update available copies, record return date, and calculate/display any late fees owed. |
| calculate_late_fee_for_book| Incomplete            | API endpoint `GET /api/late_fee/<patron_id>/<book_id>` not implemented. Needs to calculate late fees based on due date (14 days), apply $0.50/day for first 7 days overdue, $1.00/day thereafter, cap at $15/book, and return fee + days overdue in JSON format. |
| search_books_in_catalog    | Incomplete            | Search endpoint missing. Must support parameters: `q` (search term) and `type` (title, author, ISBN). Needs partial case-insensitive matching for title/author, exact matching for ISBN, and return results in catalog format. |
| get_patron_status_report   | Incomplete            | Needs functionality to display patron’s current borrowed books with due dates, total late fees owed, number of books currently borrowed, and borrowing history. |


# Test Script Summary

For **f1_test.py** and **f2_test.py**, all the tests passed successfully.  

**f1_test.py** tests the `add_book_to_catalog` function. The cases check both valid input (adding a book successfully) and invalid inputs such as ISBN too short, missing title, missing author, overly long title, and invalid number of copies. This ensures the catalog correctly validates new book entries before adding them.  

**f2_test.py** tests the `borrow_book_by_patron` function. The cases focus on validating patron IDs (too short, non-numeric, or empty) and handling invalid book IDs (negative values or wrong type). These tests confirm that only properly formatted patron IDs and valid book IDs are accepted when borrowing.

Since these functions have already been implemented, I was able to properly test both positive and negative cases, and all tests passed.

For the other test files (**f3_test.py**, **f4_test.py**, **f5_test.py**, **f6_test.py**), the tests failed because the corresponding functions have not been implemented yet. The test cases are still written to match the requirements:

- **(f3_test.py)** → Returning a book: should validate patron ID, check if the book was borrowed, update copies, and confirm the return.  
- **(f4_test.py)** → Late fee calculation: should calculate overdue days, apply the fee rules, and cap at $15.  
- **(f5_test.py)** → Search: should allow partial case-insensitive matches for title/author and exact match for ISBN.  
- **(f6_test.py)** → Patron status report: should show current loans with due dates, total fees, number of books borrowed, and borrowing history.

As of now I could only fully verify the functionality for **f1** and **f2**, while the rest will pass once their code is implemented.