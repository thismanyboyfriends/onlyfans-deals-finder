"""SQLite database management for OnlyFans user data."""
import sqlite3
import logging
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """Manages SQLite database for OnlyFans scraper data."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to data/scraper.db
        """
        if db_path is None:
            # Get project root (one level up from src)
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "scraper.db"

        self.db_path = db_path
        self.conn = None
        self._connect()
        self._init_schema()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        logger.info(f"Connected to database: {self.db_path}")

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        cursor = self.conn.cursor()

        # Scrape runs table - tracks each scraping session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                user_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running'
            )
        """)

        # Users table - current state of each user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                display_name TEXT,
                current_price REAL,
                subscription_status TEXT,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                last_scraped_run_id INTEGER,
                FOREIGN KEY (last_scraped_run_id) REFERENCES scrape_runs(id)
            )
        """)

        # Price history table - tracks all price changes over time
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                price REAL NOT NULL,
                subscription_status TEXT,
                scraped_at TIMESTAMP NOT NULL,
                scrape_run_id INTEGER NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (scrape_run_id) REFERENCES scrape_runs(id)
            )
        """)

        # Lists table - tracks which lists users appear in
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                list_name TEXT NOT NULL,
                added_at TIMESTAMP NOT NULL,
                removed_at TIMESTAMP,
                scrape_run_id INTEGER NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (scrape_run_id) REFERENCES scrape_runs(id)
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_username ON price_history(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_scraped_at ON price_history(scraped_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_lists_username ON user_lists(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_lists_list_name ON user_lists(list_name)")

        self.conn.commit()
        logger.info("Database schema initialized")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    def start_scrape_run(self, list_id: str, started_at: Optional[datetime] = None) -> int:
        """Start a new scrape run and return its ID.

        Args:
            list_id: The list ID being scraped
            started_at: Optional datetime for the scrape (defaults to now)

        Returns:
            The ID of the created scrape run
        """
        if started_at is None:
            started_at = datetime.now()

        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO scrape_runs (list_id, started_at, status)
                VALUES (?, ?, 'running')
            """, (list_id, started_at))
            return cursor.lastrowid

    def complete_scrape_run(self, run_id: int, user_count: int, status: str = 'completed'):
        """Mark a scrape run as completed."""
        with self.transaction() as cursor:
            cursor.execute("""
                UPDATE scrape_runs
                SET completed_at = ?, user_count = ?, status = ?
                WHERE id = ?
            """, (datetime.now(), user_count, status, run_id))

    def upsert_user(self, username: str, price: float, subscription_status: str,
                    lists: List[str], run_id: int, scraped_at: Optional[datetime] = None):
        """Insert or update user data.

        Args:
            username: OnlyFans username
            price: Subscription price
            subscription_status: NO_SUBSCRIPTION or SUBSCRIBED
            lists: List of list names
            run_id: The scrape run ID
            scraped_at: Optional timestamp for when this was scraped (defaults to now)
        """
        if scraped_at is None:
            scraped_at = datetime.now()

        with self.transaction() as cursor:
            # Check if user exists
            cursor.execute("SELECT username, current_price FROM users WHERE username = ?", (username,))
            existing = cursor.fetchone()

            if existing:
                old_price = existing['current_price']

                # Update user
                cursor.execute("""
                    UPDATE users
                    SET current_price = ?, subscription_status = ?,
                        last_seen = ?, last_scraped_run_id = ?
                    WHERE username = ?
                """, (price, subscription_status, scraped_at, run_id, username))

                # Log price change
                if old_price != price:
                    logger.info(f"Price change for {username}: ${old_price} -> ${price}")
            else:
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (username, current_price, subscription_status,
                                     first_seen, last_seen, last_scraped_run_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, price, subscription_status, scraped_at, scraped_at, run_id))
                logger.debug(f"New user added: {username}")

            # Always insert into price history
            cursor.execute("""
                INSERT INTO price_history (username, price, subscription_status,
                                         scraped_at, scrape_run_id)
                VALUES (?, ?, ?, ?, ?)
            """, (username, price, subscription_status, scraped_at, run_id))

            # Update lists
            self._update_user_lists(cursor, username, lists, run_id, scraped_at)

    def _update_user_lists(self, cursor, username: str, current_lists: List[str],
                           run_id: int, now: datetime):
        """Update which lists a user belongs to."""
        # Get currently active lists for this user
        cursor.execute("""
            SELECT list_name FROM user_lists
            WHERE username = ? AND removed_at IS NULL
        """, (username,))

        existing_lists = {row['list_name'] for row in cursor.fetchall()}
        new_lists = set(current_lists)

        # Lists to add
        to_add = new_lists - existing_lists
        for list_name in to_add:
            cursor.execute("""
                INSERT INTO user_lists (username, list_name, added_at, scrape_run_id)
                VALUES (?, ?, ?, ?)
            """, (username, list_name, now, run_id))

        # Lists to remove (mark as removed)
        to_remove = existing_lists - new_lists
        for list_name in to_remove:
            cursor.execute("""
                UPDATE user_lists
                SET removed_at = ?
                WHERE username = ? AND list_name = ? AND removed_at IS NULL
            """, (now, username, list_name))

    def get_price_history(self, username: str) -> List[Dict]:
        """Get price history for a user."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT price, subscription_status, scraped_at
            FROM price_history
            WHERE username = ?
            ORDER BY scraped_at DESC
        """, (username,))

        return [dict(row) for row in cursor.fetchall()]

    def get_price_changes(self, days: int = 30) -> List[Dict]:
        """Get users whose prices changed in the last N days."""
        cursor = self.conn.cursor()
        cursor.execute("""
            WITH ranked_prices AS (
                SELECT
                    username,
                    price,
                    scraped_at,
                    LAG(price) OVER (PARTITION BY username ORDER BY scraped_at) as prev_price
                FROM price_history
                WHERE scraped_at >= datetime('now', '-' || ? || ' days')
            )
            SELECT username, prev_price, price, scraped_at
            FROM ranked_prices
            WHERE prev_price IS NOT NULL AND prev_price != price
            ORDER BY scraped_at DESC
        """, (days,))

        return [dict(row) for row in cursor.fetchall()]

    def get_historical_low_prices(self) -> List[Dict]:
        """Get users currently at their historical low price."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                u.username,
                u.current_price,
                MIN(ph.price) as historical_low,
                COUNT(DISTINCT ph.scrape_run_id) as scrape_count
            FROM users u
            JOIN price_history ph ON u.username = ph.username
            WHERE u.subscription_status = 'NO_SUBSCRIPTION'
            GROUP BY u.username
            HAVING u.current_price = historical_low AND scrape_count > 1
            ORDER BY u.current_price
        """)

        return [dict(row) for row in cursor.fetchall()]

    def get_users_with_lists(self, active_only: bool = True) -> List[Dict]:
        """Get all users with their current lists."""
        cursor = self.conn.cursor()

        removed_clause = "AND ul.removed_at IS NULL" if active_only else ""

        cursor.execute(f"""
            SELECT
                u.username,
                u.current_price,
                u.subscription_status,
                GROUP_CONCAT(ul.list_name) as lists
            FROM users u
            LEFT JOIN user_lists ul ON u.username = ul.username {removed_clause}
            GROUP BY u.username
        """)

        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data['lists'] = data['lists'].split(',') if data['lists'] else []
            results.append(data)

        return results

    def get_stats(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()['total_users']

        cursor.execute("SELECT COUNT(*) as total_scrapes FROM scrape_runs WHERE status = 'completed'")
        total_scrapes = cursor.fetchone()['total_scrapes']

        cursor.execute("SELECT COUNT(*) as price_records FROM price_history")
        price_records = cursor.fetchone()['price_records']

        cursor.execute("""
            SELECT started_at FROM scrape_runs
            WHERE status = 'completed'
            ORDER BY started_at DESC LIMIT 1
        """)
        last_scrape = cursor.fetchone()
        last_scrape_date = last_scrape['started_at'] if last_scrape else None

        return {
            'total_users': total_users,
            'total_scrapes': total_scrapes,
            'price_records': price_records,
            'last_scrape': last_scrape_date
        }

    @staticmethod
    def _extract_date_from_filename(csv_path: Path) -> Optional[datetime]:
        """Extract date from CSV filename in format output-YYYY-MM-DD.csv

        Args:
            csv_path: Path to CSV file

        Returns:
            Datetime object at start of day, or None if no date found
        """
        filename = csv_path.stem  # Get filename without extension
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)

        if match:
            year, month, day = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None

        return None

    def import_csv(self, csv_path: Path, list_id: str = "imported",
                   scraped_at: Optional[datetime] = None) -> int:
        """Import data from a CSV file into the database.

        Args:
            csv_path: Path to CSV file (must have columns: username, price, subscription_status, lists)
            list_id: List ID to associate with this import (default: "imported")
            scraped_at: Optional datetime for when data was scraped. If None, attempts to extract from filename.
                       Filename format: output-YYYY-MM-DD.csv

        Returns:
            Number of users imported
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Extract date from filename if not provided
        if scraped_at is None:
            extracted_date = self._extract_date_from_filename(csv_path)
            if extracted_date:
                scraped_at = extracted_date
                logger.info(f"Extracted date from filename: {scraped_at.date()}")
            else:
                logger.warning(f"Could not extract date from filename. Using current time.")
                scraped_at = datetime.now()

        # Create a scrape run for this import with the specified timestamp
        run_id = self.start_scrape_run(list_id, started_at=scraped_at)
        logger.info(f"Importing from {csv_path.name} (dated: {scraped_at.strftime('%Y-%m-%d %H:%M:%S')})")
        user_count = 0

        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Validate required columns
                if not reader.fieldnames:
                    raise ValueError("CSV file is empty")

                required_cols = {'username', 'price', 'subscription_status', 'lists'}
                csv_cols = set(reader.fieldnames)

                if not required_cols.issubset(csv_cols):
                    missing = required_cols - csv_cols
                    raise ValueError(f"CSV missing required columns: {missing}")

                # Process each row
                for row in reader:
                    try:
                        username = row['username'].strip()
                        if not username:
                            logger.warning("Skipping row with empty username")
                            continue

                        # Parse price - handle various formats
                        price_str = row['price'].strip()
                        try:
                            price = float(price_str) if price_str and price_str != '?' else 0.0
                        except ValueError:
                            logger.warning(f"Could not parse price '{price_str}' for {username}, using 0.0")
                            price = 0.0

                        # Get subscription status
                        status = row['subscription_status'].strip() or "NO_SUBSCRIPTION"

                        # Parse lists - can be comma-separated
                        lists_str = row['lists'].strip()
                        lists = [l.strip() for l in lists_str.split(',') if l.strip()] if lists_str else []

                        # Insert user data with the scraped timestamp
                        self.upsert_user(username, price, status, lists, run_id, scraped_at=scraped_at)
                        user_count += 1

                        if user_count % 100 == 0:
                            logger.info(f"Imported {user_count} users...")

                    except Exception as e:
                        logger.warning(f"Error importing row {user_count + 1}: {e}")
                        continue

            # Mark import as complete
            self.complete_scrape_run(run_id, user_count, 'completed')
            logger.info(f"Successfully imported {user_count} users from {csv_path.name} dated {scraped_at.strftime('%Y-%m-%d')}")

            return user_count

        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            # Mark as failed
            self.complete_scrape_run(run_id, 0, 'failed')
            raise

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
