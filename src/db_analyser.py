"""Database-based analyzer with historical price tracking."""
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from database import Database

logger = logging.getLogger(__name__)


class DatabaseAnalyser:
    """Analyzes OnlyFans data from SQLite database with historical tracking."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize analyzer with database connection."""
        self.db = Database(db_path)
        logger.info(f"Analyzer connected to database: {self.db.db_path}")

    def analyse_all(self):
        """Run all analysis methods."""
        logger.info("Running comprehensive analysis...")

        self.show_stats()
        self.find_free_accounts()  # Primary target - free unsubscribed accounts
        self.find_categorization_issues()
        self.find_historical_lows()
        self.find_trending_prices()

    def show_stats(self):
        """Show database statistics."""
        stats = self.db.get_stats()

        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        print(f"Total Users:       {stats['total_users']}")
        print(f"Total Scrapes:     {stats['total_scrapes']}")
        print(f"Price Records:     {stats['price_records']}")
        print(f"Last Scrape:       {stats['last_scrape'] or 'Never'}")
        print("="*60)

    def find_free_accounts(self):
        """Find free trial accounts not yet subscribed - PRIMARY TARGET."""
        # Only show users from the most recent scrape run
        latest_run_id = self.db.get_latest_scrape_run_id()
        if not latest_run_id:
            print("\n" + "="*70)
            print("No completed scrape runs found!")
            print("="*70)
            return

        users = self.db.get_users_from_scrape_run(latest_run_id)

        free_users = [
            u for u in users
            if u['subscription_status'] == 'NO_SUBSCRIPTION'
            and u['current_price'] == 0.0
        ]

        if free_users:
            print("\n" + "="*70)
            print("FREE ACCOUNTS YOU'RE NOT SUBSCRIBED TO")
            print(f"Total: {len(free_users)} free trial accounts")
            print("="*70)
            for user in free_users:  # Show all free accounts
                lists_str = ', '.join(user['lists']) if user['lists'] else 'No lists'
                print(f"  ✓ https://onlyfans.com/{user['username']}")
                print(f"    Lists: {lists_str}")
            print("="*70)

            # Save all free accounts to log file
            free_accounts_log = [
                {
                    'username': u['username'],
                    'url': f"https://onlyfans.com/{u['username']}",
                    'price': u['current_price'],
                    'lists': u['lists']
                }
                for u in free_users
            ]
            self._save_free_accounts_to_log(free_accounts_log)
        else:
            print("\n" + "="*70)
            print("No free accounts found!")
            print("="*70)

    def _save_free_accounts_to_log(self, accounts: List[Dict], filename: str = "free_accounts.txt"):
        """Save all free accounts to a text file with one URL per line."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / filename

        with open(log_file, 'w') as f:
            for account in accounts:
                f.write(account['url'] + '\n')

        logger.info(f"Free accounts saved to {log_file}")
        print(f"✓ All free accounts saved to: {log_file}")

    def _save_issues_to_log(self, issues: List[Dict], filename: str = "issues_report.json"):
        """Save all issues to a JSON log file without truncation."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / filename
        timestamp = datetime.now().isoformat()

        report = {
            "timestamp": timestamp,
            "total_issues": len(issues),
            "issues": issues
        }

        with open(log_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Issues saved to {log_file}")
        print(f"✓ Full issues report saved to: {log_file}")

    def find_categorization_issues(self):
        """Find users with incorrect list categorization from the most recent scrape."""
        # Only check users from the most recent scrape run
        latest_run_id = self.db.get_latest_scrape_run_id()
        if not latest_run_id:
            return

        users = self.db.get_users_from_scrape_run(latest_run_id)

        issues = []

        for user in users:
            lists_set = set(user['lists'])

            # Paid user not in 'paid' list
            if user['current_price'] > 0 and 'paid' not in lists_set:
                issues.append({
                    'username': user['username'],
                    'url': f"https://onlyfans.com/{user['username']}",
                    'issue': 'not flagged as paid',
                    'price': user['current_price'],
                    'lists': user['lists']
                })

            # Free user not in 'free' list
            if user['current_price'] == 0 and 'free' not in lists_set:
                issues.append({
                    'username': user['username'],
                    'url': f"https://onlyfans.com/{user['username']}",
                    'issue': 'not flagged as free',
                    'price': user['current_price'],
                    'lists': user['lists']
                })

        if issues:
            print("\n" + "="*60)
            print(f"CATEGORIZATION ISSUES ({len(issues)})")
            print("="*60)
            for issue in issues[:15]:  # Show first 15 in console
                lists_str = ', '.join(issue['lists'])
                print(f"{issue['issue']}: https://onlyfans.com/{issue['username']}")
                print(f"  Price: ${issue['price']}, Lists: {lists_str}")
            if len(issues) > 15:
                print(f"... and {len(issues) - 15} more (see logs/issues_report.json for full list)")

            # Save all issues to log file without truncation
            self._save_issues_to_log(issues)

    def find_price_changes_recently(self, days: int = 30):
        """Find users whose prices changed in the last N days."""
        changes = self.db.get_price_changes(days)

        if changes:
            print("\n" + "="*60)
            print(f"PRICE CHANGES (Last {days} Days) - {len(changes)} changes")
            print("="*60)

            for change in changes[:15]:  # Limit to 15
                prev_price = change['prev_price']
                new_price = change['price']
                change_date = change['scraped_at']

                arrow = "↓" if new_price < prev_price else "↑"
                print(f"{arrow} https://onlyfans.com/{change['username']}")
                print(f"  ${prev_price} → ${new_price} on {change_date}")

            if len(changes) > 15:
                print(f"\n... and {len(changes) - 15} more")

    def find_historical_lows(self):
        """Find users currently at their historical low price."""
        lows = self.db.get_historical_low_prices()

        if lows:
            print("\n" + "="*60)
            print(f"HISTORICAL LOW PRICES ({len(lows)})")
            print("="*60)
            print("Users currently at their lowest price ever:")
            print()

            for low in lows[:20]:  # Limit to 20
                print(f"💰 https://onlyfans.com/{low['username']}")
                print(f"   Current: ${low['current_price']} (seen {low['scrape_count']} times)")

            if len(lows) > 20:
                print(f"\n... and {len(lows) - 20} more")

    def find_trending_prices(self):
        """Find users with consistent price decreases (trending cheaper)."""
        cursor = self.db.conn.cursor()

        # Get users with at least 3 price records
        cursor.execute("""
            WITH price_trends AS (
                SELECT
                    username,
                    price,
                    scraped_at,
                    LAG(price, 1) OVER (PARTITION BY username ORDER BY scraped_at) as prev_price,
                    LAG(price, 2) OVER (PARTITION BY username ORDER BY scraped_at) as prev_price_2
                FROM price_history
                WHERE scraped_at >= datetime('now', '-60 days')
            )
            SELECT username, prev_price_2, prev_price, price
            FROM price_trends
            WHERE prev_price_2 IS NOT NULL
              AND prev_price < prev_price_2
              AND price < prev_price
            GROUP BY username
            ORDER BY (prev_price_2 - price) DESC
            LIMIT 20
        """)

        trends = [dict(row) for row in cursor.fetchall()]

        if trends:
            print("\n" + "="*60)
            print(f"TRENDING CHEAPER ({len(trends)})")
            print("="*60)
            print("Users with consistently decreasing prices:")
            print()

            for trend in trends:
                print(f"📉 https://onlyfans.com/{trend['username']}")
                print(f"   ${trend['prev_price_2']} → ${trend['prev_price']} → ${trend['price']}")

    def get_user_history(self, username: str):
        """Get price history for a specific user."""
        history = self.db.get_price_history(username)

        if history:
            print(f"\n" + "="*60)
            print(f"PRICE HISTORY: @{username}")
            print("="*60)

            for record in history:
                status = record['subscription_status']
                date = record['scraped_at']
                price = record['price']
                print(f"  {date}: ${price} ({status})")
        else:
            print(f"No history found for @{username}")

    def close(self):
        """Close database connection."""
        self.db.close()
