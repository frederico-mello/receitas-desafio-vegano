from __future__ import annotations

import pytest

from src.recipes.assistant.service import RecipeAssistant
from src.recipes.catalog.service import RecipeCatalog
from src.recipes.domain import IngredientAmount, NoMatchResult
from src.recipes.inventory.service import IngredientInventory
from src.recipes.recommendations.engine import RecommendationEngine


@pytest.fixture
def assistant(tmp_path):
    db = f"sqlite:///{tmp_path}/test.db"
    catalog = RecipeCatalog(db_url=db)
    inventory = IngredientInventory(db_url=db)
    engine = RecommendationEngine(catalog=catalog, inventory=inventory, min_coverage=0.3)
    return RecipeAssistant(engine=engine), catalog, inventory


def _add_ingredient(inventory, person_id, name):
    return inventory.add_to_inventory(person_id=person_id, ingredient_name=name).ingredient_id


def test_assistant_recommend_with_results(assistant):
    svc, catalog, inventory = assistant
    arroz_id = _add_ingredient(inventory, "p1", "arroz")
    catalog.ingest_recipe(
        url="https://exemplo.com/arroz",
        title="Arroz Simples",
        ingredients=[IngredientAmount(ingredient_id=arroz_id)],
        preparation_steps=["Cozinhar"],
    )
    msg = svc.recommend("p1")
    assert not isinstance(msg, NoMatchResult)
    assert "Arroz Simples" in msg.content
    assert "https://exemplo.com/arroz" in msg.source_references


def test_assistant_recommend_no_match(assistant):
    svc, catalog, inventory = assistant
    catalog.ingest_recipe(
        url="https://exemplo.com/risoto",
        title="Risoto",
        ingredients=[IngredientAmount(ingredient_id="arroz_arboreo")],
        preparation_steps=["Cozinhar"],
    )
    msg = svc.recommend("p1")
    assert isinstance(msg, NoMatchResult)


def test_assistant_explain_recipe(assistant):
    svc, catalog, inventory = assistant
    farinha_id = _add_ingredient(inventory, "p1", "farinha")
    catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão",
        ingredients=[IngredientAmount(ingredient_id=farinha_id)],
        preparation_steps=["Assar"],
    )
    msg = svc.explain("p1", "Pão")
    assert "Pão" in msg.content
    assert "https://exemplo.com/pao" in msg.source_references


def test_assistant_explain_unknown_recipe(assistant):
    svc, catalog, inventory = assistant
    _add_ingredient(inventory, "p1", "farinha")
    msg = svc.explain("p1", "Receita Inexistente")
    assert "não encontrei" in msg.content.lower()


def test_assistant_adaptation_labeled_as_suggestion(assistant):
    svc, catalog, inventory = assistant
    farinha_id = _add_ingredient(inventory, "p1", "farinha")
    catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão",
        ingredients=[IngredientAmount(ingredient_id=farinha_id)],
        preparation_steps=["Assar"],
    )
    msg = svc.adapt("p1", "Pão", "Substitua a farinha branca por integral.")
    assert "sugestão" in msg.content.lower()
    assert "inalterada" in msg.content.lower()
    assert "https://exemplo.com/pao" in msg.source_references


def test_assistant_priority_refinement(assistant):
    svc, catalog, inventory = assistant
    farinha_id = _add_ingredient(inventory, "p1", "farinha")
    agua_id = _add_ingredient(inventory, "p1", "agua")
    catalog.ingest_recipe(
        url="https://exemplo.com/pao",
        title="Pão Rápido",
        ingredients=[
            IngredientAmount(ingredient_id=farinha_id),
            IngredientAmount(ingredient_id=agua_id),
        ],
        preparation_steps=["Misturar", "Assar 30min"],
    )
    catalog.ingest_recipe(
        url="https://exemplo.com/massa",
        title="Massa",
        ingredients=[
            IngredientAmount(ingredient_id=farinha_id),
            IngredientAmount(ingredient_id=agua_id),
        ],
        preparation_steps=["Misturar", "Cozinhar 10min"],
    )
    msg = svc.recommend("p1")
    assert not isinstance(msg, NoMatchResult)
    assert "Pão Rápido" in msg.content or "Massa" in msg.content
