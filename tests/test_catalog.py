from __future__ import annotations

import pytest

from src.recipes.catalog.service import RecipeCatalog
from src.recipes.domain import IngredientAmount


@pytest.fixture
def catalog(tmp_path):
    db = f"sqlite:///{tmp_path}/test.db"
    return RecipeCatalog(db_url=db)


def test_ingest_valid_recipe(catalog):
    recipe = catalog.ingest_recipe(
        url="https://exemplo.com/risoto",
        title="Risoto de Cogumelos",
        ingredients=[IngredientAmount(ingredient_id="arroz", quantity=200, unit=None)],
        preparation_steps=["Cozinhar o arroz", "Adicionar cogumelos"],
        portions=2,
    )
    assert recipe.title == "Risoto de Cogumelos"
    assert recipe.portions == 2
    assert len(recipe.ingredients) == 1


def test_ingest_incomplete_source_raises_no_error(catalog):
    recipe = catalog.ingest_recipe(
        url="https://exemplo.com/sopa",
        title="Sopa",
        ingredients=[],
        preparation_steps=[],
        portions=1,
    )
    assert recipe.title == "Sopa"


def test_ingest_duplicate_updates_version(catalog):
    r1 = catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão",
        ingredients=[IngredientAmount(ingredient_id="farinha")],
        preparation_steps=["Misturar", "Assar"],
    )
    r2 = catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão Integral",
        ingredients=[IngredientAmount(ingredient_id="farinha_integral")],
        preparation_steps=["Misturar", "Assar"],
    )
    assert r1.version == "1"
    assert r2.version == "2"
    assert r2.previous_version_id == r1.id


def test_get_recipe_returns_none_for_missing(catalog):
    assert catalog.get_recipe("nao-existe") is None


def test_search_by_ingredient(catalog):
    catalog.ingest_recipe(
        url="https://exemplo.com/feijoada",
        title="Feijoada",
        ingredients=[IngredientAmount(ingredient_id="feijao_preto")],
        preparation_steps=["Cozinhar"],
    )
    results = catalog.search_by_ingredient("feijao_preto")
    assert len(results) == 1
    assert results[0].title == "Feijoada"


def test_search_by_text(catalog):
    catalog.ingest_recipe(
        url="https://exemplo.com/bolo",
        title="Bolo de Cenoura",
        ingredients=[IngredientAmount(ingredient_id="cenoura")],
        preparation_steps=["Ralar cenoura", "Misturar massa"],
    )
    results = catalog.search_by_text("cenoura")
    assert len(results) == 1


def test_source_reference_in_result(catalog):
    recipe = catalog.ingest_recipe(
        url="https://exemplo.com/lasanha",
        title="Lasanha",
        ingredients=[IngredientAmount(ingredient_id="massa")],
        preparation_steps=["Montar", "Assar"],
    )
    source = catalog.get_source(recipe.source_id)
    assert source is not None
    assert source.url == "https://exemplo.com/lasanha"
