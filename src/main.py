import logging
from pathlib import Path

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
        analyser = Analyser(filename)
        analyser.analyse_list()
    finally:
        scraper.close_driver()


if __name__ == "__main__":
    main()
