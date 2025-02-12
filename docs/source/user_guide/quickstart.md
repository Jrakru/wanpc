---
jupytext:
  formats: md:myst
  text_representation:
    format_name: myst
    extension: .md
    format_version: '0.13'
    jupytext_version: '1.13.0'
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Quick Start Guide

Get started with wanpc in minutes!

## Basic Usage

Here's a simple example:

```python
>wanpc config add-template

>wanpc create TEMPLATE_NAME
```
The above commands create a new template, and creates a packages in the currently dirrectory from it


## Advanced Features

### Feature 1: Setting defaults

There's two kinds of defaults you can set with wanpc, global and template level. A template level default prevails over a global default
```bash
wanpc config set-default --name python-pkg --key author --value "Your Name"

wanpc config set-global-default --key license --value MIT
```

### Feature 2: Adding docs

Wanpc can be used to create docs for your package (much like these!)

```bash
wanpc add-docs path/to/project

poetry run run-docs
```
The path is optional, if it is not provided, it assumed you are already at the root of your desired file. 

## Next Steps

- Check out the [API Documentation](../api/index) for detailed documentation