"""Configuration management for wanpc."""

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import toml

from .exceptions import PackageCreationError
from .logger import get_logger

logger = get_logger()


class Config:
    """Handle wanpc configuration."""

    def __init__(self):
        """Initialize the configuration."""
        self.config_dir = Path.home() / ".wanpc"
        self.config_file = self.config_dir / "config.toml"
        self._config: Dict[str, Any] = {}
        self._load_config()

    def load(self) -> None:
        """Load configuration from file."""
        self._load_config()

    def _load_config(self) -> None:
        """
        Load configuration from file.

        Raises:
            PackageCreationError: If config file exists but cannot be loaded
        """
        if self.config_file.exists():
            try:
                self._config = toml.load(self.config_file)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                raise PackageCreationError(f"Failed to load config file: {e}")

    def _save_config(self) -> None:
        """
        Save configuration to file.

        Raises:
            PackageCreationError: If config cannot be saved
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                toml.dump(self._config, f)
        except Exception as e:
            logger.error(f"Failed to save config file: {e}")
            raise PackageCreationError(f"Failed to save config file: {e}")

    @property
    def default_author(self) -> Optional[str]:
        """Get the default author name."""
        return self._config.get("user", {}).get("name")

    @default_author.setter
    def default_author(self, value: str) -> None:
        """Set the default author name."""
        if "user" not in self._config:
            self._config["user"] = {}
        self._config["user"]["name"] = value
        self._save_config()

    @property
    def default_email(self) -> Optional[str]:
        """Get the default author email."""
        return self._config.get("user", {}).get("email")

    @default_email.setter
    def default_email(self, value: str) -> None:
        """Set the default author email."""
        if "user" not in self._config:
            self._config["user"] = {}
        self._config["user"]["email"] = value
        self._save_config()

    @staticmethod
    def get_merged_defaults(config_data: Dict[str, Any], template_name: str) -> Dict[str, Any]:
        """
        Get merged defaults, with template defaults taking precedence over global defaults.

        Args:
            config_data: Configuration data dictionary
            template_name: Name of the template

        Returns:
            Dictionary of merged defaults

        Raises:
            KeyError: If template doesn't exist in config
        """
        if template_name not in config_data.get("templates", {}):
            raise KeyError(f"Template '{template_name}' not found in config")

        # Start with global defaults
        global_defaults = config_data.get("global_defaults", {})
        if not isinstance(global_defaults, dict):
            global_defaults = {}
        merged = global_defaults.copy()

        # Override with template-specific defaults
        template_defaults = config_data["templates"][template_name].get("defaults", {})
        if not isinstance(template_defaults, dict):
            template_defaults = {}
        merged.update(template_defaults)

        return merged

    def get_git_config(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get user name and email from git config.

        Returns:
            Tuple of (name, email) from git config, or (None, None) if not found
        """
        try:
            name = subprocess.run(
                ["git", "config", "--get", "user.name"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()

            email = subprocess.run(
                ["git", "config", "--get", "user.email"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()

            return name or None, email or None

        except Exception as e:
            logger.warning(f"Failed to get git config: {e}")
            return None, None


def load_config() -> Dict[str, Any]:
    """Load and return the configuration."""
    config = Config()
    if not config._config:
        # Create default config if none exists
        config._config = {
            "templates": {},
            "global_defaults": {}
        }
        config._save_config()
    return config._config

def save_config(cfg: Dict[str, Any]) -> None:
    """Save the configuration."""
    config = Config()
    # Ensure structure exists
    if "templates" not in cfg:
        cfg["templates"] = {}
    if "global_defaults" not in cfg:
        cfg["global_defaults"] = {}
    config._config = cfg
    config._save_config()

def get_merged_defaults(cfg: Dict[str, Any], template_name: str) -> Dict[str, Any]:
    """Get merged defaults, with template defaults taking precedence over global defaults."""
    global_defaults = cfg.get("global_defaults", {})
    template_defaults = cfg.get("templates", {}).get(template_name, {}).get("defaults", {})
    
    # Start with global defaults
    merged = global_defaults.copy()
    # Update with template defaults (these take precedence)
    merged.update(template_defaults)
    
    return merged
