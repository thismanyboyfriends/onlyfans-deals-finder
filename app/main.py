import logging
import os
import enlighten
from selenium.common import TimeoutException

import page_scraper
from pathlib import Path

from app import output

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
account_list: Path = script_dir / "input" / "account_list.txt"

MAX_PROFILE_LIMIT = 1000

def main() -> None:
    logger.info("===== OF_INFO_SCRAPER =====")

    of_profile_names: list[str] = read_file_to_list(account_list)
    logger.info(f"Found {len(of_profile_names)} onlyfans profiles")

    manager = enlighten.get_manager()
    pbar = manager.counter(total=(len(of_profile_names)), desc='OnlyFans Profiles', unit='profiles')

    current_profiles_scraped: int = 0
    output.create_output_file()

    for of_profile_name in of_profile_names:

        try:
            page_info = page_scraper.scrape_page(of_profile_name)
        except TimeoutException as e:
            logger.error(f"{of_profile_name}: timed out! Could not scrape page")
            pbar.update()
            continue
        except page_scraper.PageNotAvailableError as e:
            logger.error(f"{of_profile_name}: Not available anymore!")
            pbar.update()
            continue
        except AttributeError:
            logger.error(f"{of_profile_name}: No price info!")

        if page_info["offer"] == "FREE_TRIAL":
            logger.info(f"{of_profile_name}: Found free trial -- {page_info["url"]}")

        logger.info(f"{of_profile_name}: scraped!")

        pbar.update()
        output.add_scraped_info(page_info)
        current_profiles_scraped += 1
        if current_profiles_scraped >= MAX_PROFILE_LIMIT:
            break

    page_scraper.close_driver()

    logger.info(f"Processed {len(of_profile_names)} users!")


def read_file_to_list(filename: Path) -> list[str]:
    with open(filename, 'r') as file:
        return file.read().splitlines()


if __name__ == "__main__":
    main()
