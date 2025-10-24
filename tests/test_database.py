"""Tests for database module."""
import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import Database


@pytest.fixture
def test_db(tmp_path):
    """Create temporary test database."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    yield db
    db.close()


class TestDatabase:
    """Tests for Database class."""

    def test_database_creation(self, test_db):
        """Test that database is created successfully."""
        assert test_db.db_path.exists()
        assert test_db.db_path.suffix == '.db'

    def test_start_scrape_run(self, test_db):
        """Test scrape run creation."""
        run_id = test_db.start_scrape_run("test_list")
        assert isinstance(run_id, int)
        assert run_id > 0

    def test_upsert_user_creates_new_user(self, test_db):
        """Test that upsert_user creates new user record."""
        run_id = test_db.start_scrape_run("test_list")

        test_db.upsert_user(
            username="testuser",
            price=9.99,
            subscription_status="NO_SUBSCRIPTION",
            lists=["paid"],
            run_id=run_id
        )

        history = test_db.get_price_history("testuser")
        assert len(history) == 1
        assert history[0]['price'] == 9.99
        assert history[0]['subscription_status'] == "NO_SUBSCRIPTION"

    def test_upsert_user_updates_existing_user(self, test_db):
        """Test that upsert_user updates existing user."""
        run_id = test_db.start_scrape_run("test_list")

        # Insert initial
        test_db.upsert_user("testuser", 9.99, "NO_SUBSCRIPTION", [], run_id)

        # Update with new price
        run_id2 = test_db.start_scrape_run("test_list")
        test_db.upsert_user("testuser", 7.99, "NO_SUBSCRIPTION", [], run_id2)

        history = test_db.get_price_history("testuser")
        assert len(history) == 2
        assert history[0]['price'] == 7.99  # Most recent first
        assert history[1]['price'] == 9.99  # Older price

    def test_upsert_user_with_free_price(self, test_db):
        """Test handling of free (zero) prices."""
        run_id = test_db.start_scrape_run("test_list")

        test_db.upsert_user(
            username="freeuser",
            price=0.0,
            subscription_status="NO_SUBSCRIPTION",
            lists=["free"],
            run_id=run_id
        )

        history = test_db.get_price_history("freeuser")
        assert len(history) == 1
        assert history[0]['price'] == 0.0

    def test_get_latest_scrape_run_id(self, test_db):
        """Test retrieving latest scrape run ID."""
        run_id1 = test_db.start_scrape_run("list1")
        run_id2 = test_db.start_scrape_run("list2")

        latest_id = test_db.get_latest_scrape_run_id()
        assert latest_id == run_id2

    def test_get_users_by_list(self, test_db):
        """Test retrieving users by list name."""
        run_id = test_db.start_scrape_run("mylist")

        test_db.upsert_user("user1", 5.00, "NO_SUBSCRIPTION", ["mylist"], run_id)
        test_db.upsert_user("user2", 10.00, "NO_SUBSCRIPTION", ["mylist", "other"], run_id)
        test_db.upsert_user("user3", 15.00, "NO_SUBSCRIPTION", ["other"], run_id)

        users = test_db.get_users_by_list("mylist")
        assert len(users) == 2
        usernames = [u['username'] for u in users]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" not in usernames

    def test_price_history_ordering(self, test_db):
        """Test that price history is ordered newest first."""
        run_id1 = test_db.start_scrape_run("list")
        test_db.upsert_user("user", 10.00, "NO_SUBSCRIPTION", [], run_id1)

        run_id2 = test_db.start_scrape_run("list")
        test_db.upsert_user("user", 9.00, "NO_SUBSCRIPTION", [], run_id2)

        run_id3 = test_db.start_scrape_run("list")
        test_db.upsert_user("user", 8.00, "NO_SUBSCRIPTION", [], run_id3)

        history = test_db.get_price_history("user")
        assert len(history) == 3
        assert history[0]['price'] == 8.00
        assert history[1]['price'] == 9.00
        assert history[2]['price'] == 10.00

    def test_invalid_subscription_status(self, test_db):
        """Test that invalid subscription status is stored as provided."""
        run_id = test_db.start_scrape_run("list")

        # Should store the value even if not standard
        test_db.upsert_user("user", 5.00, "CUSTOM_STATUS", [], run_id)

        history = test_db.get_price_history("user")
        assert history[0]['subscription_status'] == "CUSTOM_STATUS"
