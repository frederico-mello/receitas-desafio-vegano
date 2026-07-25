from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Unit(str, Enum):
    UNIT = "unit"
    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITER = "ml"
    LITER = "l"
    TEASPOON = "tsp"
    TABLESPOON = "tbsp"
    CUP = "cup"
    TABLET = "tablet"
    SLICE = "slice"
    CLOVE = "clove"
    PINCH = "pinch"
    TO_TASTE = "to_taste"


class Restriction(str, Enum):
    GLUTEN = "gluten"
    SOY = "soy"
    NUTS = "nuts"
    PEANUTS = "peanuts"
    OIL = "oil"
    COCONUT = "coconut"
    CORN = "corn"
    SESAME = "sesame"


class Ingredient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    canonical_name: str
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    restrictions: list[Restriction] = Field(default_factory=list)


class IngredientAmount(BaseModel):
    ingredient_id: str
    quantity: Optional[float] = None
    unit: Optional[Unit] = None


class RecipeSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_version: str = "1"


class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    title: str
    ingredients: list[IngredientAmount]
    preparation_steps: list[str]
    portions: int = 1
    restrictions: list[Restriction] = Field(default_factory=list)
    version: str = "1"
    previous_version_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InventoryItem(BaseModel):
    ingredient_id: str
    canonical_name: str
    original_input: str
    quantity: Optional[float] = None
    unit: Optional[Unit] = None
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PersonInventory(BaseModel):
    person_id: str
    items: list[InventoryItem] = Field(default_factory=list)


class RecommendationRanking(BaseModel):
    recipe_id: str
    matched_ingredients: list[str]
    missing_ingredients: list[str]
    coverage_ratio: float
    restriction_conflicts: list[str] = Field(default_factory=list)
    score: float = 0.0


class RecommendationResult(BaseModel):
    recipe: Recipe
    source: RecipeSource
    ranking: RecommendationRanking
    adaptation_suggestions: list[str] = Field(default_factory=list)


class NoMatchResult(BaseModel):
    message: str = "Nenhuma receita suficiente encontrada com os ingredientes informados."


class AssistantMessage(BaseModel):
    role: str
    content: str
    source_references: list[str] = Field(default_factory=list)
