import random
import time

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from price_parser import Price

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("incognito")
# options.add_argument("headless")
options.add_argument("disable-extensions")
options.add_experimental_option("debuggerAddress", "localhost:9222")
# options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
# driver = uc.Chrome(options=options)
driver = webdriver.Chrome(options=options)

BASE_URL = "https://onlyfans.com/{}"

PROFILE_LIST_SELECTOR = "span.b-list-titles__item__text"


class PriceNotFoundError(Exception):
    pass


class PageNotAvailableError(Exception):
    pass





def scrape_page(of_username: str) -> dict[str, str]:
    url = BASE_URL.format(of_username)
    driver.get(url)

    wait_until_page_loads()
    throw_error_if_404()

    price_element_text: str = get_price_element_text()
    bio = driver.find_element(By.CSS_SELECTOR, "div.b-user-info__text").text
    offer = get_offer(price_element_text)
    price = get_price(price_element_text, offer)
    avatar_url = get_avatar_url()
    lists = get_lists()

    user_info = {
        "url": url,
        "username": of_username,
        "display_name": get_display_name(),
        "price": price,
        "offer": offer,
        "lists": " ".join(lists),
        "avatar_url": avatar_url,
    }

    return user_info


def get_avatar_url():
    return driver.find_element(By.CSS_SELECTOR, "a.g-avatar img").get_property("src")


def get_display_name():
    return driver.find_elements(By.CSS_SELECTOR, "div.g-user-name")[1].text


def unpredictable_wait():
    random_wait = random.uniform(1, 5)
    time.sleep(random_wait)


def wait_until_page_loads():
    unpredictable_wait()

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.g-avatar__img-wrapper"))
    )


def throw_error_if_404():
    not_found_elements = driver.find_elements(By.CSS_SELECTOR, "div.b-404")

    if len(not_found_elements) > 0:
        raise PageNotAvailableError

    return


def get_price_element_text() -> str:
    return driver.find_elements(By.CSS_SELECTOR, "div.b-offer-wrapper")[0].find_element(By.CSS_SELECTOR, "div.m-rounded").text


def get_lists() -> list[str]:
    lists_elements = driver.find_elements(By.CSS_SELECTOR, "span.b-list-titles__item__text")
    return [element.text for element in lists_elements]



def get_price(price_text: str, offer: str) -> str:
    if offer == "FREE" or offer == "FREE_TRIAL" or offer == "SUBSCRIBED":
        price = "$0"
    elif offer == "NO_OFFER":
        price = price_text.split()[1]
    elif offer == "OFFER":
        price = price_text.split()[-2]
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
