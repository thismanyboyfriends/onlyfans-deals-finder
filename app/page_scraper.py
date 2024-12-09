from time import sleep

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("incognito")
# options.add_argument("headless")
options.add_argument("disable-extensions")
options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
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

    price_element = get_price_element()
    bio = driver.find_element(By.CSS_SELECTOR, "div.b-user-info__text").text

    user_info = {
        "url": url,
        "username": of_username,
        "display_name": driver.find_element(By.CLASS_NAME, "g-user-name").text,
        "subscribed": (get_subscribed(price_element.text)),
        "price": (get_price(price_element.text, get_offer(price_element.text))),
        "offer": (get_offer(price_element.text)),
        "avatar_url": (driver.find_element(By.CSS_SELECTOR, "a.g-avatar img").get_property("src")),
    }

    return user_info


def wait_until_page_loads():
    sleep(2)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.g-avatar__img-wrapper"))
    )


def throw_error_if_404():
    not_found_elements = driver.find_elements(By.CSS_SELECTOR, "div.b-404")

    if len(not_found_elements) > 0:
        raise PageNotAvailableError

    return

def get_price_element() -> WebElement:
    elements = driver.find_elements(By.CSS_SELECTOR, "div.b-offer-join")
    return next((element for element in elements if "SUBSCRIBE" in element.text), None)


def get_price(price_text: str, offer: str) -> str:
    if offer == "FREE" or offer == "FREE_TRIAL" or offer == "SUBSCRIBED":
        return "0"
    elif offer == "NO_OFFER":
        return price_text.split()[1]
    elif offer == "OFFER":
        return price_text.split()[-2]
    else:
        raise PriceNotFoundError


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


def get_subscribed(price_text: str) -> bool:
    return "subscribed" in price_text


def close_driver() -> None:
    driver.quit()
