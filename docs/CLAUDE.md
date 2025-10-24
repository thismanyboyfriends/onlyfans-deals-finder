# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OnlyFans Deals Finder is a Python CLI tool that automates collection and analysis of OnlyFans subscription data. It uses Selenium to scrape user lists from the OnlyFans web interface, stores data in SQLite for historical tracking, and analyzes subscription patterns to identify deals, pricing discrepancies, and free trial opportunities.

## Architecture

### Core Components

**list_scraper.py** - Selenium-based web scraper
- `OnlyFansScraper` class handles automated browser-based scraping
- Connects to Chrome via remote debugging protocol (port 9222)
- Implements infinite scroll to load all users in a list
- Scrapes user profiles: username, price, subscription status
- Stores data directly in SQLite database via `Database` class
- Uses Chrome debugging mode to maintain logged-in session
- Handles stale element exceptions from Vue.js re-renders gracefully
- Price parsing: Uses `price-parser` library to standardize prices ("SUBSCRIBE $9.99/month" → 9.99, "FREE" → 0)

**database.py** - SQLite data persistence
- `Database` class manages all database operations
- Schema includes: `scrape_runs` (tracks each session), `users` (current state), `price_history` (time-series), `user_lists` (list membership)
- Indexes on `username`, `scraped_at`, `list_name` for query performance
- Enables incremental data writes to prevent loss on errors
- Stored in `data/scraper.db` by default

**db_analyser.py** - Data analysis and reporting
- `DatabaseAnalyser` class performs historical analysis
- Key analysis methods:
  - `find_free_accounts()` - Free/trial accounts not yet subscribed (primary target)
  - `find_historical_lows()` - Users currently at lowest price ever seen
  - `find_price_changes_recently()` - Price changes over specified days
  - `find_categorization_issues()` - Missing or inconsistent list tags
  - `find_trending_prices()` - Recent price trend analysis
- Reports only show users from the most recent scrape run
- Logs detailed findings to JSON files for tracking

**cli.py** - Click-based command-line interface
- Entry point: `main()` function
- Commands: `scrape`, `stats`, `deals`, `history`, `user`, `lists`, `config`
- Global options: `-v/--verbose` for debug logging
- All commands support `--db-path` for custom database location

### Data Flow

1. `ofdeals scrape` [--list-id] - Start Chrome, scrape list
2. Selenium infinite scrolls, scraping each user element
3. Data written incrementally to SQLite (prevents data loss)
4. Analysis runs automatically (or skip with `--no-analyze`)
5. Results printed to console + saved to log files in `data/logs/`
6. User can then run `ofdeals deals`, `ofdeals history`, etc. against stored data

### Key Implementation Details

**Chrome Setup** (handled automatically):
- Starts Chrome with: `--remote-debugging-port=9222 --user-data-dir=C:\tempchromdir`
- Windows paths hardcoded in `list_scraper.py:30-32` (needs adaptation for Mac/Linux)
- Automatically reuses existing Chrome process if available
- Requires manual first-login to OnlyFans (login persists in user data directory)

**Selenium Connection**:
- Uses remote debugging: `options.add_experimental_option("debuggerAddress", "localhost:9222")`
- Retries and skips stale elements from Vue.js re-renders
- Respects rate limiting (~1 user per second)

**Database Schema**:
- `scrape_runs`: Tracks session metadata (start time, count, status)
- `users`: Current snapshot of each user's data
- `price_history`: Complete time-series of all price observations
- `user_lists`: Which lists users belong to (many-to-many)

**Subscription Status Values**:
- `NO_SUBSCRIPTION` - Not subscribed (can be free or paid)
- `SUBSCRIBED` - Currently subscribed
- `RENEWAL` - Approaching renewal (for deals detection)

## Development Commands

### Setup and Installation
```bash
pip install -e .
```
This installs the package in development mode and makes `ofdeals` / `onlyfans-deals` commands available globally.

### Development Mode
```bash
pip install -e ".[dev]"  # Includes pytest, black, flake8
```

### Run Scraper
```bash
ofdeals scrape                          # Default list
ofdeals scrape --list-id 1234567890     # Specific list
ofdeals scrape --no-analyze             # Skip analysis
ofdeals -v scrape --list-id 123         # Verbose output
```

### View Results
```bash
ofdeals stats                           # Database statistics
ofdeals deals                           # Historical low prices
ofdeals history --days 7                # Last 7 days of changes
ofdeals user USERNAME                   # Single user history
ofdeals lists                           # All configured lists
ofdeals config                          # Show Chrome/paths config
```

### Running Tests
```bash
pytest                                  # Run all tests
pytest tests/test_scraper.py::test_function -v
pytest --cov                            # With coverage report
```

### Code Quality
```bash
black src/                              # Format code
flake8 src/ --max-line-length=120       # Lint check
```

## Chrome Configuration for Scraping

Chrome paths are hardcoded in `list_scraper.py:30-32`:
```python
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\tempchromdir"
DEBUGGING_PORT = "9222"
```

**First-time setup**:
1. Run `ofdeals scrape` - Chrome starts automatically
2. Log into OnlyFans manually in the Chrome window
3. Subsequent runs will stay logged in (credentials persist)

**To restart with fresh login**: Delete the user data directory or use a different `--user-data-dir`

## Experimental API Code

**src/api_experimental/** - Abandoned API-based scraper
- Attempted direct OnlyFans API reverse-engineering
- Complex authentication/signature requirements made it unreliable
- Preserved as reference; not functional
- See `src/api_experimental/README.md` for details

## Key Gotchas

1. **Windows-only paths**: Chrome paths hardcoded for Windows. Need updates for Mac/Linux
2. **Port 9222 conflicts**: If Chrome won't start, check if port 9222 is already in use
3. **Database locks**: Only one process can write at a time; close any other instances
4. **Stale elements**: Vue.js re-renders cause element staleness - already handled with retries
5. **List-only output**: Analysis only shows results from most recent scrape (historical context ignored)
