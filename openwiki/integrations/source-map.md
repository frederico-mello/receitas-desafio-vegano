---
type: Source Map
title: Source map and integration points
description: Practical map from repository concerns to source files, tests, configuration, and current external integration boundaries.
tags: [source-map, integrations, navigation]
---

# Source map and integration points

Use this page to jump from a behavior question to the smallest relevant source set. The repository's [architecture overview](../architecture/overview.md) explains how these pieces compose.

| Concern | Start with | Verify with |
| --- | --- | --- |
| Domain fields and enums | `src/recipes/domain/__init__.py` | `tests/test_catalog.py`, `tests/test_inventory.py` |
| Recipe/source ingestion and search | `src/recipes/catalog/service.py` | `tests/test_catalog.py` |
| Ingredient normalization and person inventory | `src/recipes/inventory/service.py` | `tests/test_inventory.py` |
| Ranking and eligibility | `src/recipes/recommendations/engine.py` | `tests/test_recommendations.py` |
| User-facing responses and provenance | `src/recipes/assistant/service.py` | `tests/test_assistant.py` |
| Tables, relationships, sessions | `src/recipes/infra/database.py` | service fixtures using temporary SQLite |
| Packaging and test discovery | `pyproject.toml` | `pytest` |
| Static quality analysis | `sonar-project.properties`, `.github/workflows/sonarcloud.yml` | SonarCloud workflow |
| Wiki refresh | `.github/workflows/openwiki-update.yml`, `openwiki/INSTRUCTIONS.md` | scheduled/manual GitHub Action |

## Current integration boundary

The only runtime external dependency is the local database driver used by SQLAlchemy; the default is SQLite. The package declares SQLAlchemy, Pydantic, and pydantic-settings, but no provider-specific RAG, web scraping, HTTP, vector database, or LLM dependency is declared. The “hybrid RAG” wording comes from the feature commit and README, while the inspected implementation is a deterministic service core.

The repository does have GitHub integrations for SonarCloud analysis and scheduled OpenWiki documentation updates. These are CI/documentation integrations, not application runtime integrations. Their secrets and provider setup belong in GitHub configuration, not in this wiki.

## Extension points

- Add a recipe source adapter before `RecipeCatalog.ingest_recipe`; keep URL/title/content mapping at the catalog boundary.
- Replace or augment `RecommendationEngine` while preserving `RecommendationRanking` if explainability and assistant formatting remain requirements.
- Introduce a repository/session abstraction if moving beyond SQLite or adding migrations.
- Add a delivery layer that calls `RecipeAssistant`; no route or command contract currently exists, so such a layer would define new public behavior and needs dedicated tests.
