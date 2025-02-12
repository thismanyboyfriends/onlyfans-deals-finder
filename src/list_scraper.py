import logging
import time
from collections import defaultdict
from typing import Optional, Dict, List

import csv
import os
from pathlib import Path
from datetime import date

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

current_date = date.today().strftime("%Y-%m-%d")
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
output_file: Path = script_dir / "output" / f"output-{current_date}.csv"


class PriceNotFoundError(Exception):
    pass


class OnlyFansScraper:
    def __init__(self):
        self.driver = self._setup_driver()
        self.seen_users = defaultdict(bool)

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

    def scrape_list(self, list_id):
        url = BASE_URL.format(list_id)
        self.driver.get(url)
        self.wait_until_page_loads()

        while True:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.scroll_to_bottom()
            time.sleep(4)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break

            old_size = len(self.seen_users)
            user_elements = self.get_user_elements()
            self.write_to_csv(user_elements)
            new_size = len(self.seen_users)

            logging.info(f"Scraped {len(self.seen_users)} users")

            if new_size == old_size:
                break

    def write_to_csv(self, user_elements):
        # Open the file in append mode ('a') instead of write mode ('w')
        with open(output_file, 'a', newline='') as csvfile:
            fieldnames = ['username', 'price', 'subscription_status', 'lists']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header only if the file is empty
            if csvfile.tell() == 0:
                writer.writeheader()

            for user_element in user_elements:
                user_info = self.scrape_info(user_element)
                if user_info and not self.seen_users[user_info['username']]:
                    writer.writerow(user_info)
                    csvfile.flush()  # Force write to disk
                    self.seen_users[user_info['username']] = True
                    logging.info(f"Scraped {user_info['username']}")

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

            offer = self.get_offer(price_element_text)
            price = self.get_price(price_element_text, offer)
            subscription_status: str = self.get_subscription_status(price_element_text)
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
            "subscription_status": "?"
        }

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    @staticmethod
    def get_username(user_element: WebElement) -> str:
        username = user_element.find_element(By.CSS_SELECTOR, USERNAME_SELECTOR).text
        return username[1:]  # trim @ off

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

    def get_subscription_status(self, price_element_text) -> str:
        split: str = price_element_text.split()[0]
        if split == "SUBSCRIBE":
            return "NO_SUBSCRIPTION"
        elif split == "SUBSCRIBED" or split == "RENEW":
            return "SUBSCRIBED"
        else:
            return "INVALID"
