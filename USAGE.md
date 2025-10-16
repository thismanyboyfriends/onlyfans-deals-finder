# OnlyFans Deals Finder - CLI Usage Guide

Modern command-line interface for scraping and analyzing OnlyFans subscription data.

## Installation

Install the package in development mode:

```bash
# From the project root directory
pip install -e .
```

This makes the `ofscraper` and `onlyfans-scraper` commands available globally.

## Quick Start

```bash
# Scrape the default list (configured in constants.py)
ofscraper scrape

# Scrape a specific list by ID
ofscraper scrape --list-id 1234567890

# Scrape without running analysis
ofscraper scrape --no-analyze

# Analyze an existing CSV file
ofscraper analyze output-2025-10-16.csv
```

## Commands

### `ofscraper scrape`

Scrape a OnlyFans list and optionally analyze the results.

**Options:**
- `--list-id, -l TEXT` - OnlyFans list ID to scrape (defaults to `constants.ALL_LIST`)
- `--output, -o PATH` - Custom output CSV file path
- `--analyze/--no-analyze` - Run analysis after scraping (default: analyze)
- `-v, --verbose` - Enable verbose/debug logging

**Examples:**

```bash
# Basic scrape with analysis
ofscraper scrape

# Scrape specific list
ofscraper scrape --list-id 1234567890

# Custom output location
ofscraper scrape --output ~/data/my-scrape.csv

# Scrape without analysis (just save CSV)
ofscraper scrape --no-analyze

# Verbose logging for debugging
ofscraper -v scrape --list-id 1234567890
```

### `ofscraper analyze`

Analyze an existing CSV file from a previous scrape.

**Arguments:**
- `CSV_FILE` - Path to CSV file to analyze (required)

**Examples:**

```bash
# Analyze a specific file
ofscraper analyze src/output/output-2025-10-16.csv

# Analyze with verbose logging
ofscraper -v analyze data.csv
```

### `ofscraper lists`

Show all configured list IDs from `constants.py`.

**Example:**

```bash
$ ofscraper lists

Configured Lists:
==================================================
  ALL_LIST             880876135
  PAID_LIST            1052921466
  FREE_TRIAL_LIST      1102422928

Usage:
  ofscraper scrape --list-id 880876135
```

### `ofscraper config`

Show current configuration (Chrome path, user data directory, etc.).

**Options:**
- `--chrome-path TEXT` - Path to Chrome executable
- `--user-data-dir TEXT` - Chrome user data directory

**Example:**

```bash
$ ofscraper config

Current Configuration:
==================================================
Chrome Path:      C:\Program Files\Google\Chrome\Application\chrome.exe
User Data Dir:    C:\tempchromdir
Debugging Port:   9222

✓ Chrome found
✓ User data directory exists
```

## Global Options

Available for all commands:

- `--version` - Show version and exit
- `-v, --verbose` - Enable verbose/debug logging
- `--help` - Show help message

## Workflow Examples

### Daily Scraping Routine

```bash
# Morning: scrape all lists
ofscraper scrape --list-id 880876135 --output daily-all.csv

# Afternoon: scrape free trials
ofscraper scrape --list-id 1102422928 --output daily-trials.csv

# Evening: analyze both
ofscraper analyze daily-all.csv
ofscraper analyze daily-trials.csv
```

### Quick Data Collection (No Analysis)

```bash
# Just collect data without analysis
ofscraper scrape --no-analyze --output raw-data.csv

# Process later when needed
ofscraper analyze raw-data.csv
```

### Debugging Issues

```bash
# Enable verbose logging to see what's happening
ofscraper -v scrape --list-id 1234567890

# Check configuration
ofscraper config

# Verify list IDs
ofscraper lists
```

## Output

### Scrape Command

Creates a CSV file with columns:
- `username` - OnlyFans username
- `price` - Monthly subscription price
- `subscription_status` - `NO_SUBSCRIPTION` or `SUBSCRIBED`
- `lists` - Comma-separated list tags

Default location: `src/output/output-YYYY-MM-DD.csv`

### Analyze Command

Prints OnlyFans URLs for:
- Free accounts not yet subscribed
- Paid accounts not tagged as "paid"
- Free accounts not tagged as "free"
- Expired subscriptions still marked active
- Accounts missing category tags

## Exit Codes

- `0` - Success
- `1` - Error occurred
- `130` - Interrupted by user (Ctrl+C)

## Tips

1. **First Run**: Chrome will open for you to log into OnlyFans manually
2. **Session Persistence**: Login is saved to `C:\tempchromdir` for future runs
3. **Multiple Lists**: Run `ofscraper lists` to see all configured lists
4. **Automation**: Use `--no-analyze` to scrape multiple lists, then analyze in batch
5. **Troubleshooting**: Use `-v` flag to see detailed debug information

## Legacy Usage

The old `python src/main.py` still works for backwards compatibility but will suggest using the new CLI:

```bash
python src/main.py  # Still works, but shows suggestion to use ofscraper
```

## Uninstallation

```bash
pip uninstall onlyfans-deals-finder
```
