# OnlyFans Deals Finder

A Python-based tool that automates the collection and analysis of OnlyFans subscription data. It scrapes user lists from the OnlyFans web interface, stores data in SQLite for historical tracking, and analyzes subscription patterns to identify deals, pricing discrepancies, and categorization issues.

## Features

- **Automated Scraping**: Uses Selenium to scrape OnlyFans user lists with infinite scroll support
- **SQLite Database**: Historical price tracking with advanced analysis (default mode)
- **Smart Detection**: Identifies free trials, paid subscriptions, and promotional offers
- **Historical Tracking**: Track price changes over time and find historical lows
- **Data Analysis**: Analyzes subscription patterns to find:
  - Free/trial accounts not yet subscribed
  - Pricing discrepancies and categorization issues
  - Expired subscriptions still marked as active
  - Accounts missing category tags
  - Users at historical low prices
  - Recent price trends and changes
- **Incremental Writing**: Writes data incrementally to prevent data loss
- **Optimized Performance**: Vue.js-aware scraping with batch processing

## Prerequisites

- **Python 3.7+**
- **Google Chrome** (installed at default location)
- **Active OnlyFans Account** (you must be logged in)
- **Windows OS** (currently configured for Windows paths, but adaptable)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/onlyfans-deals-finder.git
cd onlyfans-deals-finder
```

### 2. Install Python Dependencies

```bash
pip install -e .
```

## Setup

### Chrome Configuration

The scraper requires Chrome to run in remote debugging mode with a persistent user profile:

#### First-Time Setup

1. **The scraper will automatically start Chrome** with the correct settings
2. **On first run**, you'll need to manually log into OnlyFans in the Chrome window that opens
3. **Chrome will remember your login** for future scraper runs

## Usage

### Installation

After cloning, install the package in development mode:

```bash
pip install -e .
```

This makes the `ofdeals` and `onlyfans-deals` commands available globally.

### Quick Start

```bash
# Scrape data (uses database by default)
ofdeals scrape

# View statistics
ofdeals stats

# Find users at historical low prices
ofdeals deals

# Check price history
ofdeals history

# View configuration
ofdeals config

# Show all configured lists
ofdeals lists
```

### Available Commands

| Command | Description |
|---------|-------------|
| `ofdeals scrape` | Scrape list and store in database |
| `ofdeals stats` | Show database statistics |
| `ofdeals deals` | Find users at historical low prices 💰 |
| `ofdeals history` | Show recent price changes |
| `ofdeals user USERNAME` | Show user's price history |
| `ofdeals lists` | Show all configured list IDs |
| `ofdeals config` | Show current configuration |

### Global Options

Available for all commands:

- `--version` - Show version and exit
- `-v, --verbose` - Enable verbose/debug logging
- `--help` - Show help message

### Command Reference

#### `ofdeals scrape`

Scrape a OnlyFans list and store data in the database (optionally analyze results).

**Options:**
- `--list-id, -l TEXT` - OnlyFans list ID to scrape
- `--analyze/--no-analyze` - Run analysis after scraping (default: analyze)
- `-v, --verbose` - Enable verbose/debug logging

**Examples:**

```bash
# Basic scrape with analysis
ofdeals scrape

# Scrape specific list
ofdeals scrape --list-id 1234567890

# Custom database location
ofdeals scrape --output ~/data/my-scraper.db

# Scrape without analysis (just save data)
ofdeals scrape --no-analyze

# Verbose logging for debugging
ofdeals -v scrape --list-id 1234567890
```

#### `ofdeals stats`

Show database statistics including total users, scrapes, and price records.

**Example:**

```bash
$ ofdeals stats

============================================================
DATABASE STATISTICS
============================================================
Total Users:       462
Total Scrapes:     15
Price Records:     3,241
Last Scrape:       2025-10-16 14:30:00
============================================================
```

#### `ofdeals deals`

Find users currently at their historical low prices (best time to subscribe).

**Example:**

```bash
$ ofdeals deals

============================================================
HISTORICAL LOW PRICES (23)
============================================================
Users currently at their lowest price ever:

💰 https://onlyfans.com/username1
   Current: $4.99 (seen 8 times)

💰 https://onlyfans.com/username2
   Current: $7.99 (seen 5 times)
```

#### `ofdeals history`

Show recent price changes over a specified time period.

**Options:**
- `--days, -d INTEGER` - Number of days to look back (default: 30)

**Examples:**

```bash
# Last 30 days (default)
ofdeals history

# Last 7 days
ofdeals history --days 7

# Last 90 days
ofdeals history --days 90
```

#### `ofdeals user`

Show complete price history for a specific user.

**Arguments:**
- `USERNAME` - OnlyFans username

**Example:**

```bash
$ ofdeals user username1

============================================================
PRICE HISTORY: @username1
============================================================
  2025-10-16 01:45:00: $9.99 (NO_SUBSCRIPTION)
  2025-10-10 14:30:00: $12.99 (NO_SUBSCRIPTION)
  2025-10-05 09:15:00: $9.99 (NO_SUBSCRIPTION)
  2025-09-28 16:20:00: $14.99 (NO_SUBSCRIPTION)
```

#### `ofdeals config`

Show current configuration (Chrome path, user data directory, debugging port, etc.).

**Options:**
- `--chrome-path TEXT` - Path to Chrome executable
- `--user-data-dir TEXT` - Chrome user data directory

**Example:**

```bash
$ ofdeals config

Current Configuration:
==================================================
Chrome Path:      C:\Program Files\Google\Chrome\Application\chrome.exe
User Data Dir:    C:\tempchromdir
Debugging Port:   9222

✓ Chrome found
✓ User data directory exists
```

### Analysis Results

The analyzer will print URLs for:

- **Free accounts** not yet subscribed
- **Paid accounts** not tagged as "paid"
- **Free accounts** not tagged as "free"
- **Expired subscriptions** still marked active
- **Accounts missing fetish category tags**

## Troubleshooting

### Chrome Won't Start

**Problem**: Chrome is already running on port 9222

**Solution**:
```bash
# Close all Chrome instances
taskkill /F /IM chrome.exe

# Restart the scraper
ofdeals scrape
```

### "Timeout waiting for page to load"

**Problem**: Page took too long to load

**Solutions**:
- Check your internet connection
- Verify you're logged into OnlyFans
- Increase timeout in `wait_until_page_loads()` in `list_scraper.py`

### No Users Scraped

**Problem**: Database is empty or has very few users

**Solutions**:
- Check that the list isn't empty on OnlyFans
- Look for error messages in console output

### Price Parsing Errors

**Problem**: Warnings about price parsing failures

**What to do**:
- Check console logs for the actual price text
- The scraper will mark these users with `price: "?"` and `subscription_status: "?"`
- These indicate OnlyFans changed their UI format

### Stale Element Errors

**Problem**: `StaleElementReferenceException` errors

**Why it happens**: Vue.js re-renders elements during scrolling

**Solution**: Already handled automatically - the scraper retries and skips stale elements

### Database is Locked

**Problem**: Database is locked when trying to scrape

**Solution**:
- Close any other processes using the database
- Only one process can write at a time

### Start Fresh with Database

```bash
# Delete the database file
rm data/scraper.db

# Next scrape will create a new one
ofdeals scrape
```


## Uninstallation

```bash
pip uninstall onlyfans-deals-finder
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_scraper.py::test_price_parsing

# Run with coverage
pytest --cov
```

## Limitations

- **Selenium-based**: Slower than API-based approaches, but more reliable
- **Rate Limiting**: Scrapes at ~1 user per second to avoid detection
- **Chrome Required**: Must use Chrome browser
- **Windows Paths**: Currently configured for Windows (adaptable to Mac/Linux)

## Experimental API Module

The `src/api_experimental/` directory contains a non-working attempt to use OnlyFans' API directly. This approach was abandoned due to complex authentication and request signing requirements.

**Status**: Not functional
**Reason**: Complex crypto signatures and auth tokens required
**Preserved**: For future reference and experimentation

See `src/api_experimental/README.md` for details.

## Disclaimer

This tool is for personal data analysis purposes only. Users are responsible for complying with OnlyFans' Terms of Service. Use at your own risk.

## License

This project is provided as-is for educational and personal use.

---

**Note**: This tool requires an active OnlyFans account and is intended for personal subscription management and analysis.
