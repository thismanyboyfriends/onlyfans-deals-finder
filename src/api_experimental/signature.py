import hashlib
import time
import base64
import random
import logging
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SignatureGenerator:
    """Generates cryptographic signatures for OnlyFans API requests"""

    # Dynamic rule sources (URLs from OF-Scraper)
    RULE_SOURCES = [
        "https://raw.githubusercontent.com/datawhores/onlyfans-dynamic-rules/main/dynamicRules.json",
        "https://raw.githubusercontent.com/DIGITALCRIMINALS/dynamic-rules/main/onlyfans.json",
    ]

    def __init__(self):
        self.cached_rules: Optional[Dict] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_duration = timedelta(minutes=30)

    def generate_x_bc(self, user_agent: str) -> str:
        """
        Generate x-bc token

        Format: SHA1(base64(timestamp) + "." + base64(random1) + "." + base64(random2) + "." + base64(user_agent))
        """
        timestamp_ms = int(time.time() * 1000)
        random1 = random.randint(0, int(1e12))
        random2 = random.randint(0, int(1e12))

        # Create base64 encoded parts
        parts = [
            base64.b64encode(str(timestamp_ms).encode()).decode(),
            base64.b64encode(str(random1).encode()).decode(),
            base64.b64encode(str(random2).encode()).decode(),
            base64.b64encode(user_agent.encode()).decode()
        ]

        msg = ".".join(parts)
        return hashlib.sha1(msg.encode()).hexdigest()

    def fetch_dynamic_rules(self) -> Dict:
        """Fetch dynamic signing rules from external sources"""
        # Check cache
        if self.cached_rules and self.cache_timestamp:
            if datetime.now() - self.cache_timestamp < self.cache_duration:
                logger.debug("Using cached signing rules")
                return self.cached_rules

        # Try each source
        for source_url in self.RULE_SOURCES:
            try:
                logger.info(f"Fetching signing rules from {source_url}")
                response = requests.get(source_url, timeout=10)
                response.raise_for_status()
                rules = response.json()

                # Cache the rules
                self.cached_rules = rules
                self.cache_timestamp = datetime.now()
                logger.info("Successfully fetched and cached signing rules")

                logger.debug(f"Fetched dynamic rules with prefix={rules.get('prefix')}")
                return rules

            except Exception as e:
                logger.warning(f"Failed to fetch rules from {source_url}: {e}")
                continue

        # Fallback to hardcoded rules (may be outdated)
        logger.warning("All rule sources failed, using fallback rules")
        return self._get_fallback_rules()

    def _get_fallback_rules(self) -> Dict:
        """Fallback signing rules if external sources fail"""
        logger.error("Using fallback rules - these may be outdated!")
        return {
            "static_param": "STATIC_PARAM_PLACEHOLDER",
            "prefix": "00000",
            "suffix": "SUFFIX",
            "checksum_indexes": list(range(32)),
            "checksum_constant": 0
        }

    def create_signature(self, path: str, auth_id: str) -> tuple[str, str]:
        """
        Create request signature

        Args:
            path: Request path with query string (e.g., /lists/123/users?offset=0&limit=100)
            auth_id: User authentication ID

        Returns:
            Tuple of (signature, timestamp)
        """
        rules = self.fetch_dynamic_rules()
        timestamp = str(int(time.time() * 1000))

        # Extract signing parameters
        static_param = rules.get("static_param", "")
        prefix = rules.get("prefix", "")
        suffix = rules.get("suffix", "")
        checksum_indexes = rules.get("checksum_indexes", [])
        checksum_constant = rules.get("checksum_constant", 0)

        # Create message for SHA1
        message = "\n".join([
            static_param,
            timestamp,
            path,
            auth_id
        ])

        # Generate SHA1 hash
        sha1_hash = hashlib.sha1(message.encode(), usedforsecurity=False).hexdigest()

        # Convert hash to ASCII bytes for checksum calculation
        sha1_bytes = sha1_hash.encode('ascii')

        # Calculate checksum from byte values at specific indexes
        checksum = sum(sha1_bytes[i] for i in checksum_indexes if i < len(sha1_bytes))
        checksum += checksum_constant

        # Format final signature: prefix:hash:checksum_in_hex:suffix
        signature = f"{prefix}:{sha1_hash}:{abs(checksum):x}:{suffix}"

        logger.debug(f"Generated signature for {path}: {signature[:20]}...")
        return signature, timestamp
