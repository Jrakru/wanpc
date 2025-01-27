# wanpc

A wrapper around cookiecutter for easy project templating.

## Description

`wanpc` (Wan Python Package Creator) is a command-line tool that simplifies project creation using cookiecutter templates. It provides template management, default values, and a user-friendly interface for creating new projects.

## Features

- **Template Management**: Add, remove, and list cookiecutter templates
- **Default Values**: Set defaults at both template and global levels
- **Interactive Mode**: User-friendly prompts for all operations
- **Rich Output**: Colorful and well-formatted terminal output
- **Template Descriptions**: Document your templates for easy reference

## Installation

Install using pipx (recommended):
```bash
pipx install wanpc
```

Or using pip:
```bash
pip install wanpc
```

## Quick Start

1. Add a template:
```bash
wanpc config add-template --name python-pkg --path ~/templates/python
# Or use interactive mode:
wanpc config add-template
```

2. Set some defaults:
```bash
# Set template-specific defaults
wanpc config set-default --name python-pkg --key author --value "Your Name"

# Set global defaults (applied to all templates unless overridden)
wanpc config set-global-default --key license --value MIT
```

3. Create a project:
```bash
wanpc create python-pkg --output-dir ~/projects/new-pkg
```

## Commands

### Template Management

#### List Templates
```bash
# Show all templates
wanpc list

# Show templates with their default values
wanpc list --show-defaults
```

#### Add Template
```bash
# Interactive mode (recommended)
wanpc config add-template

# Command-line mode
wanpc config add-template --name python-pkg --path ~/templates/python
```

#### Set Template Description
```bash
# Interactive mode
wanpc config set-description

# Command-line mode
wanpc config set-description --name python-pkg --description "Python package template with Poetry"
```

### Default Values

#### Set Template-specific Defaults
```bash
# Interactive mode (shows all available variables from cookiecutter.json)
wanpc config set-default --name python-pkg

# Command-line mode
wanpc config set-default --name python-pkg --key author --value "Your Name"
```

#### Set Global Defaults
```bash
# Interactive mode
wanpc config set-global-default

# Command-line mode
wanpc config set-global-default --key license --value MIT
```

#### Remove Defaults
```bash
# Remove template-specific default
wanpc config remove-default --name python-pkg --key author

# Remove global default
wanpc config remove-global-default --key license
```

### Project Creation

Create a new project from a template:
```bash
# Basic usage (creates in current directory)
wanpc create python-pkg

# Specify output directory
wanpc create python-pkg --output-dir ~/projects/new-pkg

# Skip using defaults
wanpc create python-pkg --no-defaults
```

### Configuration Management

#### View Configuration
```bash
# Show current configuration
wanpc config show

# Show configuration file location
wanpc config config-path
```

#### Remove Template
```bash
# Interactive mode
wanpc config remove-template

# Command-line mode
wanpc config remove-template --name python-pkg
```

## Configuration File

`wanpc` stores its configuration in `~/.wanpc/config.toml`. The configuration includes:
- Template paths and descriptions
- Template-specific default values
- Global default values

View the configuration file location:
```bash
wanpc config config-path
```

Example configuration:
```toml
[templates.python-pkg]
path = "/home/user/templates/python"
description = "Python package template with Poetry"
defaults = { author = "John Doe", email = "john@example.com" }

[global_defaults]
license = "MIT"
year = "2025"
```

## Default Value Precedence

When creating a project, default values are applied in this order:
1. Template-specific defaults (highest priority)
2. Global defaults (if no template default exists)
3. Cookiecutter's own defaults (from cookiecutter.json)

## Interactive Mode

All commands support an interactive mode when run without their required flags. For example:
```bash
wanpc config add-template     # Will prompt for name, path, description, and defaults
wanpc config set-default      # Will show available templates and variables
wanpc config remove-template  # Will show available templates and confirm deletion
```

## Tips

1. Use template descriptions to document the purpose and features of each template
2. Set global defaults for values that are common across templates
3. Use template-specific defaults to override global defaults when needed
4. Check `wanpc config show` to see your current configuration
5. Use the `--show-defaults` flag with `wanpc list` to see all configured defaults

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.