"""Tests for configuration management."""

import json
from pathlib import Path
import pytest
from wanpc.config import Config
from wanpc.exceptions import PackageCreationError

def test_config_initialization(temp_home):
    """Test config initialization."""
    config = Config()
    assert config.config_dir == temp_home / ".wanpc"
    assert config.config_file == temp_home / ".wanpc" / "config.toml"
    assert config._config == {}

def test_config_load_nonexistent(temp_home):
    """Test loading config when file doesn't exist."""
    config = Config()
    config.load()
    assert config._config == {}

def test_config_save_and_load(temp_config):
    """Test saving and loading config."""
    config = Config()
    test_data = {
        "templates": {
            "test-template": {
                "path": "/path/to/template",
                "description": "Test template",
                "defaults": {"author": "Test Author"}
            }
        },
        "global_defaults": {
            "license": "MIT"
        }
    }
    config._config = test_data
    config._save_config()
    
    # Load in a new instance
    new_config = Config()
    assert new_config._config == test_data

def test_config_save_and_load(temp_config):
    """Test saving and loading configuration."""
    config = Config()
    config._config = {
        "templates": {
            "test": {
                "path": "/test/path",
                "defaults": {"author": "Test Author"}
            }
        },
        "global_defaults": {
            "license": "MIT"
        }
    }
    config._save_config()

    # Load in a new config instance
    new_config = Config()
    assert new_config._config == config._config

def test_config_invalid_toml(temp_config):
    """Test loading invalid TOML config."""
    # Write invalid TOML
    with open(temp_config / "config.toml", "w") as f:
        f.write("invalid [ toml")
    
    with pytest.raises(PackageCreationError):
        config = Config()
        config.load()

def test_get_merged_defaults():
    """Test merging of template and global defaults."""
    config_data = {
        "templates": {
            "test": {
                "defaults": {
                    "author": "Template Author",
                    "license": "Apache"
                }
            }
        },
        "global_defaults": {
            "author": "Global Author",
            "year": "2025",
            "license": "MIT"
        }
    }
    
    # Template defaults should override global defaults
    merged = Config.get_merged_defaults(config_data, "test")
    assert merged["author"] == "Template Author"  # From template
    assert merged["year"] == "2025"  # From global
    assert merged["license"] == "Apache"  # Template overrides global

def test_config_defaults_precedence():
    """Test that template defaults take precedence over global defaults."""
    config_data = {
        "templates": {
            "test": {
                "defaults": {
                    "author": "Template Author",
                    "license": "Apache"
                }
            }
        },
        "global_defaults": {
            "author": "Global Author",
            "license": "MIT",
            "year": "2025"
        }
    }

    merged = Config.get_merged_defaults(config_data, "test")
    assert merged["author"] == "Template Author"  # Template default should win
    assert merged["license"] == "Apache"  # Template default should win
    assert merged["year"] == "2025"  # Only in global defaults

def test_config_missing_sections(temp_config):
    """Test handling of missing config sections."""
    config = Config()
    config._config = {}  # Empty config
    
    # Should not raise errors when accessing missing sections
    templates = config._config.get("templates", {})
    assert isinstance(templates, dict)
    assert len(templates) == 0
    
    global_defaults = config._config.get("global_defaults", {})
    assert isinstance(global_defaults, dict)
    assert len(global_defaults) == 0

def test_config_invalid_template_path(temp_config):
    """Test handling of invalid template paths."""
    config = Config()
    config._config = {
        "templates": {
            "test": {
                "path": "/nonexistent/path",
                "defaults": {}
            }
        }
    }
    config._save_config()
    
    # Should still load without errors
    new_config = Config()
    assert "test" in new_config._config["templates"]
    assert new_config._config["templates"]["test"]["path"] == "/nonexistent/path"

def test_get_merged_defaults_no_template():
    """Test merging defaults when template doesn't exist."""
    config_data = {
        "global_defaults": {
            "author": "Global Author"
        }
    }
    
    with pytest.raises(KeyError):
        Config.get_merged_defaults(config_data, "nonexistent")

def test_config_missing_file(temp_config):
    """Test loading config when file doesn't exist."""
    # Remove config file if it exists
    config_file = temp_config / "config.toml"
    if config_file.exists():
        config_file.unlink()
    
    config = Config()
    assert config._config == {}

def test_config_invalid_path():
    """Test config with invalid path."""
    config = Config()
    config._config = {
        "templates": {
            "test": {
                "path": "/nonexistent/path",
                "defaults": {}
            }
        }
    }
    
    # Should not raise error when getting template path
    template_path = config._config["templates"]["test"]["path"]
    assert template_path == "/nonexistent/path"

def test_config_empty_sections():
    """Test handling of empty config sections."""
    config = Config()
    config._config = {
        "templates": {},
        "global_defaults": {}
    }
    
    # Should handle empty sections gracefully
    templates = config._config["templates"]
    assert isinstance(templates, dict)
    assert len(templates) == 0
    
    global_defaults = config._config["global_defaults"]
    assert isinstance(global_defaults, dict)
    assert len(global_defaults) == 0

def test_config_invalid_template_defaults():
    """Test handling of invalid template defaults."""
    config_data = {
        "templates": {
            "test": {
                "defaults": None  # Invalid defaults
            }
        }
    }
    
    # Should handle invalid defaults gracefully
    merged = Config.get_merged_defaults(config_data, "test")
    assert merged == {}

def test_config_invalid_global_defaults():
    """Test handling of invalid global defaults."""
    config_data = {
        "templates": {
            "test": {
                "defaults": {}
            }
        },
        "global_defaults": None  # Invalid global defaults
    }
    
    # Should handle invalid global defaults gracefully
    merged = Config.get_merged_defaults(config_data, "test")
    assert merged == {}
