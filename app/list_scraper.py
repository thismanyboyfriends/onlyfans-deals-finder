import logging
import time
from typing import Optional, Dict, List

from price_parser import Price
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Constants
BASE_URL = "https://onlyfans.com/my/collections/user-lists/{}"
PROFILE_LIST_SELECTOR = "span.b-list-titles__item__text"
USER_ITEM_SELECTOR = "div.b-users__item"
USERNAME_SELECTOR = "div.g-user-username"
PRICE_SELECTOR = ".b-wrap-btn-text"
AVATAR_SELECTOR = "a.g-avatar img"
DISPLAY_NAME_SELECTOR = "div.g-user-name"
LIST_SELECTOR = "span.b-list-titles__item__text"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PriceNotFoundError(Exception):
    pass


class OnlyFansScraper:
    def __init__(self):
        self.driver = self._setup_driver()

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

    def scrape_user_info(self) -> Dict[str, Dict]:
        user_elements = self.get_user_elements()
        user_info_dict: Dict[str, Dict] = {}

        for user_element in user_elements:
            if user_element.text:
                user_info = self.scrape_info(user_element)
                if user_info and (username := user_info.get("username")):
                    logging.info(f"Scraped user {username}")
                    logging.info(f"Details: {user_info}")
                    user_info_dict[username] = user_info

        return user_info_dict

    def scrape_list(self, list_id: int) -> Dict[str, Dict[str, str]]:
        url = BASE_URL.format(list_id)
        self.driver.get(url)
        self.wait_until_page_loads()
        user_info_dict: Dict[str, Dict] = {}

        while True:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.scroll_to_bottom()
            time.sleep(4)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break

            old_size = len(user_info_dict)
            user_info_dict.update(self.scrape_user_info())
            new_size = len(user_info_dict)
            logging.info(f"Scraped {new_size} users")

            if old_size == new_size:
                break

        return user_info_dict

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scrape_info(self, user_element: WebElement) -> Optional[Dict]:
        try:
            username: str = user_element.find_element(By.CSS_SELECTOR, USERNAME_SELECTOR).text
            price_element_text: str = self.get_price_text(user_element)
            lists_text: List[str] = self.get_lists(user_element)

            if not price_element_text:
                return self.unknown_user_info(username)

            split = price_element_text.split("\n")
            return {
                "username": username,
                "subscription_status": split[0],
                "price": split[1] if len(split) > 1 else "?",
                "lists": lists_text
            }
        except NoSuchElementException:
            logging.warning(f"Failed to scrape info for a user element")
            return None

    @staticmethod
    def unknown_user_info(username: str) -> Dict[str, str]:
        return {
            "username": username,
            "price": "?",
            "subscription_status": "?"
        }

    @staticmethod
    def get_price_text(user_element: WebElement) -> str:
        try:
            return user_element.find_element(By.CSS_SELECTOR, PRICE_SELECTOR).text
        except NoSuchElementException:
            return ""

    def get_avatar_url(self) -> str:
        return self.driver.find_element(By.CSS_SELECTOR, AVATAR_SELECTOR).get_property("src")

    def get_display_name(self) -> str:
        return self.driver.find_elements(By.CSS_SELECTOR, DISPLAY_NAME_SELECTOR)[1].text

    def wait_until_page_loads(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, USER_ITEM_SELECTOR))
            )
        except TimeoutException:
            logging.error("Timeout waiting for page to load")

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
            price = price_text.split()[1]
        elif offer == "OFFER":
            price = price_text.split()[-4]
        else:
            raise PriceNotFoundError("Unable to determine price")

        return OnlyFansScraper.standardize_price(price)

    @staticmethod
    def get_offer(price_text: str) -> str:
        if "RENEW" in price_text or "SUBSCRIBED" in price_text:
            return "SUBSCRIBED"
        elif "FREE for" in price_text:
            return "FREE_TRIAL"
        elif "days" in price_text:
            return "OFFER"
        elif "FOR FREE" in price_text:
            return "FREE"
        elif "per month" in price_text:
            return "NO_OFFER"
        else:
            raise PriceNotFoundError("Unable to determine offer type")

    def close_driver(self) -> None:
        self.driver.quit()

    @staticmethod
    def standardize_price(price_string: str) -> str:
        parsed_price = Price.fromstring(price_string)
        return str(parsed_price.amount)
