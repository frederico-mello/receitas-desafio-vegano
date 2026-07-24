from __future__ import annotations

import pytest

from src.recipes.catalog.service import RecipeCatalog
from src.recipes.domain import IngredientAmount, NoMatchResult, Restriction
from src.recipes.inventory.service import IngredientInventory
from src.recipes.recommendations.engine import RecommendationEngine


@pytest.fixture
def engine(tmp_path):
    db = f"sqlite:///{tmp_path}/test.db"
    catalog = RecipeCatalog(db_url=db)
    inventory = IngredientInventory(db_url=db)
    return RecommendationEngine(catalog=catalog, inventory=inventory, min_coverage=0.3)


def _add_ingredient(inventory, person_id, name):
    item = inventory.add_to_inventory(person_id=person_id, ingredient_name=name)
    return item.ingredient_id


def test_recommend_compatible_recipe(engine):
    inventory = engine.inventory
    arroz_id = _add_ingredient(inventory, "p1", "arroz")
    feijao_id = _add_ingredient(inventory, "p1", "feijao")

    engine.catalog.ingest_recipe(
        url="https://exemplo.com/arroz-feijao",
        title="Arroz com Feijão",
        ingredients=[
            IngredientAmount(ingredient_id=arroz_id),
            IngredientAmount(ingredient_id=feijao_id),
        ],
        preparation_steps=["Cozinhar"],
    )

    result = engine.recommend("p1")
    assert not isinstance(result, NoMatchResult)
    assert len(result) == 1
    assert result[0].recipe.title == "Arroz com Feijão"
    assert len(result[0].ranking.matched_ingredients) == 2


def test_recommend_excludes_restriction_conflict(engine):
    inventory = engine.inventory
    _add_ingredient(inventory, "p1", "arroz")
    _add_ingredient(inventory, "p1", "gluten")

    engine.catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão",
        ingredients=[IngredientAmount(ingredient_id="farinha")],
        preparation_steps=["Assar"],
        restrictions=[Restriction.GLUTEN],
    )

    result = engine.recommend("p1")
    assert isinstance(result, NoMatchResult)


def test_recommend_no_match(engine):
    engine.catalog.ingest_recipe(
        url="https://exemplo.com/risoto",
        title="Risoto",
        ingredients=[IngredientAmount(ingredient_id="arroz_arboreo")],
        preparation_steps=["Cozinhar"],
    )
    result = engine.recommend("p1")
    assert isinstance(result, NoMatchResult)


def test_recommend_ranking_order(engine):
    inventory = engine.inventory
    farinha_id = _add_ingredient(inventory, "p1", "farinha")
    agua_id = _add_ingredient(inventory, "p1", "agua")

    engine.catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão",
        ingredients=[
            IngredientAmount(ingredient_id=farinha_id),
            IngredientAmount(ingredient_id=agua_id),
            IngredientAmount(ingredient_id="fermento"),
        ],
        preparation_steps=["Misturar"],
    )
    engine.catalog.ingest_recipe(
        url="https://exemplo.com/massa",
        title="Massa",
        ingredients=[
            IngredientAmount(ingredient_id=farinha_id),
            IngredientAmount(ingredient_id=agua_id),
        ],
        preparation_steps=["Misturar"],
    )

    result = engine.recommend("p1")
    assert not isinstance(result, NoMatchResult)
    assert result[0].recipe.title == "Massa"
    assert result[0].ranking.coverage_ratio == 1.0


def test_recommend_explainability(engine):
    inventory = engine.inventory
    farinha_id = _add_ingredient(inventory, "p1", "farinha")

    engine.catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão",
        ingredients=[IngredientAmount(ingredient_id=farinha_id)],
        preparation_steps=["Assar"],
    )

    result = engine.recommend("p1")
    assert not isinstance(result, NoMatchResult)
    assert result[0].source.url == "https://exemplo.com/pao"
    assert farinha_id in result[0].ranking.matched_ingredients
