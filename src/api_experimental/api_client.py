import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Any
import httpx

from signature import SignatureGenerator

logger = logging.getLogger(__name__)


class OnlyFansAPIClient:
    """Client for interacting with the OnlyFans API"""

    BASE_URL = "https://onlyfans.com/api2/v2"

    def __init__(self, auth_file: Path = None, regenerate_xbc: bool = False):
        """
        Initialize API client

        Args:
            auth_file: Path to auth.json file containing credentials
            regenerate_xbc: If True, regenerate x-bc token dynamically
        """
        if auth_file is None:
            # Try config/auth.json first, fallback to src/auth.json
            config_auth = Path(__file__).parent.parent / "config" / "auth.json"
            src_auth = Path(__file__).parent / "auth.json"

            if config_auth.exists():
                auth_file = config_auth
            elif src_auth.exists():
                auth_file = src_auth
                logger.warning(f"Using auth.json from src/ folder. Consider moving to config/ folder for better security.")
            else:
                # Default to config location
                auth_file = config_auth

        self.auth_file = auth_file
        self.regenerate_xbc = regenerate_xbc
        self.auth_data = self._load_auth()
        self.signature_gen = SignatureGenerator()
        self.session = self._create_session()

        # Regenerate x-bc if requested
        if self.regenerate_xbc:
            old_xbc = self.auth_data['x-bc']
            self.auth_data['x-bc'] = self.signature_gen.generate_x_bc(self.auth_data['user_agent'])
            logger.debug(f"Regenerated x-bc token: {old_xbc} -> {self.auth_data['x-bc']}")

    def _load_auth(self) -> Dict[str, str]:
        """Load authentication data from auth.json"""
        if not self.auth_file.exists():
            raise FileNotFoundError(
                f"Auth file not found: {self.auth_file}\n"
                f"Please create auth.json with your OnlyFans credentials.\n"
                f"See auth.json.template for format."
            )

        with open(self.auth_file, 'r') as f:
            auth_data = json.load(f)

        # Validate required fields
        required_fields = ['auth_id', 'sess', 'user_agent', 'x-bc']
        missing_fields = [f for f in required_fields if f not in auth_data]

        if missing_fields:
            raise ValueError(
                f"Missing required auth fields: {', '.join(missing_fields)}\n"
                f"Please check your auth.json file."
            )

        # Clean up user_agent - remove any escaped quotes
        if auth_data['user_agent'].startswith('"') or auth_data['user_agent'].startswith('\\"'):
            auth_data['user_agent'] = auth_data['user_agent'].strip('"').strip('\\"')
            logger.warning("Cleaned up user_agent field (removed quotes)")

        logger.info(f"Loaded authentication for user ID: {auth_data['auth_id']}")
        return auth_data

    def _create_session(self) -> httpx.Client:
        """Create HTTP session with retry logic and HTTP/2 support"""
        # Use httpx with HTTP/2 support like OF-Scraper
        session = httpx.Client(
            http2=True,
            limits=httpx.Limits(
                max_connections=12,
                max_keepalive_connections=12
            ),
            timeout=httpx.Timeout(30.0),
            follow_redirects=True
        )

        return session

    def _get_headers(self, path: str) -> Dict[str, str]:
        """
        Generate headers for authenticated API request

        Args:
            path: Request path with query string

        Returns:
            Dictionary of HTTP headers
        """
        # Generate signature
        signature, timestamp = self.signature_gen.create_signature(
            path=path,
            auth_id=self.auth_data['auth_id']
        )

        # Build headers matching OF-Scraper exactly
        headers = {
            'accept': 'application/json, text/plain, */*',
            'app-token': '33d57ade8c02dbc5a333db99ff9ae26a',  # OF-Scraper uses static value
            'user-id': self.auth_data['auth_id'],
            'x-bc': self.auth_data['x-bc'],
            'referer': 'https://onlyfans.com',
            'user-agent': self.auth_data['user_agent'],
            'sign': signature,
            'time': timestamp
        }

        logger.debug(f"Request headers prepared for {path}")
        return headers

    def _get_cookies(self) -> Dict[str, str]:
        """
        Get cookies as dictionary (not as cookie header string)

        Returns:
            Dictionary of cookies
        """
        auth_id = self.auth_data['auth_id']

        cookies = {
            'sess': self.auth_data['sess'],
            'auth_id': auth_id,
            'auth_uid_': self.auth_data.get('auth_uid', auth_id)
        }

        logger.debug(f"Cookies prepared: auth_id={auth_id}")
        return cookies

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GET request to OnlyFans API

        Args:
            endpoint: API endpoint (e.g., /lists/123/users)
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            requests.HTTPError: If request fails
        """
        # Build full URL
        url = f"{self.BASE_URL}{endpoint}"

        # Build path with query string for signature
        if params:
            query_string = '&'.join(f"{k}={v}" for k, v in params.items())
            path = f"{endpoint}?{query_string}"
        else:
            path = endpoint

        # Get headers with signature
        headers = self._get_headers(path)

        # Get cookies
        cookies = self._get_cookies()

        # Make request
        logger.debug(f"GET {url} with params: {params}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Cookies: {cookies}")

        try:
            response = self.session.get(url, headers=headers, cookies=cookies, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed (401). Please refresh your auth.json credentials.")
            elif e.response.status_code == 403:
                logger.error("Forbidden (403). Signing rules may need refresh.")
            elif e.response.status_code == 429:
                logger.warning("Rate limited (429). Retrying with backoff...")
                time.sleep(10)
            elif e.response.status_code == 400:
                logger.error(f"Bad Request (400). Response body: {e.response.text}")
            else:
                logger.error(f"HTTP Error {e.response.status_code}. Response: {e.response.text}")
            raise

        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_user_profile(self, username_or_id: str) -> Dict[str, Any]:
        """
        Get user profile by username or ID

        Args:
            username_or_id: Username or user ID

        Returns:
            User profile data
        """
        return self.get(f"/users/{username_or_id}")

    def get_lists(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get user's custom lists

        Args:
            offset: Pagination offset
            limit: Results per page

        Returns:
            Lists data with pagination
        """
        params = {
            'offset': offset,
            'skip_users': 'all',
            'limit': limit,
            'format': 'infinite'
        }
        return self.get("/lists", params=params)

    def get_list_users(self, list_id: int, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        Get users in a specific list

        Args:
            list_id: List ID
            offset: Pagination offset
            limit: Results per page

        Returns:
            User data with pagination
        """
        params = {
            'offset': offset,
            'limit': limit,
            'format': 'infinite'
        }
        return self.get(f"/lists/{list_id}/users", params=params)

    def get_active_subscriptions(self, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """
        Get active subscriptions

        Args:
            offset: Pagination offset
            limit: Results per page (max 10)

        Returns:
            Subscription data with pagination
        """
        params = {
            'offset': offset,
            'limit': min(limit, 10),  # API max is 10
            'type': 'active',
            'format': 'infinite'
        }
        return self.get("/subscriptions/subscribes", params=params)

    def get_expired_subscriptions(self, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """
        Get expired subscriptions

        Args:
            offset: Pagination offset
            limit: Results per page (max 10)

        Returns:
            Subscription data with pagination
        """
        params = {
            'offset': offset,
            'limit': min(limit, 10),
            'type': 'expired',
            'format': 'infinite'
        }
        return self.get("/subscriptions/subscribes", params=params)

    def get_all_subscriptions(self, subscription_type: str = 'active') -> list[Dict[str, Any]]:
        """
        Get all subscriptions (handles pagination automatically)

        Args:
            subscription_type: 'active', 'expired', or 'all'

        Returns:
            List of all subscription user objects
        """
        all_users = []
        offset = 0
        has_more = True

        while has_more:
            if subscription_type == 'active':
                response = self.get_active_subscriptions(offset=offset)
            elif subscription_type == 'expired':
                response = self.get_expired_subscriptions(offset=offset)
            else:
                # Get both active and expired
                active = self.get_all_subscriptions('active')
                expired = self.get_all_subscriptions('expired')
                return active + expired

            users = response.get('list', [])
            all_users.extend(users)

            has_more = response.get('hasMore', False)
            offset += 10

            logger.info(f"Fetched {len(all_users)} {subscription_type} subscriptions...")

            # Rate limiting
            if has_more:
                time.sleep(0.5)

        logger.info(f"Total {subscription_type} subscriptions: {len(all_users)}")
        return all_users
