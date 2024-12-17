import logging
import time
from typing import Optional

from price_parser import Price
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("incognito")
# options.add_argument("headless")
options.add_argument("disable-extensions")
options.add_experimental_option("debuggerAddress", "localhost:9222")
# options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
driver = webdriver.Chrome(options=options)

BASE_URL = "https://onlyfans.com/my/collections/user-lists/{}"

PROFILE_LIST_SELECTOR = "span.b-list-titles__item__text"


def get_user_elements() -> list[WebElement]:
    return driver.find_elements(By.CSS_SELECTOR, "div.b-users__item")


def scrape_user_info() -> dict:
    user_elements = get_user_elements()
    user_info_dict: dict[str, dict] = {}

    for user_element in user_elements:
        user_info = scrape_info(user_element)
        if user_info:
            username = user_info["username"]
            if username:
                logging.info(f"scraped user {username}")
                user_info_dict[username] = user_info

    return user_info_dict


def scrape_list(list_id: int) -> dict[str, dict[str, str]]:
    url = BASE_URL.format(list_id)
    driver.get(url)
    wait_until_page_loads()
    user_info_dict: dict[str, dict] = {}

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:

        scroll_to_bottom()
        time.sleep(4)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break

        old_size = len(user_info_dict)
        user_info_dict |= scrape_user_info()
        new_size = len(user_info_dict)
        logging.info(f"scraped {new_size} users")

        if old_size == new_size:
            break

    return user_info_dict


def scroll_to_bottom():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


def scrape_info(user_element) -> Optional[dict]:
    username: str = user_element.find_element(By.CSS_SELECTOR, "div.g-user-username").text
    price_element_text: str = get_price_text(user_element)

    return {
        "username": username,
        "price": price_element_text
    }


def get_price_text(user_element):
    try:
        return user_element.find_element(By.CSS_SELECTOR, ".b-wrap-btn-text").text
    except NoSuchElementException:
        return "No Price Info"


def get_avatar_url():
    return driver.find_element(By.CSS_SELECTOR, "a.g-avatar img").get_property("src")


def get_display_name():
    return driver.find_elements(By.CSS_SELECTOR, "div.g-user-name")[1].text


def wait_until_page_loads():
    time.sleep(1)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.b-users__item"))
    )


def get_lists() -> list[str]:
    lists_elements = driver.find_elements(By.CSS_SELECTOR, "span.b-list-titles__item__text")
    return [element.text for element in lists_elements]


def get_price(price_text: str, offer: str) -> str:
    if offer == "FREE" or offer == "FREE_TRIAL" or offer == "SUBSCRIBED":
        price = "$0"
    elif offer == "NO_OFFER":
        price = price_text.split()[1]
    elif offer == "OFFER":
        price = price_text.split()[-4]
    else:
        raise PriceNotFoundError

    return standardize_price(price)


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
        raise PriceNotFoundError


def close_driver() -> None:
    driver.quit()


def standardize_price(price_string: str) -> str:
    parsed_price = Price.fromstring(price_string)
    return str(parsed_price.amount)
