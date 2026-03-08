"""MyAnimeList API client."""

import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MALClient:
    """Client for interacting with the MyAnimeList API."""

    BASE_URL = "https://api.myanimelist.net/v2"

    def __init__(self, client_id: str):
        """
        Initialize MAL API client.

        Args:
            client_id: MAL API client ID
        """
        self.client_id = client_id
        self.headers = {
            "X-MAL-CLIENT-ID": client_id
        }

    def get_user_anime_list(
        self,
        username: str,
        statuses: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get anime list for a user with specified statuses.

        Args:
            username: MAL username
            statuses: List of statuses to filter by (watching, plan_to_watch, on_hold, completed, dropped)
            limit: Number of results per page (max 100)

        Returns:
            List of anime entries with their list status
        """
        if statuses is None:
            statuses = ["watching", "plan_to_watch", "on_hold"]

        all_anime = []

        for status in statuses:
            logger.debug(f"Fetching {status} anime for user {username}")
            anime_list = self._get_user_anime_by_status(username, status, limit)
            all_anime.extend(anime_list)
            logger.info(f"Found {len(anime_list)} anime with status '{status}' for user {username}")

        logger.info(f"Total anime found for user {username}: {len(all_anime)}")
        return all_anime

    def _get_user_anime_by_status(
        self,
        username: str,
        status: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all anime for a user with a specific status, handling pagination.

        Args:
            username: MAL username
            status: Status to filter by
            limit: Number of results per page

        Returns:
            List of anime entries
        """
        anime_list = []
        url = f"{self.BASE_URL}/users/{username}/animelist"
        params = {
            "status": status,
            "fields": "list_status",
            "limit": limit,
            "offset": 0
        }

        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params if params else None)
                response.raise_for_status()
                data = response.json()

                anime_list.extend(data.get("data", []))

                # Check for next page
                paging = data.get("paging", {})
                url = paging.get("next")
                params = None  # Next URL already contains params

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching anime list for user {username} with status {status}: {e}")
                break

        return anime_list

    def get_anime_details(self, anime_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an anime.

        Args:
            anime_id: MAL anime ID

        Returns:
            Anime details dictionary, or None if request fails
        """
        url = f"{self.BASE_URL}/anime/{anime_id}"
        params = {
            "fields": "id,title,alternative_titles,media_type,num_episodes,status,studios"
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            anime_data = response.json()
            logger.debug(f"Fetched details for anime ID {anime_id}: {anime_data.get('title')}")
            return anime_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching anime details for ID {anime_id}: {e}")
            return None

    def is_tv_anime(self, anime_details: Dict[str, Any]) -> bool:
        """
        Check if an anime is a TV series.

        Args:
            anime_details: Anime details dictionary

        Returns:
            True if media_type is "tv", False otherwise
        """
        return anime_details.get("media_type") == "tv"
