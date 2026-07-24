from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.recipes.domain import (
    Ingredient,
    IngredientAmount,
    Recipe,
    RecipeSource,
    Restriction,
)
from src.recipes.infra.database import (
    IngredientModel,
    RecipeModel,
    RecipeSourceModel,
    create_session,
)


class RecipeCatalog:
    def __init__(self, db_url: str = "sqlite:///data/recipes.db"):
        self.session = create_session(db_url)

    def ingest_recipe(
        self,
        url: str,
        title: str,
        ingredients: list[IngredientAmount],
        preparation_steps: list[str],
        portions: int = 1,
        restrictions: Optional[list[Restriction]] = None,
    ) -> Recipe:
        source = (
            self.session.query(RecipeSourceModel)
            .filter(RecipeSourceModel.url == url)
            .first()
        )
        if source is None:
            source = RecipeSourceModel(
                id=RecipeSource(url=url, title=title).id,
                url=url,
                title=title,
                collected_at=datetime.utcnow(),
                content_version="1",
            )
            self.session.add(source)
            self.session.flush()
        else:
            source.content_version = str(int(source.content_version) + 1)
            source.collected_at = datetime.utcnow()

        existing = (
            self.session.query(RecipeModel)
            .filter(RecipeModel.source_id == source.id)
            .first()
        )
        prev_id = None
        if existing is not None:
            prev_id = existing.id
            existing.previous_version_id = existing.id

        recipe = Recipe(
            source_id=source.id,
            title=title,
            ingredients=ingredients,
            preparation_steps=preparation_steps,
            portions=portions,
            restrictions=restrictions or [],
            version=source.content_version,
            previous_version_id=prev_id,
        )
        model = RecipeModel(
            id=recipe.id,
            source_id=recipe.source_id,
            title=recipe.title,
            ingredients=[i.model_dump() for i in recipe.ingredients],
            preparation_steps=recipe.preparation_steps,
            portions=recipe.portions,
            restrictions=[r.value for r in recipe.restrictions],
            version=recipe.version,
            previous_version_id=recipe.previous_version_id,
        )
        self.session.add(model)
        self.session.commit()
        return recipe

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        model = self.session.query(RecipeModel).filter(RecipeModel.id == recipe_id).first()
        if model is None:
            return None
        return self._model_to_recipe(model)

    def get_source(self, source_id: str) -> Optional[RecipeSource]:
        model = (
            self.session.query(RecipeSourceModel)
            .filter(RecipeSourceModel.id == source_id)
            .first()
        )
        if model is None:
            return None
        return RecipeSource(
            id=model.id,
            url=model.url,
            title=model.title,
            collected_at=model.collected_at,
            content_version=model.content_version,
        )

    def search_by_ingredient(self, ingredient_id: str) -> list[Recipe]:
        models = self.session.query(RecipeModel).all()
        results = []
        for m in models:
            for ing in m.ingredients:
                if ing.get("ingredient_id") == ingredient_id:
                    results.append(self._model_to_recipe(m))
                    break
        return results

    def search_by_text(self, query: str) -> list[Recipe]:
        models = self.session.query(RecipeModel).all()
        q = query.lower()
        results = []
        for m in models:
            if q in m.title.lower():
                results.append(self._model_to_recipe(m))
                continue
            for step in m.preparation_steps:
                if q in step.lower():
                    results.append(self._model_to_recipe(m))
                    break
        return results

    def list_all(self) -> list[Recipe]:
        models = self.session.query(RecipeModel).all()
        return [self._model_to_recipe(m) for m in models]

    def _model_to_recipe(self, model: RecipeModel) -> Recipe:
        return Recipe(
            id=model.id,
            source_id=model.source_id,
            title=model.title,
            ingredients=[IngredientAmount(**i) for i in model.ingredients],
            preparation_steps=list(model.preparation_steps),
            portions=model.portions,
            restrictions=[Restriction(r) for r in model.restrictions],
            version=model.version,
            previous_version_id=model.previous_version_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
