import csv
import os
from pathlib import Path
from datetime import date

current_date = date.today().strftime("%Y-%m-%d")
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
output_file: Path = script_dir / "output" / f"output-{current_date}.csv"


def derive_headers(scraped_info: dict[str, dict[str, str]]):
    first_value = next(iter(scraped_info.values()))
    return first_value.keys()


def write_output_file(data: dict[str, dict[str, str]]):

    headers = derive_headers(data)

    if output_file.exists():
        os.remove(output_file)

    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        for key, value in data.items():
            writer.writerow(value)
