"""SQLite database management for OnlyFans user data."""
import sqlite3
import logging
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
