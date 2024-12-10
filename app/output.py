import csv
import os
from pathlib import Path

script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
output_file: Path = script_dir / "output" / "output.csv"

headers = ["username", "display_name", "url", "offer", "price", "lists", "avatar_url"]


def create_output_file():

    if output_file.exists():
        os.remove(output_file)

    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()


def add_scraped_info(data: dict[str, str]) -> None:

    # Write the data to the CSV file
    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        # Create a DictWriter object
        writer = csv.DictWriter(file, fieldnames=headers)

        # Write the rows
        writer.writerow(data)