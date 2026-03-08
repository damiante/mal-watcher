"""Sonarr API client."""

import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SonarrClient:
    """Client for interacting with the Sonarr API."""

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Sonarr API client.

        Args:
            base_url: Sonarr server URL (e.g., http://localhost:8989)
            api_key: Sonarr API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }

    def get_all_series(self) -> List[Dict[str, Any]]:
        """
        Get all series currently in Sonarr.

        Returns:
            List of series dictionaries
        """
        url = f"{self.base_url}/api/v3/series"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            series_list = response.json()
            logger.info(f"Retrieved {len(series_list)} series from Sonarr")
            return series_list

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching series from Sonarr: {e}")
            return []

    def lookup_series(self, title: str) -> List[Dict[str, Any]]:
        """
        Search for a series in Sonarr's lookup.

        Args:
            title: Series title to search for

        Returns:
            List of matching series from lookup
        """
        url = f"{self.base_url}/api/v3/series/lookup"
        params = {"term": title}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            results = response.json()
            logger.debug(f"Lookup for '{title}' returned {len(results)} results")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Error looking up series '{title}': {e}")
            return []

    def add_series(
        self,
        series_data: Dict[str, Any],
        root_folder_path: str = "/tv",
        quality_profile_id: int = 1,
        monitor: str = "all",
        search_on_add: bool = True,
        mal_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a series to Sonarr.

        Args:
            series_data: Series data from lookup
            root_folder_path: Root folder where series will be stored
            quality_profile_id: Quality profile ID to use
            monitor: Monitoring mode (all, future, missing, existing, firstSeason, latestSeason, none)
            search_on_add: Whether to search for episodes immediately
            mal_id: MyAnimeList ID to tag the series with

        Returns:
            Added series data, or None if failed
        """
        url = f"{self.base_url}/api/v3/series"

        # Prepare the series data for adding
        payload = {
            "title": series_data.get("title"),
            "qualityProfileId": quality_profile_id,
            "titleSlug": series_data.get("titleSlug"),
            "images": series_data.get("images", []),
            "seasons": series_data.get("seasons", []),
            "path": f"{root_folder_path}/{series_data.get('title', '').replace('/', '_')}",
            "rootFolderPath": root_folder_path,
            "monitored": True,
            "tvdbId": series_data.get("tvdbId"),
            "addOptions": {
                "monitor": monitor,
                "searchForMissingEpisodes": search_on_add,
                "searchForCutoffUnmetEpisodes": False
            }
        }

        # Add MAL ID as a tag if provided
        if mal_id:
            payload["tags"] = [f"mal-{mal_id}"]

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            added_series = response.json()
            logger.info(f"Successfully added series: {added_series.get('title')}")
            return added_series

        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding series '{series_data.get('title')}': {e}")
            if hasattr(e.response, 'text'):
                logger.debug(f"Response: {e.response.text}")
            return None

    def get_root_folders(self) -> List[Dict[str, Any]]:
        """
        Get all root folders configured in Sonarr.

        Returns:
            List of root folder dictionaries
        """
        url = f"{self.base_url}/api/v3/rootfolder"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            root_folders = response.json()
            logger.debug(f"Retrieved {len(root_folders)} root folders")
            return root_folders

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching root folders: {e}")
            return []

    def get_quality_profiles(self) -> List[Dict[str, Any]]:
        """
        Get all quality profiles configured in Sonarr.

        Returns:
            List of quality profile dictionaries
        """
        url = f"{self.base_url}/api/v3/qualityprofile"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            profiles = response.json()
            logger.debug(f"Retrieved {len(profiles)} quality profiles")
            return profiles

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching quality profiles: {e}")
            return []
