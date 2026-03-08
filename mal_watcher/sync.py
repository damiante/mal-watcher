"""Main synchronization logic for MAL Watcher."""

import logging
from typing import List, Dict, Any, Set

from .mal_client import MALClient
from .sonarr_client import SonarrClient
from .utils import find_matching_series, get_all_anime_titles, find_best_lookup_match

logger = logging.getLogger(__name__)


class MalWatcherSync:
    """Handles synchronization between MyAnimeList and Sonarr."""

    def __init__(self, mal_client: MALClient, sonarr_client: SonarrClient):
        """
        Initialize the sync handler.

        Args:
            mal_client: MAL API client
            sonarr_client: Sonarr API client
        """
        self.mal_client = mal_client
        self.sonarr_client = sonarr_client

    def sync_user(self, username: str) -> Dict[str, int]:
        """
        Sync anime list for a single user.

        Args:
            username: MAL username to sync

        Returns:
            Dictionary with sync statistics
        """
        logger.info(f"Starting sync for user: {username}")

        stats = {
            "total_anime": 0,
            "tv_anime": 0,
            "already_in_sonarr": 0,
            "added_to_sonarr": 0,
            "failed_to_add": 0,
            "not_found_in_lookup": 0
        }

        # Get user's anime list
        anime_list = self.mal_client.get_user_anime_list(
            username,
            statuses=["watching", "plan_to_watch", "on_hold"]
        )
        stats["total_anime"] = len(anime_list)

        if not anime_list:
            logger.warning(f"No anime found for user {username}")
            return stats

        # Get all series currently in Sonarr
        sonarr_series = self.sonarr_client.get_all_series()
        logger.info(f"Currently tracking {len(sonarr_series)} series in Sonarr")

        # Get root folder and quality profile for adding series
        root_folders = self.sonarr_client.get_root_folders()
        quality_profiles = self.sonarr_client.get_quality_profiles()

        if not root_folders:
            logger.error("No root folders configured in Sonarr. Cannot add series.")
            return stats

        if not quality_profiles:
            logger.error("No quality profiles configured in Sonarr. Cannot add series.")
            return stats

        root_folder_path = root_folders[0].get("path", "/tv")
        quality_profile_id = quality_profiles[0].get("id", 1)

        # Process each anime
        for anime_entry in anime_list:
            anime_node = anime_entry.get("node", {})
            anime_id = anime_node.get("id")
            anime_title = anime_node.get("title")

            logger.debug(f"Processing anime: {anime_title} (ID: {anime_id})")

            # Get detailed information
            anime_details = self.mal_client.get_anime_details(anime_id)
            if not anime_details:
                logger.warning(f"Could not fetch details for anime ID {anime_id}")
                continue

            # Check if it's a TV anime
            if not self.mal_client.is_tv_anime(anime_details):
                logger.debug(f"Skipping non-TV anime: {anime_title} (type: {anime_details.get('media_type')})")
                continue

            stats["tv_anime"] += 1

            # Check if already in Sonarr
            if self._is_anime_in_sonarr(anime_details, sonarr_series):
                logger.debug(f"Anime already in Sonarr: {anime_title}")
                stats["already_in_sonarr"] += 1
                continue

            # Try to add to Sonarr
            if self._add_anime_to_sonarr(
                anime_details,
                root_folder_path,
                quality_profile_id
            ):
                stats["added_to_sonarr"] += 1
            else:
                stats["failed_to_add"] += 1

        logger.info(f"Sync completed for user {username}: {stats}")
        return stats

    def sync_all_users(self, usernames: List[str]) -> Dict[str, Any]:
        """
        Sync anime lists for all tracked users.

        Args:
            usernames: List of MAL usernames

        Returns:
            Dictionary with overall sync statistics
        """
        logger.info(f"Starting sync for {len(usernames)} users")

        overall_stats = {
            "users_synced": 0,
            "total_anime": 0,
            "tv_anime": 0,
            "already_in_sonarr": 0,
            "added_to_sonarr": 0,
            "failed_to_add": 0,
            "not_found_in_lookup": 0
        }

        for username in usernames:
            try:
                user_stats = self.sync_user(username)
                overall_stats["users_synced"] += 1

                # Aggregate stats
                for key in ["total_anime", "tv_anime", "already_in_sonarr",
                           "added_to_sonarr", "failed_to_add", "not_found_in_lookup"]:
                    overall_stats[key] += user_stats.get(key, 0)

            except Exception as e:
                logger.error(f"Error syncing user {username}: {e}", exc_info=True)

        logger.info(f"Overall sync completed: {overall_stats}")
        return overall_stats

    def _is_anime_in_sonarr(
        self,
        anime_details: Dict[str, Any],
        sonarr_series: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if an anime is already tracked in Sonarr.

        Args:
            anime_details: Anime details from MAL
            sonarr_series: List of series from Sonarr

        Returns:
            True if anime is already in Sonarr, False otherwise
        """
        anime_titles = get_all_anime_titles(anime_details)
        anime_id = anime_details.get("id")

        for anime_title in anime_titles:
            match = find_matching_series(anime_title, sonarr_series, threshold=0.85)
            if match:
                return True

        # Also check for MAL ID tag
        for series in sonarr_series:
            tags = series.get("tags", [])
            if f"mal-{anime_id}" in [str(tag) for tag in tags]:
                return True

        return False

    def _add_anime_to_sonarr(
        self,
        anime_details: Dict[str, Any],
        root_folder_path: str,
        quality_profile_id: int
    ) -> bool:
        """
        Add an anime to Sonarr.

        Args:
            anime_details: Anime details from MAL
            root_folder_path: Root folder path in Sonarr
            quality_profile_id: Quality profile ID to use

        Returns:
            True if successfully added, False otherwise
        """
        anime_title = anime_details.get("title")
        anime_id = anime_details.get("id")

        # Try all title variations for lookup
        anime_titles = get_all_anime_titles(anime_details)

        for title_to_search in anime_titles:
            logger.debug(f"Looking up '{title_to_search}' in Sonarr")
            lookup_results = self.sonarr_client.lookup_series(title_to_search)

            if not lookup_results:
                continue

            # Find best match
            best_match = find_best_lookup_match(anime_details, lookup_results, threshold=0.7)

            if best_match:
                logger.info(f"Found match in Sonarr lookup: {best_match.get('title')} for MAL anime: {anime_title}")

                # Add the series
                added = self.sonarr_client.add_series(
                    best_match,
                    root_folder_path=root_folder_path,
                    quality_profile_id=quality_profile_id,
                    monitor="all",
                    search_on_add=True,
                    mal_id=anime_id
                )

                if added:
                    logger.info(f"Successfully added {anime_title} to Sonarr")
                    return True
                else:
                    logger.error(f"Failed to add {anime_title} to Sonarr")
                    return False

        logger.warning(f"Could not find {anime_title} in Sonarr lookup")
        return False
