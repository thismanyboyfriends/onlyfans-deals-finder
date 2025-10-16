# OnlyFans Deals Finder

A Python-based tool that automates the collection and analysis of OnlyFans subscription data. It scrapes user lists from the OnlyFans web interface, stores data in SQLite for historical tracking, and analyzes subscription patterns to identify deals, pricing discrepancies, and categorization issues.

## Features

- **Automated Scraping**: Uses Selenium to scrape OnlyFans user lists with infinite scroll support
- **SQLite Database**: Historical price tracking with advanced analysis (default mode)
- **CSV Export**: Optional CSV export
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


### Configuration

Edit `src/constants.py` to set your OnlyFans list IDs:

```python
PAID_LIST = "1234567890"      # Your paid subscribers list ID
ALL_LIST = "0987654321"       # Your all users list ID
FREE_TRIAL_LIST = "1122334455" # Your free trial list ID
```

**To find your list IDs:**
1. Navigate to a list on OnlyFans
2. Check the URL: `onlyfans.com/my/collections/user-lists/1234567890`
3. The number at the end is your list ID

## Usage

### Installation

After cloning, install the package in development mode:

```bash
pip install -e .
```

This makes the `ofdeals` and `onlyfans-deals` commands available globally.

### Quick Start

```bash
# Install
pip install -e .

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
| `ofdeals export output.csv` | Export database to CSV |
| `ofdeals lists` | Show all configured list IDs |
| `ofdeals config` | Show current configuration |
| `ofdeals analyze FILE.csv` | Analyze a CSV file (legacy mode) |

### Global Options

Available for all commands:

- `--version` - Show version and exit
- `-v, --verbose` - Enable verbose/debug logging
- `--help` - Show help message

### Command Reference

#### `ofdeals scrape`

Scrape a OnlyFans list and store data in the database (optionally analyze results).

**Options:**
- `--list-id, -l TEXT` - OnlyFans list ID to scrape (defaults to `constants.ALL_LIST`)
- `--output, -o PATH` - Custom database path (for database mode) or CSV file path (for CSV mode)
- `--analyze/--no-analyze` - Run analysis after scraping (default: analyze)
- `--use-csv` - Use CSV mode instead of database (legacy)
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

# Scrape in legacy CSV mode
ofdeals scrape --use-csv

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
$ ofdeals user bronwinaurora

============================================================
PRICE HISTORY: @bronwinaurora
============================================================
  2025-10-16 01:45:00: $9.99 (NO_SUBSCRIPTION)
  2025-10-10 14:30:00: $12.99 (NO_SUBSCRIPTION)
  2025-10-05 09:15:00: $9.99 (NO_SUBSCRIPTION)
  2025-09-28 16:20:00: $14.99 (NO_SUBSCRIPTION)
```

#### `ofdeals export`

Export current database data to CSV format for external analysis.

**Arguments:**
- `OUTPUT_FILE` - Path where to save the CSV file

**Options:**
- `--db-path PATH` - Custom database path

**Example:**

```bash
# Export to CSV
ofdeals export analysis.csv

# Export from custom database
ofdeals export analysis.csv --db-path ~/my-data/custom.db
```

#### `ofdeals lists`

Show all configured list IDs from `constants.py`.

**Example:**

```bash
$ ofdeals lists

Configured Lists:
==================================================
  ALL_LIST             880876135
  PAID_LIST            1052921466
  FREE_TRIAL_LIST      1102422928

Usage:
  ofdeals scrape --list-id 880876135
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

#### `ofdeals analyze` (Legacy)

Analyze an existing CSV file from a previous scrape (legacy CSV mode).

**Arguments:**
- `CSV_FILE` - Path to CSV file to analyze (required)

**Examples:**

```bash
# Analyze a specific file
ofdeals analyze src/output/output-2025-10-16.csv

# Analyze with verbose logging
ofdeals -v analyze data.csv
```


### Output Data

#### Database Mode (Default)

Data is automatically stored in SQLite database at `src/data/scraper.db` with full price history tracking.

Query data using CLI commands:
- `ofdeals stats` - View database statistics
- `ofdeals deals` - Find historical low prices
- `ofdeals history` - View recent price changes
- `ofdeals user USERNAME` - Get user price history
- `ofdeals export` - Export to CSV

#### CSV Mode (Legacy)

When using `--use-csv` flag, data is saved to `src/output/output-YYYY-MM-DD.csv` with columns:

| Column | Description | Example |
|--------|-------------|---------|
| `username` | OnlyFans username (without @) | `exampleuser` |
| `price` | Monthly subscription price | `9.99` |
| `subscription_status` | Current status | `NO_SUBSCRIPTION`, `SUBSCRIBED` |
| `lists` | Comma-separated list names | `paid, vanilla, freetrial` |

### Analysis Results

The analyzer will print URLs for:

- **Free accounts** not yet subscribed
- **Paid accounts** not tagged as "paid"
- **Free accounts** not tagged as "free"
- **Expired subscriptions** still marked active
- **Accounts missing fetish category tags**

## Database Schema

The SQLite database stores data in these tables:

### `users`
Current state of each user:
- `username` (primary key)
- `display_name`
- `current_price`
- `subscription_status`
- `first_seen`, `last_seen`

### `price_history`
Every price point ever scraped:
- `username`
- `price`
- `subscription_status`
- `scraped_at`
- `scrape_run_id`

### `user_lists`
Which lists users belong to (with history):
- `username`
- `list_name`
- `added_at`, `removed_at`
- `scrape_run_id`

### `scrape_runs`
Metadata about each scrape:
- `list_id`
- `started_at`, `completed_at`
- `user_count`, `status`

## Project Structure

```
onlyfans-deals-finder/
├── src/
│   ├── main.py                    # Entry point
│   ├── cli.py                     # CLI commands
│   ├── list_scraper.py            # Selenium-based scraper
│   ├── analyser.py                # Data analysis
│   ├── database.py                # SQLite database management
│   ├── db_analyser.py             # Database-based analysis
│   ├── constants.py               # List IDs configuration
│   ├── output/                    # CSV output directory (legacy mode)
│   │   └── output-YYYY-MM-DD.csv
│   ├── data/                      # Database directory
│   │   └── scraper.db
│   └── api_experimental/          # Non-working API approach (experimental)
│       ├── api_client.py
│       ├── list_fetcher.py
│       ├── signature.py
│       ├── setup_auth.py
│       └── README.md
├── docs/                          # Documentation
│   ├── database.md                # Detailed database documentation
│   └── CLAUDE.md                  # Development guidance
├── examples/                      # HTML examples for reference
├── requirements.txt               # Python dependencies
├── setup.py                       # Setup configuration
├── ONLYFANS_API_DOCUMENTATION.md  # Reverse-engineered API docs
└── README.md                      # This file
```

## How It Works

### Scraping Process

1. **Chrome Startup**: Launches Chrome with remote debugging enabled
2. **Page Load**: Navigates to the specified OnlyFans list URL
3. **Vue Detection**: Waits for Vue.js virtual scroller to initialize
4. **Infinite Scroll**:
   - Scrolls to bottom
   - Waits for Vue to render new items
   - Scrapes only new visible users
   - Repeats until no new users found (3 consecutive failures)
5. **Data Extraction**: For each user, extracts:
   - Username from profile link
   - Price from subscribe button text
   - Subscription status (subscribed/not subscribed)
   - List tags (paid, free, etc.)
6. **Database Storage**: Writes data to SQLite with full price history
7. **Analysis**: Runs analysis methods to identify patterns

### Price Detection

The scraper handles various price formats:

- `SUBSCRIBE $9.99 per month` → `9.99`
- `FREE for 30 days` → `0` (free trial)
- `SUBSCRIBED` → `0` (already subscribed)
- `$5 per month` → `5.00`

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

**Problem**: Database/CSV is empty or has very few users

**Solutions**:
- Verify the list ID in `constants.py` is correct
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
rm src/data/scraper.db

# Next scrape will create a new one
ofdeals scrape
```

## Advanced SQL Queries

The database is standard SQLite. Query it directly for custom analysis:

```bash
# Open database
sqlite3 src/data/scraper.db

# Example queries:
# Users who decreased price in last week
SELECT username, price, scraped_at
FROM price_history
WHERE scraped_at >= date('now', '-7 days')
ORDER BY username, scraped_at;

# Average price per user
SELECT username, AVG(price) as avg_price
FROM price_history
GROUP BY username
HAVING COUNT(*) > 3
ORDER BY avg_price;

# Find users trending cheaper
SELECT username, price, scraped_at
FROM price_history
WHERE username IN (
  SELECT username FROM price_history
  WHERE scraped_at >= date('now', '-30 days')
  GROUP BY username
  HAVING MIN(price) < MAX(price)
)
ORDER BY username, scraped_at;
```

## Example Workflows

### Daily Routine

```bash
# Morning: scrape all lists
ofdeals scrape --list-id 880876135

# Check for new deals
ofdeals deals

# See what changed
ofdeals history --days 1
```

### Weekly Analysis

```bash
# See weekly trends
ofdeals history --days 7

# Export for spreadsheet analysis
ofdeals export weekly-$(date +%Y-%m-%d).csv
```

### Before Subscribing

```bash
# Check if user is at historical low
ofdeals user targetusername

# Check overall deals
ofdeals deals
```

### Multiple Lists Scraping

```bash
# Morning: scrape all lists
ofdeals scrape --list-id 880876135 --output daily-all.csv

# Afternoon: scrape free trials
ofdeals scrape --list-id 1102422928 --output daily-trials.csv

# Evening: analyze both
ofdeals analyze daily-all.csv
ofdeals analyze daily-trials.csv
```

### Quick Data Collection (No Analysis)

```bash
# Just collect data without analysis
ofdeals scrape --no-analyze --output raw-data.csv

# Process later when needed
ofdeals analyze raw-data.csv
```

### Debugging Issues

```bash
# Enable verbose logging to see what's happening
ofdeals -v scrape --list-id 1234567890

# Check configuration
ofdeals config

# Verify list IDs
ofdeals lists
```

## Tips and Best Practices

1. **First Run**: Chrome will open for you to log into OnlyFans manually
2. **Session Persistence**: Login is saved to `C:\tempchromdir` for future runs
3. **Multiple Lists**: Run `ofdeals lists` to see all configured lists
4. **Automation**: Use `--no-analyze` to scrape multiple lists quickly, then analyze in batch
5. **Troubleshooting**: Use `-v` flag to see detailed debug information
6. **Scrape Regularly**: Run scraping daily to build good historical price data
7. **Historical Lows**: Check `ofdeals deals` before subscribing to catch the best prices
8. **Price Alerts**: Use `ofdeals history` to spot recent discounts
9. **Custom Queries**: Database is SQLite - use any SQL tool for advanced analysis

## Exit Codes

- `0` - Success
- `1` - Error occurred
- `130` - Interrupted by user (Ctrl+C)

## Legacy Usage

The old `python src/main.py` still works for backwards compatibility but will suggest using the new CLI:

```bash
python src/main.py  # Still works, but shows suggestion to use ofdeals
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

## Performance

Typical scraping speeds:
- **Small lists** (< 50 users): ~30-60 seconds
- **Medium lists** (50-200 users): ~2-5 minutes
- **Large lists** (200+ users): ~5-15 minutes

Performance improvements in latest version:
- 2-3x faster than previous version
- Vue.js-aware waiting (no fixed 4-second delays)
- Batch CSV writing (10-100x faster I/O)
- Smart element detection (only scrapes new users)

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

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Disclaimer

This tool is for personal data analysis purposes only. Users are responsible for complying with OnlyFans' Terms of Service. Use at your own risk.

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review `CLAUDE.md` for development details
- See `docs/database.md` for detailed database documentation

---

**Note**: This tool requires an active OnlyFans account and is intended for personal subscription management and analysis.
