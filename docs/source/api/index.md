# API Documentation

This section provides detailed API documentation for wanpc.

## Examples

Here's a quick example of a new project's timeline

```python
wanpc config add-template --name python-pkg --path ~/templates/python

wanpc config set-default --name python-pkg --key author --value "Your Name"

wanpc config set-global-default --key license --value MIT

wanpc create python-pkg --output-dir ~/projects/new-pkg

cd ~/projects/new-pkg

wanpc add-docs

poetry run run-docs
```

## API Versioning

We follow semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR version for incompatible API changes
- MINOR version for new functionality in a backwards compatible manner
- PATCH version for backwards compatible bug fixes
