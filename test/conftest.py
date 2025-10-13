import pytest
import os
from database import init_database

@pytest.fixture(autouse=True)
def setup_test_database():
    import database
    original_database = database.DATABASE
    test_database = "test_library.db"
    database.DATABASE = test_database
    init_database()
    yield
    database.DATABASE = original_database
    if os.path.exists(test_database):
        os.remove(test_database)