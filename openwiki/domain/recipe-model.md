---
type: Domain Model
title: Recipe, ingredient, inventory, and recommendation model
description: Canonical domain vocabulary for recipe sources, ingredients, inventories, restrictions, rankings, assistant messages, and their Pydantic validation contracts.
tags: [domain, pydantic, recipes, ingredients]
---

# Domain model

`src/recipes/domain/__init__.py` is the canonical vocabulary shared by the [service architecture](../architecture/overview.md). Pydantic models validate the in-memory contract; `src/recipes/infra/database.py` stores the same concepts in SQLAlchemy tables.

## Core concepts

- **`RecipeSource`** identifies the provenance URL, title, collection time, and source content version.
- **`Recipe`** references a source and contains a title, `IngredientAmount` list, preparation steps, portions, restrictions, and version lineage through `previous_version_id`.
- **`Ingredient`** provides a stable UUID, canonical and display names, aliases, and restriction metadata.
- **`InventoryItem` / `PersonInventory`** preserve the original input while associating a normalized ingredient and optional quantity/unit with a `person_id`.
- **`RecommendationRanking`** records matched and missing ingredient IDs, coverage ratio, restriction conflicts, and score. `RecommendationResult` bundles the ranking with the recipe and source.
- **`AssistantMessage`** contains a role, Portuguese content, and source URL references. `NoMatchResult` is the explicit no-result response.

`Unit` supports common cooking units such as grams, milliliters, cups, slices, cloves, pinches, and “to taste”. `Restriction` currently enumerates gluten, soy, nuts, peanuts, oil, coconut, corn, and sesame.

## Relationships

A recipe points to one source through `source_id` and contains ingredient references by `IngredientAmount.ingredient_id`. An inventory item points to an ingredient and is scoped by person. The [catalog and inventory persistence](../data/catalog-and-inventory.md) page explains how these relationships are represented in SQLite. The [recommendation workflow](../workflows/recommendation.md) consumes both sides to produce an explainable ranking.

## Contract caveats

The model treats quantities as optional and does not perform unit conversion. Restrictions are represented on recipes and ingredients, but the current ranking implementation checks recipe restriction values against inventory canonical names; this is a simple conflict heuristic, not a full dietary policy engine. `AssistantMessage` carries source URLs, but the current assistant displays ingredient IDs rather than resolving them to display names.

When extending the model, preserve enum serialization compatibility: database recipes store restriction values as strings and ingredient amounts as JSON dictionaries. Update round-trip tests in `tests/test_catalog.py` or `tests/test_inventory.py` accordingly.
