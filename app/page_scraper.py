from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("incognito")
options.add_argument("headless")
options.add_argument("disable-extensions")
options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
# driver = uc.Chrome(options=options)
driver = webdriver.Chrome(options=options)

BASE_URL = "https://onlyfans.com/{}"

PROFILE_DISPLAY_NAME_SELECTOR = "g-user-name"
PROFILE_BIO_SELECTOR = "div.b-user-info__text"
PROFILE_SUBSCRIBED_SELECTOR = ""
PROFILE_PRICE_SELECTOR = "div.b-offer-join"
PROFILE_LIST_SELECTOR = "span.b-list-titles__item__text"
PROFILE_PIC_SELECTOR = "a.g-avatar img"


class PriceNotFoundError:
    pass


def scrape_page(of_username: str) -> dict[str, str]:
    url = BASE_URL.format(of_username)
    driver.get(url)

    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, PROFILE_DISPLAY_NAME_SELECTOR))
    )

    display_name = element.text
    bio = driver.find_element(By.CSS_SELECTOR, PROFILE_BIO_SELECTOR).text

    price_element = get_price_element()

    offer = get_offer(price_element.text)
    price = get_price(price_element.text, offer)
    subscribed = get_subscribed(price_element.text)
    avatar = driver.find_element(By.CSS_SELECTOR, PROFILE_PIC_SELECTOR)

    user_info = {
        "url": url,
        "username": of_username,
        "display_name": display_name,
        "subscribed": subscribed,
        "price": price,
        "offer": offer,
        "avatar_url": avatar.get_property("src"),
    }

    return user_info


def get_price_element() -> WebElement:
    elements = driver.find_elements(By.CSS_SELECTOR, PROFILE_PRICE_SELECTOR)
    return next((element for element in elements if "SUBSCRIBE" in element.text), None)


def get_price(price_text: str, offer: str) -> str:

    if offer == "FREE" or offer == "FREE_TRIAL":
        return "0"
    elif offer == "NO_OFFER":
        return price_text.split()[1]
    elif offer == "OFFER":
        return price_text.split()[-2]
    else:
        raise PriceNotFoundError


def get_offer(price_text: str) -> str:
    if "FREE for" in price_text:
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
