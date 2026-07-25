---
type: Operations and Testing Guide
title: Testing and operations
description: Local verification, test organization, SQLite runtime defaults, lint and quality automation, and operational gaps for the recipe services.
tags: [testing, operations, pytest, ci, sonarcloud]
---

# Testing and operations

The repository is currently a library-style Python project. The [recommendation workflow](../workflows/recommendation.md) and [catalog/inventory persistence](../data/catalog-and-inventory.md) are the primary behavior surfaces; there is no server or deployment runbook yet.

## Local checks

The project requires Python `>=3.11`. Install development dependencies from `pyproject.toml` and run:

```bash
python -m pip install -e '.[dev]'
pytest
```

Pytest is configured with `testpaths = ["tests"]`, `asyncio_mode = "auto"`, and `pythonpath = ["src"]`. The current tests are synchronous service tests despite the async mode setting. The suite uses temporary SQLite databases, so it should not depend on `data/recipes.db`.

The dev dependency set includes `ruff`, but no Ruff configuration or explicit lint command is checked in. Run lint only after confirming the desired project configuration rather than treating it as a repository-enforced gate.

## CI and quality automation

`.github/workflows/sonarcloud.yml` runs SonarCloud on pushes to `main`, selected pull requests, and manual dispatch. It uses a full checkout and expects `GITHUB_TOKEN` and `SONAR_TOKEN`; `sonar-project.properties` identifies the project, excludes Markdown, and expects `coverage.xml` for Python coverage. The workflow does not install dependencies, run pytest, or generate coverage itself, so coverage availability depends on SonarCloud behavior or future workflow changes.

`.github/workflows/openwiki-update.yml` schedules a daily OpenWiki update and allows manual dispatch. It installs OpenWiki with npm, runs `openwiki code --update --print`, and opens a pull request containing wiki/control files. Provider and tracing credentials are GitHub secrets; do not copy their values into repository docs.

## Operational gaps

- no application entrypoint, health check, migration system, seed data, or deployment manifest;
- default SQLite directory creation is not handled explicitly;
- service constructors create sessions and schema immediately;
- no documented backup, retention, or concurrency strategy;
- no enforced test/lint job in the checked-in CI workflows.

These gaps are intentionally recorded rather than inferred as supported behavior. For model or schema changes, update the [domain model](../domain/recipe-model.md), round-trip tests, and this page together.
