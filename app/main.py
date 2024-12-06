import csv
import logging
import os
import enlighten
import page_scraper
from pathlib import Path



logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
account_list: Path = script_dir / "input" / "account_list.txt"
output_file: Path = script_dir / "output" / "output.csv"

MAX_PROFILE_LIMIT = 30
headers = ["username", "display_name"]

def main() -> None:
    logger.info("===== OF_INFO_SCRAPER =====")

    of_profile_names: list[str] = read_file_to_list(account_list)
    logger.info(f"Found {len(of_profile_names)} onlyfans profiles")

    manager = enlighten.get_manager()
    pbar = manager.counter(total=(len(of_profile_names)), desc='OnlyFans Profiles', unit='profiles')

    profile_info_scraped: list[dict[str, str]] = []

    current_profiles_scraped: int = 0
    create_output_file()

    for of_profile_name in of_profile_names:
        page_info = page_scraper.scrape_page(of_profile_name)
        logger.info(f"{of_profile_name}: Finished!")
        pbar.update()
        add_scraped_info(page_info)
        current_profiles_scraped += 1
        if current_profiles_scraped >= MAX_PROFILE_LIMIT:
            break

    page_scraper.close_driver()

    logger.info(f"Processed {len(profile_info_scraped)} users!")


def read_file_to_list(filename: Path) -> list[str]:
    with open(filename, 'r') as file:
        return file.read().splitlines()


def create_output_file():
    if not output_file.exists():
        with open(output_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)

            # Write the header (column names)
            writer.writeheader()


def add_scraped_info(data: dict[str, str]) -> None:

    # Write the data to the CSV file
    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        # Create a DictWriter object
        writer = csv.DictWriter(file, fieldnames=headers)

        # Write the rows
        writer.writerow(data)


if __name__ == "__main__":
    main()
