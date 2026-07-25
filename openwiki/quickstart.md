---
type: Repository Guide
title: Receitas Desafio Vegano quickstart
description: Entry point for the Python recipe catalog, ingredient inventory, deterministic recommendation engine, and source-grounded assistant in this repository.
tags: [python, recipes, rag, recommendations, quickstart]
---

# Receitas Desafio Vegano

This repository is a small Python 3.11+ application for personalized vegan-recipe recommendations. Its current implementation is a deterministic, database-backed core: recipes are ingested from source URLs, ingredients are normalized into a shared catalog, each person has an inventory, and recommendations are ranked by ingredient coverage with source references. The README summarizes the product as “RAG com receitas do Desafio Vegano”; the code currently contains no HTTP server, LLM client, embedding store, or external ingestion adapter.

## Start here

- Read the [architecture overview](architecture/overview.md) to understand package boundaries and service composition.
- Use the [recipe and ingredient model](domain/recipe-model.md) as the canonical vocabulary for entities, units, restrictions, and result objects.
- Follow the [recommendation workflow](workflows/recommendation.md) for the end-to-end user-facing path.
- Consult [catalog and inventory persistence](data/catalog-and-inventory.md) before changing ingestion, aliases, or SQLite behavior.
- Run the checks described in [testing and operations](operations/testing.md).
- Use the [database migrations runbook](operations/database-migrations.md) for schema changes via Alembic.
- Use the [source map and integrations](integrations/source-map.md) to locate implementation files and identify current extension points.

## Local orientation

- `src/recipes/domain/__init__.py` contains Pydantic models and enums shared by all services.
- `src/recipes/catalog/service.py` owns recipe/source ingestion and read/search operations.
- `src/recipes/inventory/service.py` owns ingredient registration, alias resolution, and per-person inventory.
- `src/recipes/recommendations/engine.py` combines catalog and inventory into ranked recommendations.
- `src/recipes/assistant/service.py` turns engine results into Portuguese assistant messages with source URLs.
- `src/recipes/infra/database.py` defines SQLAlchemy tables and creates the database schema.
- `tests/` contains the executable behavior contract; fixtures use temporary SQLite files.

## Typical development loop

Install the package and development dependencies, then run the test suite:

```bash
python -m pip install -e '.[dev]'
pytest
```

There is no checked-in CLI or application entrypoint. To exercise the core directly, import `RecipeCatalog`, `IngredientInventory`, `RecommendationEngine`, and `RecipeAssistant` from their service modules and pass an explicit `sqlite:///...` URL when isolation matters. The default URL is `sqlite:///data/recipes.db`; schema creation occurs when a service opens its session.

## Product boundary and watch-outs

The feature was introduced in commit `b8e9f7f` as “receitas personalizadas com RAG hibrido,” followed by SonarCloud CI in `363f8e3`. Despite the feature name, retrieval and ranking are presently implemented with in-process SQLAlchemy reads and deterministic Python scoring. Treat source URLs as the provenance boundary: assistant responses expose them through `source_references`, and adaptations are explicitly labeled suggestions that do not mutate the catalog.

Important behavior to preserve:

- recipe recommendations require at least `min_coverage` score (default `0.3`);
- restriction conflicts subtract `0.5` per conflict from the score;
- unknown inventory ingredient names are registered as-is;
- recipe ingestion increments source `content_version` for an existing URL and creates a new recipe version;
- the current implementation does not expose a public API or production deployment command.

## Backlog

- **External recipe/RAG ingestion** — anchor: `src/recipes/catalog/service.py`; deferred because only the service-level ingestion API exists, with no crawler, parser, embeddings, or retrieval provider.
- **Application/API entrypoint** — anchor: repository root and `src/recipes/`; deferred because no web, CLI, or worker entrypoint is checked in.
