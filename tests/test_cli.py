"""Tests for CLI functionality."""

from pathlib import Path
import pytest
from typer.testing import CliRunner
from wanpc.cli import app

runner = CliRunner()

def test_list_empty_config(temp_config):
    """Test listing templates when no templates exist."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No templates configured" in result.stdout

def test_config_show_empty(temp_config):
    """Test showing empty configuration."""
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "No configuration found" in result.stdout

def test_config_add_template(temp_config, temp_template):
    """Test adding a template."""
    result = runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template),
        "--description", "Test template"
    ])
    assert result.exit_code == 0
    assert "Added template" in result.stdout

    # Verify template was added
    result = runner.invoke(app, ["list"])
    assert "test-template" in result.stdout
    assert "Test template" in result.stdout

def test_config_set_description(temp_config, temp_template):
    """Test setting template description."""
    # First add a template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Set description
    result = runner.invoke(app, [
        "config", "set-description",
        "--name", "test-template",
        "--description", "Updated description"
    ])
    assert result.exit_code == 0
    assert "Updated description" in result.stdout

    # Verify description was updated
    result = runner.invoke(app, ["list"])
    assert "Updated description" in result.stdout

def test_config_set_default(temp_config, temp_template):
    """Test setting template-specific default."""
    # Add template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Set default
    result = runner.invoke(app, [
        "config", "set-default",
        "--name", "test-template",
        "--key", "author",
        "--value", "Test Author"
    ])
    assert result.exit_code == 0
    
    # Verify default was set
    result = runner.invoke(app, ["list", "--show-defaults"])
    assert "Test Author" in result.stdout

def test_config_set_global_default(temp_config):
    """Test setting global default."""
    result = runner.invoke(app, [
        "config", "set-global-default",
        "--key", "license",
        "--value", "MIT"
    ])
    assert result.exit_code == 0
    
    # Verify global default was set
    result = runner.invoke(app, ["config", "show"])
    assert "MIT" in result.stdout

def test_config_remove_template(temp_config, temp_template):
    """Test removing a template."""
    # Add template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Remove template
    result = runner.invoke(app, [
        "config", "remove-template",
        "--name", "test-template"
    ])
    assert result.exit_code == 0
    assert "Removed template" in result.stdout
    
    # Verify template was removed
    result = runner.invoke(app, ["list"])
    assert "test-template" not in result.stdout

def test_create_project(temp_config, temp_template, tmp_path):
    """Test creating a project from template."""
    # Add template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Create project
    output_dir = tmp_path / "output"
    result = runner.invoke(app, [
        "create",
        "test-template",
        "--output-dir", str(output_dir)
    ])
    assert result.exit_code == 0
    
    # Verify project was created
    assert (output_dir / "My Project").exists()
    assert (output_dir / "My Project" / "README.md").exists()

def test_create_project_invalid_template(temp_config, tmp_path):
    """Test creating a project with non-existent template."""
    result = runner.invoke(app, [
        "create",
        "nonexistent-template",
        "--output-dir", str(tmp_path)
    ])
    assert result.exit_code == 1
    assert "Template 'nonexistent-template' not found" in result.stdout

def test_create_project_invalid_template_path(temp_config, temp_template, tmp_path):
    """Test creating a project with invalid template path."""
    # Add template with invalid path
    result = runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template / "nonexistent")
    ])
    assert result.exit_code == 1
    assert "Error: Template path does not exist" in result.stdout

def test_create_project_with_defaults(temp_config, temp_template, tmp_path):
    """Test creating a project with template and global defaults."""
    # Add template with defaults
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Set template-specific default
    runner.invoke(app, [
        "config", "set-default",
        "--name", "test-template",
        "--key", "author",
        "--value", "Template Author"
    ])
    
    # Set global default
    runner.invoke(app, [
        "config", "set-global-default",
        "--key", "license",
        "--value", "MIT"
    ])
    
    # Create project
    output_dir = tmp_path / "output"
    result = runner.invoke(app, [
        "create",
        "test-template",
        "--output-dir", str(output_dir)
    ])
    assert result.exit_code == 0
    
    # Verify defaults were used
    readme_path = output_dir / "My Project" / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text()
    assert "Template Author" in content  # Template default was used

def test_create_project_no_defaults(temp_config, temp_template, tmp_path):
    """Test creating a project without using defaults."""
    # Add template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Set some defaults that should be ignored
    runner.invoke(app, [
        "config", "set-default",
        "--name", "test-template",
        "--key", "author",
        "--value", "Template Author"
    ])
    
    # Create project with --no-defaults
    output_dir = tmp_path / "output"
    result = runner.invoke(app, [
        "create",
        "test-template",
        "--output-dir", str(output_dir),
        "--no-defaults"
    ])
    assert result.exit_code == 0
    
    # Verify cookiecutter defaults were used instead of config defaults
    readme_path = output_dir / "My Project" / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text()
    assert "John Doe" in content  # Default from cookiecutter.json was used

def test_create_project_existing_output_dir(temp_config, temp_template, tmp_path):
    """Test creating a project in an existing output directory."""
    # Add template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Create output directory with some content
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "existing.txt").write_text("existing content")
    
    # Create project
    result = runner.invoke(app, [
        "create",
        "test-template",
        "--output-dir", str(output_dir)
    ])
    assert result.exit_code == 0
    
    # Verify both the new project and existing content exist
    assert (output_dir / "existing.txt").exists()
    assert (output_dir / "My Project").exists()
    assert (output_dir / "My Project" / "README.md").exists()

def test_create_project_with_command_line_overrides(temp_config, temp_template, tmp_path):
    """Test creating a project with command line overrides that take precedence over defaults."""
    # Add template with defaults
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    # Set template-specific default
    runner.invoke(app, [
        "config", "set-default",
        "--name", "test-template",
        "--key", "author",
        "--value", "Template Author"
    ])
    
    # Set global default
    runner.invoke(app, [
        "config", "set-global-default",
        "--key", "license",
        "--value", "MIT"
    ])
    
    # Create project with command line overrides
    output_dir = tmp_path / "output"
    result = runner.invoke(app, [
        "create",
        "test-template",
        "--output-dir", str(output_dir),
        "--author", "Command Line Author",  # This should override template default
        "--license", "GPL"  # This should override global default
    ])
    assert result.exit_code == 0
    
    # Verify overrides were used instead of defaults
    readme_path = output_dir / "My Project" / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text()
    assert "Command Line Author" in content  # Command line override was used
    assert "Template Author" not in content  # Template default was not used
    assert "GPL" in content  # Command line override was used
    assert "MIT" not in content  # Global default was not used

def test_help_text():
    """Test help text formatting."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "Commands:" in result.stdout

def test_config_help():
    """Test config command help text."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "ACTION" in result.stdout  # The command expects an ACTION argument

def test_remove_nonexistent_template(temp_config):
    """Test removing a template that doesn't exist."""
    result = runner.invoke(app, [
        "config", "remove-template",
        "--name", "nonexistent"
    ])
    assert result.exit_code == 1
    assert "Template 'nonexistent' not found" in result.stdout

def test_remove_nonexistent_default(temp_config, temp_template):
    """Test removing a default that doesn't exist."""
    # Add template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    result = runner.invoke(app, [
        "config", "remove-default",
        "--name", "test-template",
        "--key", "nonexistent"
    ])
    assert result.exit_code == 1
    assert "Default 'nonexistent' not found" in result.stdout

def test_remove_nonexistent_global_default(temp_config):
    """Test removing a global default that doesn't exist."""
    result = runner.invoke(app, [
        "config", "remove-global-default",
        "--key", "nonexistent"
    ])
    assert result.exit_code == 1
    assert "Global default 'nonexistent' not found" in result.stdout

def test_set_invalid_default(temp_config, temp_template):
    """Test setting a default for a key that doesn't exist in cookiecutter.json."""
    # Add template
    runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", str(temp_template)
    ])
    
    result = runner.invoke(app, [
        "config", "set-default",
        "--name", "test-template",
        "--key", "invalid_key",
        "--value", "value"
    ])
    assert result.exit_code == 1
    assert "Key 'invalid_key' not found in cookiecutter.json" in result.stdout

def test_config_add_template_interactive(temp_config, temp_template):
    """Test adding a template in interactive mode."""
    # Simulate interactive input for name, path, and description
    result = runner.invoke(
        app,
        ["config", "add-template"],
        input=f"test-template\n{temp_template}\nTest Description\n"
    )
    assert result.exit_code == 0
    assert "Added template 'test-template'" in result.stdout
    assert "Description: Test Description" in result.stdout

    # Verify template was added with correct values
    result = runner.invoke(app, ["list"])
    assert "test-template" in result.stdout
    assert "Test Description" in result.stdout

def test_config_add_template_interactive_partial(temp_config, temp_template):
    """Test adding a template with some values provided via CLI and others via interactive input."""
    result = runner.invoke(
        app,
        ["config", "add-template", "--name", "test-template"],
        input=f"{temp_template}\nTest Description\n"
    )
    assert result.exit_code == 0
    assert "Added template 'test-template'" in result.stdout
    assert "Description: Test Description" in result.stdout

    # Verify template was added with correct values
    result = runner.invoke(app, ["list"])
    assert "test-template" in result.stdout
    assert "Test Description" in result.stdout

def test_config_add_template_relative_path(temp_config, temp_template, monkeypatch):
    """Test adding a template using a relative path."""
    # Set up a fake current working directory
    fake_cwd = temp_template.parent
    monkeypatch.setattr(Path, "cwd", lambda: fake_cwd)

    # Use relative path (just the template directory name)
    relative_path = temp_template.name

    result = runner.invoke(app, [
        "config", "add-template",
        "--name", "test-template",
        "--path", relative_path,
        "--description", "Test template"
    ])
    assert result.exit_code == 0
    assert "Added template" in result.stdout

    # Verify template was added with absolute path
    result = runner.invoke(app, ["config", "show"])
    config_output = result.stdout
    assert str(temp_template.resolve()) in config_output  # Should show absolute path
    assert "test-template" in config_output

def test_config_add_template_relative_path_interactive(temp_config, temp_template, monkeypatch):
    """Test adding a template using a relative path in interactive mode."""
    # Set up a fake current working directory
    fake_cwd = temp_template.parent
    monkeypatch.setattr(Path, "cwd", lambda: fake_cwd)

    # Use relative path in interactive input
    relative_path = temp_template.name
    result = runner.invoke(
        app,
        ["config", "add-template"],
        input=f"test-template\n{relative_path}\nTest Description\n"
    )
    assert result.exit_code == 0
    assert "Added template" in result.stdout

    # Verify template was added with absolute path
    result = runner.invoke(app, ["config", "show"])
    config_output = result.stdout
    assert str(temp_template.resolve()) in config_output  # Should show absolute path
    assert "test-template" in config_output
