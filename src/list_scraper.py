import logging
import time
import re
from collections import defaultdict
from typing import Optional, Dict, List
from pathlib import Path

from price_parser import Price
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from database import Database

# Constants
BASE_URL = "https://onlyfans.com/my/collections/user-lists/{}"
PROFILE_LIST_SELECTOR = "span.b-list-titles__item__text"
USER_ITEM_SELECTOR = "div.b-users__item"
USERNAME_SELECTOR = "div.g-user-username"
PRICE_SELECTOR = ".b-wrap-btn-text"
AVATAR_SELECTOR = "a.g-avatar img"
DISPLAY_NAME_SELECTOR = "div.g-user-name"
LIST_SELECTOR = "span.b-list-titles__item__text"


CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUGGING_PORT = "9222"
USER_DATA_DIR = r"C:\tempchromdir"
import subprocess

class PriceNotFoundError(Exception):
    pass

def start_chrome():
    command = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUGGING_PORT}",
        f"--user-data-dir={USER_DATA_DIR}"
    ]

    subprocess.Popen(command)
    time.sleep(3)  # Wait for Chrome to start


class OnlyFansScraper:
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize scraper.

        Args:
            db_path: Path to database file (optional, defaults to data/scraper.db)
        """
        start_chrome()
        self.driver = self._setup_driver()
        self.seen_users = defaultdict(bool)
        self.db = Database(db_path)
        self.current_run_id = None

    @staticmethod
    def _setup_driver():
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("incognito")
        options.add_argument("disable-extensions")
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        return webdriver.Chrome(options=options)

    def get_user_elements(self) -> List[WebElement]:
        return self.driver.find_elements(By.CSS_SELECTOR, USER_ITEM_SELECTOR)

    def get_new_user_elements(self) -> List[WebElement]:
        """Get only user elements we haven't seen before (optimization for Vue virtual scrolling)"""
        all_elements = self.driver.find_elements(By.CSS_SELECTOR, USER_ITEM_SELECTOR)
        new_elements = []

        for elem in all_elements:
            try:
                # Quick check - has this element been processed?
                username_elem = elem.find_element(By.CSS_SELECTOR, USERNAME_SELECTOR)
                username = username_elem.text.strip()

                if username:
                    # Remove @ if present
                    username = username[1:] if username.startswith('@') else username

                    if username and not self.seen_users.get(username):
                        new_elements.append(elem)
            except (NoSuchElementException, StaleElementReferenceException):
                # Element might be stale from Vue re-rendering, skip it
                continue

        return new_elements

    def scrape_list(self, list_id) -> Path:
        url = BASE_URL.format(list_id)
        self.driver.get(url)
        self.wait_until_page_loads()

        # Initialize database scrape run
        self.current_run_id = self.db.start_scrape_run(list_id)
        logging.info(f"Started scrape run #{self.current_run_id} for list {list_id}")

        # Wait for Vue virtual scroller to initialize
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".vue-recycle-scroller.ready"))
            )
            logging.info("Vue scroller initialized")
        except TimeoutException:
            logging.warning("Vue scroller not found, continuing anyway...")

        no_new_items_count = 0
        max_failures = 3  # 3 consecutive failures = end of list

        while no_new_items_count < max_failures:
            # Check for page errors
            if self.check_for_page_errors():
                logging.error("Page error couldn't be resolved, stopping scrape")
                self.db.complete_scrape_run(self.current_run_id, len(self.seen_users), 'error')
                break

            old_user_count = len(self.seen_users)

            # Scroll to bottom to trigger Vue to load more items
            self.scroll_to_bottom()

            # Wait for Vue to render new items
            self.wait_for_vue_items_to_render()

            # Scrape only NEW visible items (optimization)
            new_elements = self.get_new_user_elements()
            if new_elements:
                self.write_to_database(new_elements)

                new_user_count = len(self.seen_users)
                newly_added = new_user_count - old_user_count
                logging.info(f"Scraped {newly_added} new users ({new_user_count} total)")
                no_new_items_count = 0  # Reset failure counter
            else:
                no_new_items_count += 1
                logging.info(f"No new users loaded (attempt {no_new_items_count}/{max_failures})")

            # Brief rate limiting between scrolls
            time.sleep(1)

        # Complete the scrape
        logging.info(f"Scraping complete. Total users: {len(self.seen_users)}")
        self.db.complete_scrape_run(self.current_run_id, len(self.seen_users), 'completed')
        return self.db.db_path

    def write_to_database(self, user_elements):
        """Write user data to SQLite database with batch processing"""
        new_users = []

        # Collect all new user data first
        for user_element in user_elements:
            user_info = self.scrape_info(user_element)
            if user_info and not self.seen_users.get(user_info['username']):
                new_users.append(user_info)
                self.seen_users[user_info['username']] = True

        # Batch write to database
        for user in new_users:
            try:
                # Convert price string to float
                try:
                    price_float = float(user['price']) if user['price'] != '?' else 0.0
                except ValueError:
                    price_float = 0.0

                self.db.upsert_user(
                    username=user['username'],
                    price=price_float,
                    subscription_status=user['subscription_status'],
                    lists=user['lists'],
                    run_id=self.current_run_id
                )
                logging.info(f"Scraped {user['username']}")
            except Exception as e:
                logging.error(f"Failed to save {user['username']} to database: {e}")

    def scrape_info(self, user_element: WebElement) -> Optional[Dict]:

        username: str = ""

        try:
            username: str = self.get_username(user_element)

            if username is None or username == "":
                return None

            price_element_text: str = self.get_price_text(user_element)
            lists_text: List[str] = self.get_lists(user_element)

            if not price_element_text:
                return self.unknown_user_info(username)

            try:
                offer = self.get_offer(price_element_text)
                price = self.get_price(price_element_text, offer)
                subscription_status: str = self.get_subscription_status(price_element_text)
            except (PriceNotFoundError, IndexError) as e:
                logging.warning(f"Price parsing failed for user {username}: {str(e)}")
                logging.warning(f"  Raw price text was: '{price_element_text}'")
                return self.unknown_user_info(username)
            return {
                "username": username,
                "subscription_status": subscription_status,
                "price": price,
                "lists": lists_text
            }
        except NoSuchElementException as e:
            logging.warning(f"Failed to scrape info for user {username}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error while scraping user {username}: {str(e)}")
            return None

    @staticmethod
    def unknown_user_info(username: str) -> Dict[str, str]:
        return {
            "username": username,
            "price": "?",
            "subscription_status": "?",
            "lists": []
        }

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    @staticmethod
    def get_username(user_element: WebElement) -> str:
        """Get username with fallback selectors for robustness"""
        selectors = [
            "div.g-user-username",
            "div.b-username-row div.g-user-username",
            "a[href*='onlyfans.com/'] div.g-user-username"
        ]

        for selector in selectors:
            try:
                elem = user_element.find_element(By.CSS_SELECTOR, selector)
                username = elem.text.strip()
                if username:
                    # Remove @ if present
                    return username[1:] if username.startswith('@') else username
            except NoSuchElementException:
                continue

        raise NoSuchElementException("Could not find username with any selector")

    @staticmethod
    def get_price_text(user_element: WebElement) -> str:
        try:
            elem = user_element.find_element(By.CSS_SELECTOR, PRICE_SELECTOR)
            # Get all text including nested spans (like g-btn__new-line-text)
            text = elem.get_attribute('textContent') or elem.text
            # Normalize whitespace (remove newlines and extra spaces)
            return ' '.join(text.split())
        except NoSuchElementException:
            return ""

    def get_avatar_url(self) -> str:
        return self.driver.find_element(By.CSS_SELECTOR, AVATAR_SELECTOR).get_property("src")

    def get_display_name(self) -> str:
        elements = self.driver.find_elements(By.CSS_SELECTOR, DISPLAY_NAME_SELECTOR)
        if len(elements) > 1:
            return elements[1].text
        elif len(elements) == 1:
            return elements[0].text
        return ""

    def wait_until_page_loads(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, USER_ITEM_SELECTOR))
            )
        except TimeoutException:
            logging.error("Timeout waiting for page to load")

    def wait_for_vue_items_to_render(self, timeout=10) -> bool:
        """Wait for Vue virtual scroller to render new items after scroll"""
        try:
            # Wait for Vue scroller to be present and ready
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".vue-recycle-scroller__item-wrapper"))
            )
            # Brief pause for Vue to finish rendering items
            time.sleep(0.5)
            return True
        except TimeoutException:
            logging.warning("Timeout waiting for Vue items to render")
            return False

    def check_for_page_errors(self) -> bool:
        """Check if page shows error state and try to recover"""
        try:
            # Look for the error message
            error_elem = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Opps, something went wrong')]")

            # Only treat as error if the element is actually visible to the user
            if error_elem and error_elem.is_displayed():
                logging.error("Page showed error: 'Opps, something went wrong'")
                # Try clicking retry button
                try:
                    retry_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-try-infinite")

                    # Check if button is actually clickable
                    if retry_btn.is_displayed() and retry_btn.is_enabled():
                        # Scroll to button to ensure it's in view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", retry_btn)
                        time.sleep(0.5)
                        retry_btn.click()
                        logging.info("Clicked retry button, waiting for recovery...")
                        time.sleep(2)
                        return False  # Error handled
                    else:
                        logging.error("Retry button found but not clickable")
                        return True  # Error couldn't be fixed

                except (NoSuchElementException, ElementNotInteractableException) as e:
                    logging.error(f"Could not interact with retry button: {str(e)}")
                    return True  # Error couldn't be fixed
            else:
                # Error element exists in DOM but is hidden - not a real error
                return False
        except NoSuchElementException:
            return False  # No error

    @staticmethod
    def get_lists(user_element: WebElement) -> List[str]:
        lists_elements = user_element.find_elements(By.CSS_SELECTOR, LIST_SELECTOR)
        lists: List[str] = [element.text for element in lists_elements if element.text != "Lists"]
        lists.sort()
        return lists

    @staticmethod
    def get_price(price_text: str, offer: str) -> str:
        if offer in ("FREE", "FREE_TRIAL", "SUBSCRIBED"):
            price = "$0"
        elif offer == "NO_OFFER":
            parts = price_text.split()
            if len(parts) < 2:
                raise PriceNotFoundError(f"Unexpected NO_OFFER format: '{price_text}' (expected at least 2 parts)")
            price = parts[1]
        elif offer == "OFFER":
            parts = price_text.split()
            if len(parts) < 4:
                raise PriceNotFoundError(f"Unexpected OFFER format: '{price_text}' (expected at least 4 parts)")
            price = parts[-4]
        else:
            raise PriceNotFoundError(f"Unable to determine price for unknown offer type: '{offer}'")

        return OnlyFansScraper.standardize_price(price)

    @staticmethod
    def get_offer(price_text: str) -> str:
        # Make matching case-insensitive for robustness
        price_upper = price_text.upper()

        if "RENEW" in price_upper or "SUBSCRIBED" in price_upper:
            return "SUBSCRIBED"
        elif "FREE FOR" in price_upper:
            return "FREE_TRIAL"
        # Match patterns like "20% off for 30 days" but NOT "FREE for 30 days"
        elif re.search(r'\b\d+\s*days?\b', price_upper, re.IGNORECASE) and "FREE" not in price_upper:
            return "OFFER"
        elif "FOR FREE" in price_upper:
            return "FREE"
        elif "PER MONTH" in price_upper:
            return "NO_OFFER"
        else:
            raise PriceNotFoundError(f"Unable to determine offer type from: '{price_text}'")

    def close_driver(self) -> None:
        """Close browser and database connections."""
        self.driver.quit()
        if self.db:
            self.db.close()

    @staticmethod
    def standardize_price(price_string: str) -> str:
        parsed_price = Price.fromstring(price_string)
        if parsed_price.amount is None:
            raise PriceNotFoundError(f"Could not parse price from: '{price_string}'")
        return str(parsed_price.amount)

    @staticmethod
    def get_subscription_status(price_element_text) -> str:
        parts = price_element_text.split()
        if len(parts) == 0:
            logging.warning(f"Empty price text when determining subscription status")
            return "INVALID"

        # Make case-insensitive
        text_upper = price_element_text.upper()
        first_word = parts[0].upper()
        if first_word == "SUBSCRIBE":
            return "NO_SUBSCRIPTION"
        elif first_word == "SUBSCRIBED" or first_word == "RENEW" or "SUBSCRIBEDFOR" in text_upper:
            return "SUBSCRIBED"
        else:
            logging.warning(f"Unknown subscription status keyword: '{parts[0]}' in text: '{price_element_text}'")
            return "INVALID"
