# Getting Started

Welcome to wanpc! This guide will help you get started with both local documentation development and CI/CD setup.

## Local Documentation Development

### Initial Setup

1. Install the documentation dependencies:
```bash
wanpc add-docs path/to/project (optional)
```

### Live Development Server

For real-time preview of your documentation as you write:

```bash
poetry run run-docs
```

This will:
- Start a development server at http://localhost:8000
- Open your browser automatically
- Watch for changes and rebuild instantly
- Auto-reload your browser when changes are detected

## GitLab CI/CD Configuration

### Configure GitLab Pages

CI/CD for this project is already in place, however, if you would like to configure it, here are some options.

#### Build Preview for Merge Requests

Add this job to preview documentation changes in merge requests:

```yaml
docs-preview:
  stage: docs
  script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install -r docs/requirements.txt
    - cd docs
    - make html
    - cd ..
    - mv docs/_build/html/ preview/
  artifacts:
    paths:
      - preview
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

#### Quality Checks

Add documentation quality checks:

```yaml
docs-lint:
  stage: docs
  script:
    - python -m venv venv
    - source venv/bin/activate
    - pip install -r docs/requirements.txt doc8
    - doc8 docs/source
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Best Practices

1. **Version Control**:
   - Keep documentation close to code
   - Include documentation changes in your PRs
   - Use meaningful commit messages

2. **Writing Style**:
   - Use clear, concise language
   - Include code examples
   - Keep documentation up-to-date with code changes

3. **Organization**:
   - Use meaningful file names
   - Group related topics together
   - Maintain a clear hierarchy

## Next Steps

- Check out the [Quick Start Guide](quickstart) for using wanpc
- Read about [Advanced Configuration](../advanced/configuration)
- Browse the [API Documentation](../api/index)
