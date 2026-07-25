---
type: Architecture Overview
title: Service architecture
description: Layered view of the recipe domain, catalog and inventory services, deterministic recommendation engine, assistant formatter, and SQLAlchemy persistence adapter.
tags: [architecture, services, sqlalchemy, python]
---

# Service architecture

The repository is organized as a compact service core under `src/recipes`, rather than as a deployed application. The [recipe domain model](../domain/recipe-model.md) defines the shared contracts. The [catalog and inventory persistence](../data/catalog-and-inventory.md) services use SQLAlchemy models through the infrastructure module. The [recommendation workflow](../workflows/recommendation.md) composes those services, and the assistant is a presentation-oriented wrapper around the engine.

## Runtime composition

```text
RecipeAssistant
    -> RecommendationEngine
        -> RecipeCatalog -> create_session -> SQLite/SQLAlchemy models
        -> IngredientInventory -> create_session -> SQLite/SQLAlchemy models
```

`RecommendationEngine` accepts injected catalog and inventory services, which is how tests isolate each scenario. If omitted, it constructs both services with the default `sqlite:///data/recipes.db` URL. `RecipeAssistant` similarly accepts an engine or constructs the default composition.

## Boundaries

- **Domain:** Pydantic models, UUID defaults, `Unit` and `Restriction` enums, and result objects. It has no database imports.
- **Application services:** catalog, inventory, recommendation, and assistant modules. These contain business rules and orchestration.
- **Infrastructure:** `src/recipes/infra/database.py` maps the domain concepts to SQLAlchemy tables and creates sessions/schema.
- **Delivery/integration:** currently absent. There is no HTTP route, CLI, queue, LLM provider, vector index, or external source connector in the checked-in implementation. The [source map and integrations](../integrations/source-map.md) records this boundary.

## Why this shape exists

The initial feature commit explicitly introduced domain models, versioned/idempotent catalog ingestion, alias-aware inventory, deterministic coverage ranking, and source-attributed assistant responses. The separation keeps those behaviors testable without requiring a network or model provider. Future adapters should preserve the service contracts rather than putting transport or provider logic into the domain module.

## Change guidance

Start with the domain model when changing fields or enum values, then update both the SQLAlchemy serialization/deserialization paths and affected service tests. Changes to ranking rules belong in `RecommendationEngine` and should add explainability assertions. Changes to user-facing wording or provenance belong in `RecipeAssistant` tests. The [testing and operations](../operations/testing.md) page lists the relevant checks.
