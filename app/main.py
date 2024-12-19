import logging
import os

from pathlib import Path

import output, list_scraper

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
account_list: Path = script_dir / "input" / "account_list.txt"


def main() -> None:
    logger.info("===== ONLYFANS_LIST_PRICE_SCRAPER =====")

    scraped_info: dict[str, dict[str, str]] = list_scraper.scrape_list(880876135)
    output.write_output_file(scraped_info)


if __name__ == "__main__":
    main()
