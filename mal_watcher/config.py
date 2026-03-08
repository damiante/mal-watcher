"""Configuration management for MAL Watcher."""

import os
import yaml
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration."""

    def __init__(self, config_file: str = "config.yaml", environment: str = "env-prod"):
        """
        Initialize configuration.

        Args:
            config_file: Path to the configuration YAML file
            environment: Environment to load from config file (env-prod or env-dev)
        """
        self.mal_client_id: str = ""
        self.search_frequency_minutes: int = 60
        self.tracked_users_file: str = "./tracked_users"
        self.sonarr_url: str = ""
        self.sonarr_api_key: str = ""
        self.log_level: str = "INFO"

        # Load from config file if it exists
        config_path = Path(config_file)
        if config_path.exists():
            self._load_from_yaml(config_path, environment)

        # Override with environment variables (for Docker)
        self._load_from_env()

        # Validate required fields
        self._validate()

    def _load_from_yaml(self, config_path: Path, environment: str):
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if environment in config_data:
            env_config = config_data[environment]
            for item in env_config:
                name = item.get('name')
                value = item.get('value')

                if name == 'X-MAL-CLIENT-ID':
                    self.mal_client_id = value
                elif name == 'SEARCH_FREQUENCY_MINUTES':
                    self.search_frequency_minutes = int(value)
                elif name == 'MAL_TRACKED_USERS_FILE':
                    self.tracked_users_file = value
                elif name == 'SONARR_URL':
                    self.sonarr_url = value
                elif name == 'SONARR_API_KEY':
                    self.sonarr_api_key = value
                elif name == 'LOG_LEVEL':
                    self.log_level = value.upper()

    def _load_from_env(self):
        """Load configuration from environment variables."""
        if os.getenv('X_MAL_CLIENT_ID'):
            self.mal_client_id = os.getenv('X_MAL_CLIENT_ID')
        if os.getenv('SEARCH_FREQUENCY_MINUTES'):
            self.search_frequency_minutes = int(os.getenv('SEARCH_FREQUENCY_MINUTES'))
        if os.getenv('MAL_TRACKED_USERS_FILE'):
            self.tracked_users_file = os.getenv('MAL_TRACKED_USERS_FILE')
        if os.getenv('SONARR_URL'):
            self.sonarr_url = os.getenv('SONARR_URL')
        if os.getenv('SONARR_API_KEY'):
            self.sonarr_api_key = os.getenv('SONARR_API_KEY')
        if os.getenv('LOG_LEVEL'):
            self.log_level = os.getenv('LOG_LEVEL').upper()

    def _validate(self):
        """Validate required configuration fields."""
        if not self.mal_client_id:
            raise ValueError("MAL Client ID is required (X-MAL-CLIENT-ID)")
        if not self.sonarr_url or self.sonarr_url == "<TODO>":
            raise ValueError("Sonarr URL is required (SONARR_URL)")
        if not self.sonarr_api_key or self.sonarr_api_key == "<TODO>":
            raise ValueError("Sonarr API Key is required (SONARR_API_KEY)")

    def get_tracked_users(self) -> list[str]:
        """
        Read and return the list of tracked users.

        Returns:
            List of usernames to track
        """
        users_path = Path(self.tracked_users_file)
        if not users_path.exists():
            return []

        with open(users_path, 'r') as f:
            users = [line.strip() for line in f if line.strip()]

        return users
