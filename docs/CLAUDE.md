# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OFDealsFinder is a Python-based tool that automates the collection and analysis of OnlyFans subscription data. It uses Selenium to scrape user lists from the OnlyFans web interface, exports data to CSV, and analyzes subscription patterns to identify free trials, pricing discrepancies, and categorization issues.

## Architecture

### Core Components

**list_scraper.py** - Selenium-based web scraper
- `OnlyFansScraper` class handles automated browser-based scraping
- Connects to Chrome via remote debugging protocol (port 9222)
- Implements infinite scroll to load all users in a list
- Scrapes user profiles (username, price, subscription status, list tags)
- Writes incrementally to CSV format
- Uses Chrome debugging mode to maintain logged-in session

**analyser.py** - Data analysis module
- `Analyser` class loads CSV output and performs filtering/sorting operations
- Converts CSV rows to anonymous objects for dynamic attribute access
- Analysis methods identify actionable patterns:
  - `find_free_accounts()` - Free/trial accounts not yet subscribed
  - `find_paid()` - Paid accounts not tagged as "paid"
  - `find_free()` - Free accounts not tagged as "free"
  - `find_lapsed_activesubs()` - Expired subscriptions still marked active
  - `find_not_tagged_with_fetish()` - Accounts missing category tags

**constants.py** - List IDs
- Defines OnlyFans list IDs as constants (PAID_LIST, ALL_LIST, etc.)

**main.py** - Entry point
- Orchestrates Selenium scraping → analysis workflow
- Starts scraper, fetches list data, runs analysis

### Data Flow

1. Start Chrome in debugging mode with existing user profile
2. Selenium connects to debug port and navigates to list URL
3. Infinite scroll loads all users in the list
4. For each user element, scrape username, price, subscription status, tags
5. Write incrementally to CSV: `src/output/output-YYYY-MM-DD.csv`
6. Analyser loads CSV and runs analysis methods
7. Results printed as OnlyFans URLs

### Key Implementation Details

**Chrome Setup**: Requires Chrome to be running in remote debugging mode:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\tempchromdir"
```
The scraper starts Chrome automatically via `start_chrome()` function.

**Selenium Connection**: Connects to existing Chrome instance on port 9222:
```python
options.add_experimental_option("debuggerAddress", "localhost:9222")
```

**CSV Output**: Files written to `src/output/output-YYYY-MM-DD.csv` with columns:
- username
- price (standardized to dollar amount)
- subscription_status (NO_SUBSCRIPTION, SUBSCRIBED)
- lists (comma-separated list names)

**Price Parsing**: Uses `price-parser` library to standardize prices from various formats:
- "SUBSCRIBE $9.99 per month" → 9.99
- "FREE for 30 days" → 0
- "SUBSCRIBED" → 0

## Development Commands

### Setup
```bash
pip install -r requirements.txt
```

### Run Scraper
```bash
python src/main.py
```

Make sure Chrome is logged into OnlyFans first (the scraper will start Chrome automatically).

### Run Tests
```bash
pytest
```

### Run Single Test
```bash
pytest tests/test_name.py::test_function_name
```

## Chrome Setup for Scraping

The scraper needs Chrome to be logged into OnlyFans:

1. The scraper automatically starts Chrome with: `--remote-debugging-port=9222 --user-data-dir="C:\tempchromdir"`
2. First time: Manually log into OnlyFans in this Chrome window
3. Chrome will stay logged in for future scraper runs
4. Selenium connects to this Chrome instance via debugging port

## Experimental API Code

**src/api_experimental/** - Experimental API-based scraper (non-functional)
- Previously attempted to reverse-engineer OnlyFans API
- Moved to this directory as it doesn't currently work
- Preserved for reference and future experimentation
- See `src/api_experimental/README.md` for details

The API approach was attempted but proved unreliable due to complex authentication and request signing requirements. The Selenium approach is slower but more reliable.

## Documentation

**ONLYFANS_API_DOCUMENTATION.md** - Reverse-engineered API documentation
- Created during API experimentation
- Contains endpoint details, authentication flow, data models
- May be useful for future API attempts
