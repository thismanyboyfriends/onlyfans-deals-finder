"""Command-line interface for OnlyFans Deals Finder."""
import logging
import sys
from pathlib import Path
import os

import click

import constants
import list_scraper
from analyser import Analyser
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
@click.option('--output', '-o', type=click.Path(), help='Output path (database or CSV)')
@click.option('--analyze/--no-analyze', default=True, help='Run analysis after scraping')
@click.option('--use-csv', is_flag=True, help='Use legacy CSV mode instead of database')
@click.pass_context
def scrape(ctx, list_id, output, analyze, use_csv):
    """Scrape a OnlyFans list and optionally analyze the results.

    By default, data is stored in SQLite database for historical tracking.
    Use --use-csv for legacy CSV output mode.
    """
    logger = logging.getLogger(__name__)
    logger.info("===== ONLYFANS DEALS FINDER =====")

    # Use provided list_id or default to ALL_LIST
    target_list = list_id or constants.ALL_LIST
    logger.info(f"Scraping list ID: {target_list}")

    # Determine storage mode
    use_database = not use_csv
    storage_mode = "SQLite Database" if use_database else "CSV"
    logger.info(f"Storage mode: {storage_mode}")

    scraper = list_scraper.OnlyFansScraper(
        use_database=use_database,
        db_path=Path(output) if (output and use_database) else None
    )

    try:
        result_path = scraper.scrape_list(target_list)

        # Check if scraping was successful
        if use_csv:
            # Legacy CSV mode checks
            if not os.path.exists(result_path):
                logger.error("CSV file not created. Scraping may have failed.")
                sys.exit(1)

            file_size = os.path.getsize(result_path)
            if file_size < 100:
                logger.warning("CSV file is empty or has no data. Skipping analysis.")
                logger.info(f"Output file: {result_path}")
                sys.exit(0)

            logger.info(f"Scraping successful! Output: {result_path}")

            # Run CSV analysis
            if analyze:
                logger.info("Running analysis...")
                analyser = Analyser(result_path)
                analyser.analyse_list()
            else:
                logger.info("Skipping analysis (--no-analyze flag)")
        else:
            # Database mode
            logger.info(f"Scraping successful! Database: {result_path}")

            # Run database analysis
            if analyze:
                logger.info("Running analysis...")
                db_analyser = DatabaseAnalyser(result_path)
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
@click.argument('csv_file', type=click.Path(exists=True))
@click.pass_context
def analyze(ctx, csv_file):
    """Analyze an existing CSV file from a previous scrape (legacy)."""
    logger = logging.getLogger(__name__)
    logger.info(f"Analyzing {csv_file}...")

    try:
        analyser = Analyser(csv_file)
        analyser.analyse_list()
    except FileNotFoundError:
        logger.error(f"File not found: {csv_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


@cli.command(name='import')
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.option('--list-id', '-l', default='imported', help='List ID to associate with import (default: imported)')
@click.option('--date', type=str, help='Date for import (YYYY-MM-DD format). If not provided, extracts from filename.')
@click.option('--analyze/--no-analyze', default=True, help='Run analysis after import')
@click.pass_context
def import_csv(ctx, csv_file, db_path, list_id, date, analyze):
    """Import data from a CSV file into the database.

    Converts your existing CSV scrapes into the SQLite database format
    for historical tracking and advanced analysis.

    CSV file must have columns: username, price, subscription_status, lists

    Date handling:
    - If --date is not provided, tries to extract from filename (output-YYYY-MM-DD.csv)
    - Use --date YYYY-MM-DD to manually specify the scrape date
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Importing CSV: {csv_file}")

    try:
        from datetime import datetime

        # Parse date if provided
        scraped_at = None
        if date:
            try:
                scraped_at = datetime.strptime(date, '%Y-%m-%d')
                logger.info(f"Using specified date: {date}")
            except ValueError:
                logger.error(f"Invalid date format. Use YYYY-MM-DD (got: {date})")
                sys.exit(1)

        db_path = Path(db_path) if db_path else None
        db = Database(db_path)

        # Import the CSV file
        user_count = db.import_csv(Path(csv_file), list_id, scraped_at=scraped_at)
        logger.info(f"✓ Successfully imported {user_count} users!")

        # Run analysis if requested
        if analyze and user_count > 0:
            logger.info("Running analysis on imported data...")
            analyser = DatabaseAnalyser(db_path)
            analyser.analyse_all()
            analyser.close()
        else:
            logger.info("Skipping analysis (--no-analyze flag)")

        db.close()

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"CSV format error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Import failed: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


@cli.command(name='import-folder')
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.option('--list-id', '-l', default='imported', help='List ID to associate with imports (default: imported)')
@click.option('--pattern', '-p', default='output-*.csv', help='File pattern to match (default: output-*.csv)')
@click.option('--analyze/--no-analyze', default=False, help='Run analysis after importing all files')
@click.pass_context
def import_folder(ctx, folder_path, db_path, list_id, pattern, analyze):
    """Import all CSV files from a folder into the database.

    Bulk imports all matching CSV files from a directory, automatically extracting
    dates from filenames (output-YYYY-MM-DD.csv format).

    By default, imports files matching 'output-*.csv' pattern.
    Use --pattern to specify a different pattern (e.g., '*.csv', 'data-*.csv').
    """
    logger = logging.getLogger(__name__)
    folder_path = Path(folder_path)

    try:
        from glob import glob

        # Find all matching CSV files
        pattern_path = str(folder_path / pattern)
        csv_files = sorted(glob(pattern_path))

        if not csv_files:
            logger.warning(f"No files found matching pattern '{pattern}' in {folder_path}")
            sys.exit(0)

        logger.info(f"Found {len(csv_files)} file(s) to import")

        db_path = Path(db_path) if db_path else None
        db = Database(db_path)

        total_users = 0
        failed_files = []

        for i, csv_file in enumerate(csv_files, 1):
            try:
                logger.info(f"[{i}/{len(csv_files)}] Importing {Path(csv_file).name}...")
                user_count = db.import_csv(Path(csv_file), list_id)
                total_users += user_count
                logger.info(f"  ✓ Imported {user_count} users")
            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                failed_files.append((csv_file, str(e)))
                continue

        logger.info(f"\n{'='*60}")
        logger.info(f"Import Complete!")
        logger.info(f"  Total files: {len(csv_files)}")
        logger.info(f"  Successful: {len(csv_files) - len(failed_files)}")
        logger.info(f"  Failed: {len(failed_files)}")
        logger.info(f"  Total users: {total_users}")
        logger.info(f"{'='*60}\n")

        if failed_files:
            logger.warning("Failed files:")
            for filename, error in failed_files:
                logger.warning(f"  - {Path(filename).name}: {error}")

        # Run analysis if requested
        if analyze:
            logger.info("Running analysis on all imported data...")
            analyser = DatabaseAnalyser(db_path)
            analyser.analyse_all()
            analyser.close()

        db.close()

    except Exception as e:
        logger.error(f"Bulk import failed: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


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
@click.argument('output_csv', type=click.Path())
@click.option('--db-path', '-d', type=click.Path(), help='Path to database file')
@click.pass_context
def export(ctx, output_csv, db_path):
    """Export database to CSV file."""
    logger = logging.getLogger(__name__)

    try:
        db_path = Path(db_path) if db_path else None
        output_path = Path(output_csv)
        analyser = DatabaseAnalyser(db_path)
        analyser.export_csv(output_path)
        analyser.close()
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=ctx.obj.get('verbose', False))
        sys.exit(1)


@cli.command()
def lists():
    """Show configured list IDs from constants.py."""
    click.echo("\nConfigured Lists:")
    click.echo("=" * 50)

    # Get all uppercase attributes from constants module
    list_ids = {name: getattr(constants, name)
                for name in dir(constants)
                if name.isupper() and not name.startswith('_')}

    for name, list_id in sorted(list_ids.items()):
        click.echo(f"  {name:<20} {list_id}")

    click.echo("\nUsage:")
    click.echo(f"  ofscraper scrape --list-id {list(list_ids.values())[0] if list_ids else 'YOUR_LIST_ID'}")
    click.echo()


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
