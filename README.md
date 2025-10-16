# OnlyFans Deals Finder

A Python-based tool that automates the collection and analysis of OnlyFans subscription data. It scrapes user lists from the OnlyFans web interface, exports data to CSV, and analyzes subscription patterns to identify free trials, pricing opportunities, and categorization issues.

## Features

- **Automated Scraping**: Uses Selenium to scrape OnlyFans user lists with infinite scroll support
- **Smart Detection**: Identifies free trials, paid subscriptions, and promotional offers
- **Data Analysis**: Analyzes subscription patterns to find:
  - Free/trial accounts not yet subscribed
  - Pricing discrepancies and categorization issues
  - Expired subscriptions still marked as active
  - Accounts missing category tags
- **CSV Export**: Exports user data with prices, subscription status, and list tags
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
pip install -r requirements.txt
```

This will install:
- `selenium` - Web automation
- `chromedriver` - Chrome driver for Selenium
- `undetected-chromedriver` - Bypass detection
- `price-parser` - Parse price strings
- `pytest` - Testing framework
- Other dependencies

## Setup

### Chrome Configuration

The scraper requires Chrome to run in remote debugging mode with a persistent user profile:

#### First-Time Setup

1. **The scraper will automatically start Chrome** with the correct settings
2. **On first run**, you'll need to manually log into OnlyFans in the Chrome window that opens
3. **Chrome will remember your login** for future scraper runs

#### What Happens Under the Hood

The scraper starts Chrome with:
```bash
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\tempchromdir"
```

- `--remote-debugging-port=9222`: Allows Selenium to connect
- `--user-data-dir`: Stores your login session persistently

#### Manual Chrome Start (Optional)

If you prefer to start Chrome manually:

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\tempchromdir"
```

Then log into OnlyFans in this Chrome window.

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

### Basic Usage

Run the scraper to fetch and analyze a list:

```bash
python src/main.py
```

By default, this scrapes the `ALL_LIST` defined in `constants.py`.

### Output

Data is saved to `src/output/output-YYYY-MM-DD.csv` with columns:

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

## Project Structure

```
onlyfans-deals-finder/
├── src/
│   ├── main.py                    # Entry point
│   ├── list_scraper.py            # Selenium-based scraper
│   ├── analyser.py                # Data analysis
│   ├── constants.py               # List IDs configuration
│   ├── output/                    # CSV output directory
│   │   └── output-YYYY-MM-DD.csv
│   └── api_experimental/          # Non-working API approach (experimental)
│       ├── api_client.py
│       ├── list_fetcher.py
│       ├── signature.py
│       ├── setup_auth.py
│       └── README.md
├── examples/                      # HTML examples for reference
├── requirements.txt               # Python dependencies
├── CLAUDE.md                      # Development documentation
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
6. **CSV Export**: Writes data incrementally in batches
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
python src/main.py
```

### "Timeout waiting for page to load"

**Problem**: Page took too long to load

**Solutions**:
- Check your internet connection
- Verify you're logged into OnlyFans
- Increase timeout in `wait_until_page_loads()` (line 191)

### No Users Scraped

**Problem**: CSV is empty or has very few users

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

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_scraper.py::test_price_parsing
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

---

**Note**: This tool requires an active OnlyFans account and is intended for personal subscription management and analysis.
