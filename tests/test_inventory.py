from __future__ import annotations

import pytest

from src.recipes.domain import Unit
from src.recipes.inventory.service import IngredientInventory


@pytest.fixture
def inventory(tmp_path):
    db = f"sqlite:///{tmp_path}/test.db"
    return IngredientInventory(db_url=db)


def test_add_and_list_inventory(inventory):
    inventory.add_to_inventory(person_id="p1", ingredient_name="tomate")
    inv = inventory.list_inventory("p1")
    assert len(inv.items) == 1
    assert inv.items[0].canonical_name == "tomate"
    assert inv.items[0].original_input == "tomate"


def test_add_with_quantity(inventory):
    inventory.add_to_inventory(
        person_id="p1",
        ingredient_name="farinha",
        quantity=500,
        unit=Unit.GRAM,
    )
    inv = inventory.list_inventory("p1")
    assert inv.items[0].quantity == 500
    assert inv.items[0].unit == Unit.GRAM


def test_add_without_quantity(inventory):
    inventory.add_to_inventory(person_id="p1", ingredient_name="sal")
    inv = inventory.list_inventory("p1")
    assert inv.items[0].quantity is None
    assert inv.items[0].unit is None


def test_remove_from_inventory(inventory):
    inventory.add_to_inventory(person_id="p1", ingredient_name="cebola")
    inv = inventory.list_inventory("p1")
    item_id = inv.items[0].ingredient_id
    inventory.remove_from_inventory("p1", item_id)
    inv = inventory.list_inventory("p1")
    assert len(inv.items) == 0


def test_alias_resolution(inventory):
    inventory.register_ingredient(
        canonical_name="tomate",
        display_name="Tomate",
        aliases=["tomates", "tomate italiano"],
    )
    resolved = inventory.resolve_ingredient("tomates")
    assert resolved is not None
    assert resolved.canonical_name == "tomate"


def test_unknown_ingredient_stored_as_is(inventory):
    resolved = inventory.resolve_ingredient("ingrediente_desconhecido_xyz")
    assert resolved is None


def test_multiple_persons(inventory):
    inventory.add_to_inventory(person_id="p1", ingredient_name="alho")
    inventory.add_to_inventory(person_id="p2", ingredient_name="cebola")
    inv1 = inventory.list_inventory("p1")
    inv2 = inventory.list_inventory("p2")
    assert len(inv1.items) == 1
    assert len(inv2.items) == 1
    assert inv1.items[0].canonical_name == "alho"
    assert inv2.items[0].canonical_name == "cebola"
