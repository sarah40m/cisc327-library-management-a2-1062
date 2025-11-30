from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://127.0.0.1:5000"


# test adding a book and verifying it appears in the catalog
def test_add_book_appears_in_catalog():
    """Add a new book and check that it appears in the catalog."""
    with sync_playwright() as p:
        # launches a real browser session (headless Chromium)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. open home page
        page.goto(BASE_URL)

        # 2. verify the home page loaded (UI text assertion)
        home_text = page.text_content("body").lower()
        assert "library management system" in home_text

        # 3. go to "Add Book" page
        page.click("a:has-text('Add Book')")

        # 4. verify the add book form heading appears (UI text assertion)
        add_page_text = page.text_content("body").lower()
        assert "add new book" in add_page_text

        # 5. fill in the add book form
        # generate a unique 13-digit ISBN each run to avoid duplicate ISBN errors
        unique_isbn = f"9{int(time.time() * 1000):012d}"[-13:]
        page.fill("input[name='title']", "E2E Test Book")
        page.fill("input[name='author']", "QA Bot")
        page.fill("input[name='isbn']", unique_isbn)
        page.fill("input[name='total_copies']", "3")

        # 6. submit the form
        page.click("button:has-text('Add Book')")

        # 7. navigate to the catalog page
        page.click("a:has-text('Catalog')")
        page.wait_for_load_state("networkidle")

        # 8. verify the catalog heading and that the new book title appears
        catalog_text = page.text_content("body").lower()
        assert "book catalog" in catalog_text           # UI heading assertion
        assert "e2e test book" in catalog_text          # verify book appears

        browser.close()
