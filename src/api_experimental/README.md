# API Experimental

This directory contains experimental code for accessing the OnlyFans API directly, bypassing the need for Selenium web scraping.

## Status: Non-functional

The API-based approach was attempted but does not currently work. This code is preserved here for reference and future experimentation.

## Files

- **api_client.py** - OnlyFans API client with authentication and retry logic
- **list_fetcher.py** - Data fetching module using API instead of Selenium
- **signature.py** - Cryptographic signature generation for API requests
- **setup_auth.py** - Interactive authentication setup helper

## Why it doesn't work

The OnlyFans API requires complex request signing and authentication that proved difficult to reverse engineer reliably. The Selenium approach, while slower, is more reliable for now.

## Restoring API functionality

If you want to try the API approach again:

1. Move these files back to `src/`
2. Update `main.py` to import from `list_fetcher` instead of `list_scraper`
3. Run `python src/setup_auth.py` to configure authentication
4. See `ONLYFANS_API_DOCUMENTATION.md` in the root directory for API details

## Original working approach

The main codebase uses Selenium web scraping via `list_scraper.py`, which is slower but more reliable.
