"""Command-line interface for OnlyFans Deals Finder."""
import logging
import sys
from pathlib import Path
import os

import click

import constants
import list_scraper
from analyser import Analyser


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
@click.option('--output', '-o', type=click.Path(), help='Output CSV file path')
@click.option('--analyze/--no-analyze', default=True, help='Run analysis after scraping')
@click.pass_context
def scrape(ctx, list_id, output, analyze):
    """Scrape a OnlyFans list and optionally analyze the results."""
    logger = logging.getLogger(__name__)
    logger.info("===== ONLYFANS DEALS FINDER =====")

    # Use provided list_id or default to ALL_LIST
    target_list = list_id or constants.ALL_LIST
    logger.info(f"Scraping list ID: {target_list}")

    scraper = list_scraper.OnlyFansScraper()
    try:
        filename = scraper.scrape_list(target_list)

        # Move output file if custom path specified
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(filename):
                os.rename(filename, output_path)
                filename = output_path
                logger.info(f"Moved output to: {filename}")

        # Check if scraping was successful
        if not os.path.exists(filename):
            logger.error("CSV file not created. Scraping may have failed.")
            sys.exit(1)

        # Check if file has data
        file_size = os.path.getsize(filename)
        if file_size < 100:
            logger.warning("CSV file is empty or has no data. Skipping analysis.")
            logger.info(f"Output file: {filename}")
            sys.exit(0)

        logger.info(f"Scraping successful! Output: {filename}")

        # Run analysis if requested
        if analyze:
            logger.info("Running analysis...")
            analyser = Analyser(filename)
            analyser.analyse_list()
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
    """Analyze an existing CSV file from a previous scrape."""
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
