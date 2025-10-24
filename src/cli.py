"""Command-line interface for OnlyFans Deals Finder."""
import logging
import sys
from pathlib import Path
from typing import Optional
import os

import click

import list_scraper
from db_analyser import DatabaseAnalyser
from database import Database


def get_default_chrome_path() -> str:
    """Get platform-appropriate default Chrome path."""
    if os.name == 'nt':  # Windows
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    else:  # Linux/macOS
        return "/usr/bin/google-chrome"


def get_default_user_data_dir() -> str:
    """Get platform-appropriate default Chrome user data directory."""
    if os.name == 'nt':  # Windows
        return r"C:\tempchromdir"
    else:  # Linux/macOS
        return os.path.expanduser("~/.config/onlyfans-deals-finder")


def setup_logging(verbose: bool):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=level,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
@click.version_option(version="1.0.0", prog_name="OnlyFans Deals Finder")
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """OnlyFans Deals Finder - Scrape and analyze OnlyFans subscription data."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@cli.command()
@click.option('--list-id', '-l', type=str, help='OnlyFans list ID to scrape')
@click.option('--output', '-o', type=click.Path(writable=True), help='Custom database path')
@click.option('--analyze/--no-analyze', default=True, help='Run analysis after scraping')
@click.pass_context
def scrape(ctx: click.Context, list_id: Optional[str], output: Optional[str], analyze: bool) -> None:
    """Scrape a OnlyFans list and store data in the database.

    Data is automatically stored in SQLite database for historical tracking and analysis.
    """
    logger = logging.getLogger(__name__)
    logger.info("===== ONLYFANS DEALS FINDER =====")

    # Validate list_id if provided
    if list_id is not None:
        if not list_id.strip():
            logger.error("List ID cannot be empty")
            sys.exit(1)
        # Optional: validate that it's numeric
        if not list_id.isdigit():
            logger.warning(f"List ID '{list_id}' is not numeric. If scraping fails, verify the list ID.")

    # Validate output path if provided
    if output:
        try:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, ValueError) as e:
            logger.error(f"Invalid output path: {e}")
            sys.exit(1)

    logger.info(f"Scraping list ID: {list_id or 'default'}")

    scraper = list_scraper.OnlyFansScraper(
        db_path=Path(output) if output else None
    )

    try:
        db_path = scraper.scrape_list(list_id)
        logger.info(f"✓ Scraping successful! Database: {db_path}")

        # Run database analysis
        if analyze:
            logger.info("Running analysis...")
            try:
                db_analyser = DatabaseAnalyser(db_path)
                db_analyser.analyse_all()
                db_analyser.close()
            except Exception as e:
                logger.error(f"Analysis failed: {e}", exc_info=ctx.obj.get('verbose', False))
                sys.exit(1)
        else:
            logger.info("Skipping analysis (--no-analyze flag)")

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid value: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during scraping: {e}")
        sys.exit(1)
    finally:
        scraper.close_driver()



@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def stats(ctx: click.Context, db_path: Optional[str]) -> None:
    """Show database statistics and information."""
    logger = logging.getLogger(__name__)

    try:
        db_path_obj = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path_obj)
        analyser.show_stats()
        analyser.close()
    except FileNotFoundError as e:
        logger.error(f"Database not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.option('--days', default=30, type=int, help='Number of days to look back (default: 30)')
@click.pass_context
def history(ctx: click.Context, db_path: Optional[str], days: int) -> None:
    """Show price changes in the last N days."""
    logger = logging.getLogger(__name__)

    if days <= 0:
        logger.error("Days must be a positive integer")
        sys.exit(1)

    try:
        db_path_obj = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path_obj)
        analyser.find_price_changes_recently(days)
        analyser.close()
    except FileNotFoundError as e:
        logger.error(f"Database not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def deals(ctx: click.Context, db_path: Optional[str]) -> None:
    """Find users currently at their historical low price."""
    logger = logging.getLogger(__name__)

    try:
        db_path_obj = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path_obj)
        analyser.find_historical_lows()
        analyser.close()
    except FileNotFoundError as e:
        logger.error(f"Database not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('username', type=str)
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def user(ctx: click.Context, username: str, db_path: Optional[str]) -> None:
    """Show price history for a specific user."""
    logger = logging.getLogger(__name__)

    if not username.strip():
        logger.error("Username cannot be empty")
        sys.exit(1)

    try:
        db_path_obj = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path_obj)
        analyser.get_user_history(username)
        analyser.close()
    except FileNotFoundError as e:
        logger.error(f"Database not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid username: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def new_deals(ctx: click.Context, db_path: Optional[str]) -> None:
    """Find users with recent significant price drops (new good deals)."""
    logger = logging.getLogger(__name__)

    try:
        db_path_obj = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path_obj)
        analyser.find_recent_price_drops()
        analyser.close()
    except FileNotFoundError as e:
        logger.error(f"Database not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--chrome-path', help='Path to Chrome executable',
              default=None)
@click.option('--user-data-dir', help='Chrome user data directory',
              default=None)
def config(chrome_path: Optional[str], user_data_dir: Optional[str]) -> None:
    """Show current configuration."""
    # Use defaults if not provided
    chrome_path = chrome_path or get_default_chrome_path()
    user_data_dir = user_data_dir or get_default_user_data_dir()

    click.echo("\nCurrent Configuration:")
    click.echo("=" * 50)
    click.echo(f"Chrome Path:      {chrome_path}")
    click.echo(f"User Data Dir:    {user_data_dir}")
    click.echo(f"Debugging Port:   9222")
    click.echo(f"Platform:         {'Windows' if os.name == 'nt' else 'Linux/macOS'}")
    click.echo()

    # Check if Chrome exists
    if os.path.exists(chrome_path):
        click.secho("✓ Chrome found", fg='green')
    else:
        click.secho("✗ Chrome not found at this path", fg='red')

    # Check if user data dir exists
    if os.path.exists(user_data_dir):
        click.secho(f"✓ User data directory exists", fg='green')
    else:
        click.secho(f"✗ User data directory doesn't exist (will be created)", fg='yellow')

    click.echo()


def main():
    """Entry point for console script."""
    cli(obj={})


if __name__ == '__main__':
    main()
