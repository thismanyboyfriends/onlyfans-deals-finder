import logging
from pathlib import Path
import subprocess

from constants import ALL_LIST
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

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUGGING_PORT = "9222"
USER_DATA_DIR = r"C:\tempchromdir"


def start_chrome():
    command = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUGGING_PORT}",
        f"--user-data-dir={USER_DATA_DIR}"
    ]

    subprocess.Popen(command)


def main():
    logger.info("===== ONLYFANS_LIST_PRICE_SCRAPER =====")

    start_chrome()

    scraper = list_scraper.OnlyFansScraper()
    try:
        filename = scraper.scrape_list(ALL_LIST)
        # filename = r"Z:\scripts\OFDealsFinder\src\output\output-2025-03-05.csv"
        analyser = Analyser(filename)
        analyser.analyse_list()
    finally:
        scraper.close_driver()


if __name__ == "__main__":
    main()
