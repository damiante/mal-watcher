"""Utility functions for MAL Watcher."""

import logging
import sys
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional


def setup_logging(log_level: str = "INFO"):
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Convert string to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from requests library
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def similarity_ratio(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def find_matching_series(
    anime_title: str,
    sonarr_series_list: List[Dict[str, Any]],
    threshold: float = 0.8
) -> Optional[Dict[str, Any]]:
    """
    Find a matching series in Sonarr's series list.

    Args:
        anime_title: Anime title to match
        sonarr_series_list: List of series from Sonarr
        threshold: Minimum similarity threshold (0.0-1.0)

    Returns:
        Matching series dict if found, None otherwise
    """
    best_match = None
    best_score = 0.0

    for series in sonarr_series_list:
        series_title = series.get("title", "")

        # Check main title
        score = similarity_ratio(anime_title, series_title)

        # Check alternative titles if available
        alt_titles = series.get("alternateTitles", [])
        for alt in alt_titles:
            alt_title = alt.get("title", "")
            alt_score = similarity_ratio(anime_title, alt_title)
            score = max(score, alt_score)

        if score > best_score:
            best_score = score
            best_match = series

    if best_score >= threshold:
        return best_match

    return None


def get_all_anime_titles(anime_details: Dict[str, Any]) -> List[str]:
    """
    Extract all title variations from anime details.

    Args:
        anime_details: Anime details from MAL API

    Returns:
        List of all title variations
    """
    titles = []

    # Main title
    main_title = anime_details.get("title")
    if main_title:
        titles.append(main_title)

    # Alternative titles
    alt_titles = anime_details.get("alternative_titles", {})
    if alt_titles.get("en"):
        titles.append(alt_titles["en"])
    if alt_titles.get("ja"):
        titles.append(alt_titles["ja"])

    for synonym in alt_titles.get("synonyms", []):
        titles.append(synonym)

    return titles


def find_best_lookup_match(
    anime_details: Dict[str, Any],
    lookup_results: List[Dict[str, Any]],
    threshold: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Find the best match from Sonarr lookup results for an anime.

    Args:
        anime_details: Anime details from MAL API
        lookup_results: Results from Sonarr series lookup
        threshold: Minimum similarity threshold

    Returns:
        Best matching series from lookup, or None
    """
    if not lookup_results:
        return None

    anime_titles = get_all_anime_titles(anime_details)
    best_match = None
    best_score = 0.0

    for result in lookup_results:
        result_title = result.get("title", "")

        for anime_title in anime_titles:
            score = similarity_ratio(anime_title, result_title)

            if score > best_score:
                best_score = score
                best_match = result

    if best_score >= threshold:
        return best_match

    return None
