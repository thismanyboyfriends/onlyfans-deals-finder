from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()


def scrape_page(of_username: str) -> dict[str, str]:
    driver.get(f"https://onlyfans.com/{of_username}")

    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "g-user-name"))
    )

    user_info = {
        "username": of_username,
        "display_name": str(element.text)
    }

    return user_info


def close_driver():
    driver.quit()
