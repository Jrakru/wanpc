# Installation Guide

This guide will help you install wanpc.

## Requirements

- Python 3.9 or higher
- pip package manager

## Quick Install

```bash
git clone https://github.com/Jrakru/wanpc.git
cd wanpc
pipx install .
```

## Development Install

For development, you might want to install in editable mode:

```bash
git clone https://github.com/Jrakru/wanpc.git
cd wanpc
pipx install -e ".[dev]"
```

## Verifying Installation

You can verify your installation by running:

```bash
wanpc --help
```

If the above command is accepted (and returns the help list) then youll know everything is working!
