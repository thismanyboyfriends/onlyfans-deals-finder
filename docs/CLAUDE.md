# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OnlyFans Deals Finder is a Python CLI tool that automates collection and analysis of OnlyFans subscription data. It uses Selenium to scrape user lists from the OnlyFans web interface, stores data in SQLite for historical tracking, and analyzes subscription patterns to identify deals, pricing discrepancies, and free trial opportunities.

## Quick Start

```bash
# Install in development mode
pip install -e ".[dev]"

# Run scraper
ofdeals scrape

# View results
ofdeals new-deals  # Recent price drops
ofdeals deals      # Historical lows
ofdeals stats      # Database stats
```

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
- Chrome setup supports environment variables: `CHROME_PATH`, `USER_DATA_DIR`, `CHROME_DEBUG_PORT`
- Platform detection: Automatically selects Windows paths or Linux/macOS paths (list_scraper.py:30-40)

**database.py** - SQLite data persistence
- `Database` class manages all database operations
- Schema includes: `scrape_runs` (tracks each session), `users` (current state), `price_history` (time-series), `user_lists` (list membership)
- Indexes on `username`, `scraped_at`, `list_name` for query performance
- Enables incremental data writes to prevent loss on errors
- Stored in `data/scraper.db` by default

**db_analyser.py** - Data analysis and reporting
- `DatabaseAnalyser` class performs historical analysis
- Key analysis methods:
  - `find_recent_price_drops()` - Users with significant recent price drops (20%+ off 30-day baseline) - **PRIMARY OUTPUT**
  - `find_free_accounts()` - Free/trial accounts not yet subscribed
  - `find_historical_lows()` - Users currently at lowest price ever seen
  - `find_price_changes_recently()` - Price changes over specified days
  - `find_categorization_issues()` - Missing or inconsistent list tags
  - `find_trending_prices()` - Recent price trend analysis
- Reports only show users from the most recent scrape run
- Logs detailed findings to JSON files in `data/logs/` for tracking
- Recent price drops now output as the primary CLI focus (as of commit 18bd9e8)

**cli.py** - Click-based command-line interface
- Entry point: `main()` function with Click framework
- Commands: `scrape`, `stats`, `deals`, `new-deals`, `history`, `user`, `config`
- Global options: `-v/--verbose` for debug logging
- All data commands support `--db-path` for custom database location
- Entry points in setup.py: `ofdeals` and `onlyfans-deals` (both point to cli:main)

### Data Flow

1. User runs `ofdeals scrape [--list-id]`
2. Chrome starts automatically (or connects to existing instance on port 9222)
3. Selenium infinite scrolls through list, scraping each user element
4. Data written incrementally to SQLite (prevents data loss on errors)
5. Analysis runs automatically (or skip with `--no-analyze`)
6. **Primary output**: Recent price drops printed to console + saved to `data/logs/recent_deals.json`
7. User can then run `ofdeals new-deals`, `ofdeals deals`, `ofdeals history`, etc. for other analyses

### Key Implementation Details

**Chrome Setup** (handles all platforms):
- Environment variables: `CHROME_PATH`, `USER_DATA_DIR`, `CHROME_DEBUG_PORT` (list_scraper.py:39-41)
- Windows defaults: `C:\Program Files\Google\Chrome\Application\chrome.exe`, `C:\tempchromdir`
- Linux/macOS defaults: `/usr/bin/google-chrome`, `~/.config/onlyfans-deals-finder`
- Automatically reuses existing Chrome process if available (checks port 9222)
- Requires manual first-login to OnlyFans (login persists in user data directory)

**Selenium Connection**:
- Uses remote debugging: WebDriver connects to `localhost:9222`
- Retries and skips stale elements from Vue.js re-renders (try/except blocks in scraper loop)
- Respects rate limiting (~1 user per second via time.sleep)

**Database Schema**:
- `scrape_runs`: id, started_at, user_count, is_analyzing, status, list_name
- `users`: id, username, display_name, price, subscription_status, avatar_url, last_scraped
- `price_history`: id, user_id, price, subscription_status, scraped_at
- `user_lists`: user_id, list_name (many-to-many relationship)

**Subscription Status Values**:
- `NO_SUBSCRIPTION` - Not subscribed (can be free or paid)
- `SUBSCRIBED` - Currently subscribed
- `RENEWAL` - Approaching renewal (for deals detection)

**Recent Price Drops Analysis Logic**:
- Compares current price to 30-day rolling average
- Only highlights prices at least 20% below average
- Filters out stale deals (prices that have been low for weeks)
- Only shows if price recently changed (in last 1-2 scrapes)
- Results saved to `logs/recent_deals.json`

## Development Commands

### Setup and Installation
```bash
pip install -e .              # Basic install
pip install -e ".[dev]"       # With dev tools (pytest, black, flake8)
```

### Run Scraper
```bash
ofdeals scrape                          # Default list
ofdeals scrape --list-id 1234567890     # Specific list
ofdeals scrape --no-analyze             # Skip analysis
ofdeals -v scrape --list-id 123         # Verbose output
ofdeals scrape --output ~/custom.db     # Custom database path
```

### View Results
```bash
ofdeals new-deals                       # Recent price drops (new good deals) - PRIMARY OUTPUT
ofdeals stats                           # Database statistics
ofdeals deals                           # Historical low prices
ofdeals history --days 7                # Last 7 days of changes
ofdeals user USERNAME                   # Single user history
ofdeals config                          # Show Chrome/paths config
```

### Code Quality
```bash
black src/                              # Format code
flake8 src/ --max-line-length=120       # Lint check
```

### Running Tests
```bash
pytest                                  # Run all tests
pytest tests/test_scraper.py::test_function -v
pytest --cov                            # With coverage report
```

## Common Development Tasks

### Adding a New Analysis Method
1. Add method to `DatabaseAnalyser` class in db_analyser.py
2. Create corresponding CLI command in cli.py using @cli.command()
3. Method should query `price_history` and `users` tables from latest scrape
4. Output formatted results to console via click.echo()

### Modifying Scraper Output
- Primary output is controlled by `DatabaseAnalyser.find_recent_price_drops()` which is auto-called after scrape
- Print statements and click.echo() determine console output
- JSON logging to `data/logs/recent_deals.json` tracks detailed findings

### Testing Chrome Connectivity
```bash
# Verify Chrome port is accessible
python -c "import socket; s = socket.socket(); print('Port 9222 open' if s.connect_ex(('localhost', 9222)) == 0 else 'Port 9222 closed')"

# Run with verbose logging to see Selenium errors
ofdeals -v scrape
```

## Chrome Configuration

Chrome paths are now platform-aware and support environment variables:
- `CHROME_PATH` - Path to Chrome executable
- `USER_DATA_DIR` - Chrome profile directory
- `CHROME_DEBUG_PORT` - Remote debugging port (default: 9222)

**First-time setup**:
1. Run `ofdeals scrape` - Chrome starts automatically with correct platform paths
2. Log into OnlyFans manually in the Chrome window
3. Subsequent runs stay logged in (credentials persist in user data directory)

**To restart with fresh login**: Delete the user data directory (`rm -r ~/.config/onlyfans-deals-finder` on Linux/macOS or `rmdir C:\tempchromdir` on Windows)

## Experimental API Code

**src/api_experimental/** - Abandoned API-based scraper
- Attempted direct OnlyFans API reverse-engineering
- Complex authentication/signature requirements made it unreliable
- Preserved as reference; not functional
- See `src/api_experimental/README.md` for details

## Key Gotchas and Debugging

1. **Port 9222 already in use**: If Chrome won't start, kill existing Chrome processes
   ```bash
   # Windows: taskkill /F /IM chrome.exe
   # Linux/macOS: pkill -9 chrome
   ```

2. **Database locks**: Only one process can write at a time. Close other instances of ofdeals.

3. **Stale elements**: Vue.js re-renders cause element staleness during scroll - already handled with try/except and retries in list_scraper.py

4. **Missing Chrome**: Set CHROME_PATH environment variable if Chrome isn't in default location

5. **Not logged in**: First scrape requires manual OnlyFans login in Chrome window before data collection starts

6. **Analysis output only from latest scrape**: `find_recent_price_drops()` and other analysis methods intentionally filter to most recent scrape run for clarity
