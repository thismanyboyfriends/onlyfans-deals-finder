import logging
import csv
import time
from pathlib import Path
from datetime import date
from typing import Dict, List

from api_client import OnlyFansAPIClient

logger = logging.getLogger(__name__)

# Output configuration
current_date = date.today().strftime("%Y-%m-%d")
script_dir = Path(__file__).parent
output_dir = script_dir / "output"
output_dir.mkdir(exist_ok=True)
output_file: Path = output_dir / f"output-{current_date}.csv"


class ListFetcher:
    """Fetches OnlyFans list data using the API instead of Selenium"""

    def __init__(self, auth_file: Path = None, regenerate_xbc: bool = False):
        """
        Initialize list fetcher

        Args:
            auth_file: Path to auth.json file
            regenerate_xbc: If True, regenerate x-bc token dynamically
        """
        self.api_client = OnlyFansAPIClient(auth_file=auth_file, regenerate_xbc=regenerate_xbc)
        self.seen_users = set()

    def fetch_list(self, list_id: int) -> Path:
        """
        Fetch all users in a list and write to CSV

        Args:
            list_id: OnlyFans list ID

        Returns:
            Path to output CSV file
        """
        logger.info(f"Fetching list {list_id}...")

        all_users = []
        offset = 0
        has_more = True

        # Fetch all users in list with pagination
        while has_more:
            try:
                response = self.api_client.get_list_users(
                    list_id=list_id,
                    offset=offset,
                    limit=100
                )

                users = response.get('list', [])
                all_users.extend(users)

                has_more = response.get('hasMore', False)
                offset += 100

                logger.info(f"Fetched {len(all_users)} users from list...")

                # Rate limiting
                if has_more:
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error fetching list at offset {offset}: {e}")
                break

        logger.info(f"Total users in list: {len(all_users)}")

        # Fetch full profile data for each user and write to CSV
        self._write_users_to_csv(all_users)

        return output_file

    def _write_users_to_csv(self, users: List[Dict]):
        """
        Write user data to CSV file

        Args:
            users: List of user objects from API
        """
        # Clear output file if starting fresh
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['username', 'price', 'subscription_status', 'lists']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        # Process each user
        for i, user in enumerate(users, 1):
            username = user.get('username')

            if not username or username in self.seen_users:
                continue

            self.seen_users.add(username)

            try:
                # Get full profile data with pricing
                logger.debug(f"Fetching profile for {username} ({i}/{len(users)})")
                profile = self.api_client.get_user_profile(username)

                # Extract data
                user_data = self._extract_user_data(profile)

                # Write to CSV
                with open(output_file, 'a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow(user_data)
                    csvfile.flush()

                logger.info(f"Scraped {username} ({i}/{len(users)})")

                # Rate limiting
                time.sleep(0.3)

            except Exception as e:
                logger.warning(f"Failed to fetch profile for {username}: {e}")
                continue

    def _extract_user_data(self, profile: Dict) -> Dict[str, str]:
        """
        Extract relevant data from user profile

        Args:
            profile: User profile data from API

        Returns:
            Dictionary with username, price, subscription_status, lists
        """
        username = profile.get('username', 'unknown')

        # Get price (prefer current price if available)
        current_price = profile.get('currentSubscribePrice')
        regular_price = profile.get('subscribePrice')

        if current_price is not None:
            price = str(current_price)
        elif regular_price is not None:
            price = str(regular_price)
        else:
            price = "0"

        # Get subscription status
        subscribed_data = profile.get('subscribedByData')

        if subscribed_data:
            status = subscribed_data.get('status', 'UNKNOWN')
            if status == 'Active':
                subscription_status = 'SUBSCRIBED'
            elif status in ('Set to Expire', 'Expired'):
                subscription_status = 'NO_SUBSCRIPTION'
            else:
                subscription_status = 'UNKNOWN'
        else:
            subscription_status = 'NO_SUBSCRIPTION'

        # Get lists (for now, empty - would need separate API call to get list names)
        # This matches the original Selenium scraper behavior
        lists = []

        return {
            'username': username,
            'price': price,
            'subscription_status': subscription_status,
            'lists': lists
        }

    def fetch_all_subscriptions(self, subscription_type: str = 'all') -> Path:
        """
        Fetch all subscriptions (active and/or expired) and write to CSV

        Args:
            subscription_type: 'active', 'expired', or 'all'

        Returns:
            Path to output CSV file
        """
        logger.info(f"Fetching {subscription_type} subscriptions...")

        all_users = self.api_client.get_all_subscriptions(subscription_type)

        logger.info(f"Total subscriptions: {len(all_users)}")

        # Write to CSV (users already have full profile data from subscriptions endpoint)
        self._write_subscription_users_to_csv(all_users)

        return output_file

    def _write_subscription_users_to_csv(self, users: List[Dict]):
        """
        Write subscription user data directly to CSV (no need to fetch profiles)

        Args:
            users: List of user objects from subscriptions API
        """
        fieldnames = ['username', 'price', 'subscription_status', 'lists']

        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for user in users:
                username = user.get('username')

                if not username or username in self.seen_users:
                    continue

                self.seen_users.add(username)

                # Extract data (users from subscriptions endpoint have all needed fields)
                user_data = self._extract_user_data(user)

                writer.writerow(user_data)
                csvfile.flush()

                logger.info(f"Added {username}")

    def close(self):
        """Cleanup resources (for compatibility with old scraper interface)"""
        # API client doesn't need cleanup, but keep method for interface compatibility
        pass
