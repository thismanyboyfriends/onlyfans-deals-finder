import logging
from pathlib import Path
import os

import constants
import list_scraper
from analyser import Analyser

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
ACCOUNT_LIST = SCRIPT_DIR / "input" / "account_list.txt"


def main():
    logger.info("===== ONLYFANS_LIST_PRICE_SCRAPER =====")

    scraper = list_scraper.OnlyFansScraper()
    try:
        filename = scraper.scrape_list(constants.ALL_LIST)

        # Check if scraping was successful before analyzing
        if not os.path.exists(filename):
            logger.error(f"CSV file not created. Scraping may have failed.")
            return

        # Check if file has data (more than just headers)
        file_size = os.path.getsize(filename)
        if file_size < 100:  # Less than 100 bytes means likely just headers or empty
            logger.warning(f"CSV file is empty or has no data. Skipping analysis.")
            logger.info(f"Output file: {filename}")
            return

        logger.info(f"Scraping successful. Analyzing {filename}...")
        analyser = Analyser(filename)
        analyser.analyse_list()
    finally:
        scraper.close_driver()


if __name__ == "__main__":
    main()
