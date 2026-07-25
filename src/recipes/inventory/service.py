from __future__ import annotations

from typing import Optional

from src.recipes.domain import Ingredient, InventoryItem, PersonInventory, Unit
from src.recipes.infra.database import (
    IngredientModel,
    InventoryItemModel,
    create_session,
)


class IngredientInventory:
    def __init__(self, db_url: str = "sqlite:///data/recipes.db"):
        self.session = create_session(db_url)

    def register_ingredient(
        self,
        canonical_name: str,
        display_name: str,
        aliases: Optional[list[str]] = None,
    ) -> Ingredient:
        existing = (
            self.session.query(IngredientModel)
            .filter(IngredientModel.canonical_name == canonical_name)
            .first()
        )
        if existing is not None:
            return Ingredient(
                id=existing.id,
                canonical_name=existing.canonical_name,
                display_name=existing.display_name,
                aliases=list(existing.aliases),
                restrictions=list(existing.restrictions),
            )
        ing = Ingredient(
            canonical_name=canonical_name,
            display_name=display_name,
            aliases=aliases or [],
        )
        model = IngredientModel(
            id=ing.id,
            canonical_name=ing.canonical_name,
            display_name=ing.display_name,
            aliases=ing.aliases,
            restrictions=[],
        )
        self.session.add(model)
        self.session.commit()
        return ing

    def resolve_ingredient(self, name: str) -> Optional[Ingredient]:
        models = self.session.query(IngredientModel).all()
        for m in models:
            if m.canonical_name == name or name in (m.aliases or []):
                return Ingredient(
                    id=m.id,
                    canonical_name=m.canonical_name,
                    display_name=m.display_name,
                    aliases=list(m.aliases),
                    restrictions=list(m.restrictions),
                )
        return None

    def add_to_inventory(
        self,
        person_id: str,
        ingredient_name: str,
        quantity: Optional[float] = None,
        unit: Optional[Unit] = None,
    ) -> InventoryItem:
        resolved = self.resolve_ingredient(ingredient_name)
        if resolved is None:
            resolved = self.register_ingredient(
                canonical_name=ingredient_name,
                display_name=ingredient_name,
            )
        item = InventoryItem(
            ingredient_id=resolved.id,
            canonical_name=resolved.canonical_name,
            original_input=ingredient_name,
            quantity=quantity,
            unit=unit,
        )
        model = InventoryItemModel(
            id=item.ingredient_id,
            person_id=person_id,
            ingredient_id=resolved.id,
            canonical_name=resolved.canonical_name,
            original_input=ingredient_name,
            quantity=quantity,
            unit=unit.value if unit else None,
        )
        self.session.add(model)
        self.session.commit()
        return item

    def list_inventory(self, person_id: str) -> PersonInventory:
        models = (
            self.session.query(InventoryItemModel)
            .filter(InventoryItemModel.person_id == person_id)
            .all()
        )
        items = [
            InventoryItem(
                ingredient_id=m.ingredient_id,
                canonical_name=m.canonical_name,
                original_input=m.original_input,
                quantity=m.quantity,
                unit=Unit(m.unit) if m.unit else None,
                added_at=m.added_at,
            )
            for m in models
        ]
        return PersonInventory(person_id=person_id, items=items)

    def remove_from_inventory(self, person_id: str, ingredient_id: str) -> None:
        self.session.query(InventoryItemModel).filter(
            InventoryItemModel.person_id == person_id,
            InventoryItemModel.ingredient_id == ingredient_id,
        ).delete()
        self.session.commit()
