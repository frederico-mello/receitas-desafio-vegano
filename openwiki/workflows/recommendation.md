---
type: Business Workflow
title: Personalized recommendation and assistant workflow
description: End-to-end deterministic workflow from a person's ingredient inventory to ranked recipes, no-match handling, explanations, adaptations, and source attribution.
tags: [workflow, recommendations, assistant, explainability]
---

# Recommendation workflow

The [service architecture](../architecture/overview.md) composes `RecipeCatalog`, `IngredientInventory`, and `RecommendationEngine`; `RecipeAssistant` formats the engine result for a user.

## Ranking path

1. `RecommendationEngine.recommend(person_id)` loads that person's inventory and builds available ingredient ID and canonical-name sets.
2. It loads every catalog recipe and compares each `IngredientAmount.ingredient_id` with the available IDs.
3. It computes `coverage_ratio = matched / total`; an empty-ingredient recipe has coverage `0.0`.
4. For every recipe restriction whose value appears in the available canonical names, it records a conflict.
5. It computes `score = coverage_ratio - (0.5 * number_of_conflicts)`, sorts descending, and retains scores at or above `min_coverage` (default `0.3`).
6. Eligible rankings are hydrated with their recipe and source. Missing recipe/source records are skipped.
7. If no eligible ranking remains, the result is `NoMatchResult` with a Portuguese default message.

This is deterministic and explainable, but it is not semantic RAG: catalog reads are full-table scans, ingredient matching is ID-based, and there is no embedding or language-model stage.

## Assistant behaviors

- `recommend` produces a Markdown-like list with title, portions, matched IDs, missing IDs, coverage, and source URL references.
- `explain` reruns recommendation, finds a case-insensitive exact recipe title, and reports the same match/missing/coverage details plus the source URL. It returns a not-found message when the title is not among eligible recommendations.
- `adapt` accepts a caller-provided suggestion, labels it as a suggestion, preserves source attribution, and explicitly states that the original catalog recipe remains unchanged.

The source URL is the provenance link between the [domain result objects](../domain/recipe-model.md) and user-facing assistant output.

## Tests and change risks

`tests/test_recommendations.py` covers compatible recipes, conflicts, no-match behavior, ordering, and explainability. `tests/test_assistant.py` covers formatting, source references, title lookup, no-match behavior, and the non-mutating adaptation promise. Any scoring or restriction change should update these tests first; any wording or source-reference change should preserve the assertions that users can identify the recipe and its origin.
