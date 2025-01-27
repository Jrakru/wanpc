"""Test fixtures for wanpc."""

import json
import shutil
from pathlib import Path
import pytest
from rich.console import Console

@pytest.fixture
def temp_home(tmp_path):
    """Create a temporary home directory for tests."""
    old_home = Path.home()
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    Path.home = lambda: home_dir
    yield home_dir
    Path.home = lambda: old_home

@pytest.fixture
def temp_config(temp_home):
    """Create a temporary config directory."""
    config_dir = temp_home / ".wanpc"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def temp_template(tmp_path):
    """Create a temporary cookiecutter template."""
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    
    # Create cookiecutter.json
    cookiecutter_json = {
        "project_name": "My Project",
        "author": "John Doe",
        "email": "john@example.com",
        "license": "MIT"
    }
    
    with open(template_dir / "cookiecutter.json", "w") as f:
        json.dump(cookiecutter_json, f, indent=2)
    
    # Create template structure
    (template_dir / "{{cookiecutter.project_name}}").mkdir()
    with open(template_dir / "{{cookiecutter.project_name}}" / "README.md", "w") as f:
        f.write("# {{cookiecutter.project_name}}\n\nBy {{cookiecutter.author}}")
    
    return template_dir

@pytest.fixture
def console():
    """Create a Rich console for testing."""
    return Console()
