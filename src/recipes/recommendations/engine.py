from __future__ import annotations

from typing import Optional

from src.recipes.catalog.service import RecipeCatalog
from src.recipes.domain import (
    NoMatchResult,
    RecommendationRanking,
    RecommendationResult,
    Recipe,
    RecipeSource,
    Restriction,
)
from src.recipes.inventory.service import IngredientInventory


class RecommendationEngine:
    def __init__(
        self,
        catalog: Optional[RecipeCatalog] = None,
        inventory: Optional[IngredientInventory] = None,
        min_coverage: float = 0.3,
    ):
        self.catalog = catalog or RecipeCatalog()
        self.inventory = inventory or IngredientInventory()
        self.min_coverage = min_coverage

    def recommend(self, person_id: str) -> list[RecommendationResult] | NoMatchResult:
        inv = self.inventory.list_inventory(person_id)
        available_ids = {i.ingredient_id for i in inv.items}
        available_restrictions = {r.value for i in inv.items for r in i.restrictions}

        recipes = self.catalog.list_all()
        ranked: list[RecommendationRanking] = []

        for recipe in recipes:
            matched = []
            missing = []
            conflicts = []

            for ing in recipe.ingredients:
                if ing.ingredient_id in available_ids:
                    matched.append(ing.ingredient_id)
                else:
                    missing.append(ing.ingredient_id)

            for r in recipe.restrictions:
                if r.value not in available_restrictions:
                    conflicts.append(r.value)

            total = len(recipe.ingredients)
            coverage = len(matched) / total if total > 0 else 0.0

            ranking = RecommendationRanking(
                recipe_id=recipe.id,
                matched_ingredients=matched,
                missing_ingredients=missing,
                coverage_ratio=coverage,
                restriction_conflicts=conflicts,
                score=coverage - (0.5 * len(conflicts)),
            )
            ranked.append(ranking)

        ranked.sort(key=lambda r: r.score, reverse=True)
        eligible = [r for r in ranked if r.score >= self.min_coverage]

        if not eligible:
            return NoMatchResult()

        results = []
        for r in eligible:
            recipe = self.catalog.get_recipe(r.recipe_id)
            source = self.catalog.get_source(recipe.source_id) if recipe else None
            if recipe is None or source is None:
                continue
            results.append(
                RecommendationResult(
                    recipe=recipe,
                    source=source,
                    ranking=r,
                )
            )
        return results
