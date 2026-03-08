#!/usr/bin/env python3
"""
MAL Watcher - MyAnimeList to Sonarr synchronization service.

This service synchronizes anime from MyAnimeList user lists to Sonarr,
automatically adding TV anime that users are watching or plan to watch.
"""

import argparse
import logging
import time
import sys
from pathlib import Path

from mal_watcher.config import Config
from mal_watcher.mal_client import MALClient
from mal_watcher.sonarr_client import SonarrClient
from mal_watcher.sync import MalWatcherSync
from mal_watcher.utils import setup_logging

logger = logging.getLogger(__name__)


def run_sync(config: Config) -> bool:
    """
    Run a single sync cycle.

    Args:
        config: Application configuration

    Returns:
        True if sync completed successfully, False otherwise
    """
    try:
        # Get tracked users
        tracked_users = config.get_tracked_users()

        if not tracked_users:
            logger.warning("No tracked users found. Please add users to tracked_users file.")
            return False

        logger.info(f"Found {len(tracked_users)} tracked users: {', '.join(tracked_users)}")

        # Initialize clients
        mal_client = MALClient(config.mal_client_id)
        sonarr_client = SonarrClient(config.sonarr_url, config.sonarr_api_key)

        # Initialize sync handler
        sync_handler = MalWatcherSync(
            mal_client,
            sonarr_client,
            sonarr_root_folder=config.sonarr_root_folder,
            sonarr_quality_profile_id=config.sonarr_quality_profile_id
        )

        # Run sync
        stats = sync_handler.sync_all_users(tracked_users)

        logger.info("=" * 60)
        logger.info("Sync Summary:")
        logger.info(f"  Users synced: {stats['users_synced']}")
        logger.info(f"  Total anime processed: {stats['total_anime']}")
        logger.info(f"  TV anime found: {stats['tv_anime']}")
        logger.info(f"  Already in Sonarr: {stats['already_in_sonarr']}")
        logger.info(f"  Added to Sonarr: {stats['added_to_sonarr']}")
        logger.info(f"  Failed to add: {stats['failed_to_add']}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"Error during sync: {e}", exc_info=True)
        return False


def run_daemon(config: Config):
    """
    Run the service in daemon mode.

    Args:
        config: Application configuration
    """
    logger.info("Starting MAL Watcher in daemon mode")
    logger.info(f"Sync frequency: {config.search_frequency_minutes} minutes")

    while True:
        try:
            logger.info("Starting sync cycle")
            run_sync(config)

            # Sleep until next sync
            sleep_seconds = config.search_frequency_minutes * 60
            logger.info(f"Sync cycle complete. Sleeping for {config.search_frequency_minutes} minutes")
            time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Shutting down gracefully...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in daemon loop: {e}", exc_info=True)
            logger.info("Sleeping for 5 minutes before retry...")
            time.sleep(300)  # Sleep 5 minutes on error


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MAL Watcher - Sync MyAnimeList to Sonarr",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once and exit
  python main.py --manual

  # Run in daemon mode (default)
  python main.py

  # Run with custom config file
  python main.py --config /path/to/config.yaml

  # Run with debug logging
  python main.py --log-level DEBUG
        """
    )

    parser.add_argument(
        "--manual",
        action="store_true",
        help="Run once and exit (default: daemon mode)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )

    parser.add_argument(
        "--environment",
        type=str,
        default="env-prod",
        choices=["env-prod", "env-dev"],
        help="Environment to load from config file (default: env-prod)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level from config"
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = Config(config_file=args.config, environment=args.environment)

        # Override log level if specified
        if args.log_level:
            config.log_level = args.log_level

        # Setup logging
        setup_logging(config.log_level)

        logger.info("=" * 60)
        logger.info("MAL Watcher - MyAnimeList to Sonarr Sync")
        logger.info("=" * 60)
        logger.info(f"Configuration loaded from: {args.config}")
        logger.info(f"Environment: {args.environment}")
        logger.info(f"Log level: {config.log_level}")
        logger.info(f"Mode: {'Manual (run once)' if args.manual else 'Daemon'}")

        # Run in appropriate mode
        if args.manual:
            success = run_sync(config)
            sys.exit(0 if success else 1)
        else:
            run_daemon(config)

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
