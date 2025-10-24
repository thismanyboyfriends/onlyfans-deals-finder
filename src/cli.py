"""Command-line interface for OnlyFans Deals Finder."""
import logging
import sys
from pathlib import Path
import os

import click

import list_scraper
from db_analyser import DatabaseAnalyser
from database import Database


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
@click.option('--list-id', '-l', help='OnlyFans list ID to scrape')
@click.option('--output', '-o', type=click.Path(), help='Custom database path')
@click.option('--analyze/--no-analyze', default=True, help='Run analysis after scraping')
@click.pass_context
def scrape(ctx, list_id, output, analyze):
    """Scrape a OnlyFans list and store data in the database.

    Data is automatically stored in SQLite database for historical tracking and analysis.
    """
    logger = logging.getLogger(__name__)
    logger.info("===== ONLYFANS DEALS FINDER =====")

    # Use provided list_id or default to ALL_LIST
    target_list = list_id
    logger.info(f"Scraping list ID: {target_list}")

    scraper = list_scraper.OnlyFansScraper(
        db_path=Path(output) if output else None
    )

    try:
        db_path = scraper.scrape_list(target_list)
        logger.info(f"✓ Scraping successful! Database: {db_path}")

        # Run database analysis
        if analyze:
            logger.info("Running analysis...")
            db_analyser = DatabaseAnalyser(db_path)
            db_analyser.analyse_all()
            db_analyser.close()
        else:
            logger.info("Skipping analysis (--no-analyze flag)")

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)
    finally:
        scraper.close_driver()



@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def stats(ctx, db_path):
    """Show database statistics and information."""
    logger = logging.getLogger(__name__)

    try:
        db_path = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path)
        analyser.show_stats()
        analyser.close()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.option('--days', default=30, help='Number of days to look back (default: 30)')
@click.pass_context
def history(ctx, db_path, days):
    """Show price changes in the last N days."""
    logger = logging.getLogger(__name__)

    try:
        db_path = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path)
        analyser.find_price_changes_recently(days)
        analyser.close()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def deals(ctx, db_path):
    """Find users currently at their historical low price."""
    logger = logging.getLogger(__name__)

    try:
        db_path = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path)
        analyser.find_historical_lows()
        analyser.close()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


@cli.command()
@click.argument('username')
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def user(ctx, username, db_path):
    """Show price history for a specific user."""
    logger = logging.getLogger(__name__)

    try:
        db_path = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path)
        analyser.get_user_history(username)
        analyser.close()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)

@cli.command()
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def new_deals(ctx, db_path):
    """Find users with recent significant price drops (new good deals)."""
    logger = logging.getLogger(__name__)

    try:
        db_path = Path(db_path) if db_path else None
        analyser = DatabaseAnalyser(db_path)
        analyser.find_recent_price_drops()
        analyser.close()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


@cli.command()
@click.option('--chrome-path', help='Path to Chrome executable',
              default=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
@click.option('--user-data-dir', help='Chrome user data directory',
              default=r"C:\tempchromdir")
def config(chrome_path, user_data_dir):
    """Show current configuration."""
    click.echo("\nCurrent Configuration:")
    click.echo("=" * 50)
    click.echo(f"Chrome Path:      {chrome_path}")
    click.echo(f"User Data Dir:    {user_data_dir}")
    click.echo(f"Debugging Port:   9222")
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
