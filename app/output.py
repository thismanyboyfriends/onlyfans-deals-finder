import csv
import os
from pathlib import Path

script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
output_file: Path = script_dir / "output" / "output.csv"


def derive_headers(scraped_info: dict[str, dict[str, str]]):
    first_value = next(iter(scraped_info.values()))
    return first_value.keys()


def create_output_file(headers: list[str]):
    if output_file.exists():
        os.remove(output_file)

    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()


def add_scraped_info(data: dict[str, str], headers: list[str]) -> None:
    # Write the data to the CSV file
    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        # Create a DictWriter object
        writer = csv.DictWriter(file, fieldnames=headers)

        # Write the rows
        writer.writerow(data)
