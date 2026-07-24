from __future__ import annotations

from typing import Optional

from src.recipes.domain import (
    AssistantMessage,
    NoMatchResult,
    RecommendationResult,
    Recipe,
    RecipeSource,
)
from src.recipes.recommendations.engine import RecommendationEngine


class RecipeAssistant:
    def __init__(self, engine: Optional[RecommendationEngine] = None):
        self.engine = engine or RecommendationEngine()

    def recommend(self, person_id: str) -> AssistantMessage | NoMatchResult:
        result = self.engine.recommend(person_id)
        if isinstance(result, NoMatchResult):
            return result

        lines = ["Encontrei estas receitas compatíveis com seus ingredientes:\n"]
        refs = []
        for rec in result:
            r = rec.recipe
            s = rec.source
            matched_names = ", ".join(rec.ranking.matched_ingredients) or "nenhum"
            missing_names = ", ".join(rec.ranking.missing_ingredients) or "nenhum"
            lines.append(
                f"- **{r.title}** ({r.portions} porções)\n"
                f"  Ingredientes disponíveis: {matched_names}\n"
                f"  Ingredientes ausentes: {missing_names}\n"
                f"  Cobertura: {rec.ranking.coverage_ratio:.0%}\n"
            )
            refs.append(s.url)

        return AssistantMessage(
            role="assistant",
            content="\n".join(lines),
            source_references=refs,
        )

    def explain(self, person_id: str, recipe_title: str) -> AssistantMessage:
        result = self.engine.recommend(person_id)
        if isinstance(result, NoMatchResult):
            return AssistantMessage(
                role="assistant",
                content=f"Não encontrei a receita \"{recipe_title}\" entre as recomendações para você.",
            )

        for rec in result:
            if rec.recipe.title.lower() == recipe_title.lower():
                r = rec.recipe
                s = rec.source
                return AssistantMessage(
                    role="assistant",
                    content=(
                        f"**{r.title}** ({r.portions} porções)\n\n"
                        f"**Ingredientes disponíveis:** "
                        f"{', '.join(rec.ranking.matched_ingredients) or 'nenhum'}\n"
                        f"**Ingredientes ausentes:** "
                        f"{', '.join(rec.ranking.missing_ingredients) or 'nenhum'}\n"
                        f"**Cobertura:** {rec.ranking.coverage_ratio:.0%}\n"
                        f"**Fonte:** {s.url}\n"
                    ),
                    source_references=[s.url],
                )

        return AssistantMessage(
            role="assistant",
            content=f"Não encontrei a receita \"{recipe_title}\" entre as recomendações para você.",
        )

    def adapt(
        self, person_id: str, recipe_title: str, suggestion: str
    ) -> AssistantMessage:
        result = self.engine.recommend(person_id)
        if isinstance(result, NoMatchResult):
            return AssistantMessage(
                role="assistant",
                content=(
                    "Não há receitas suficientes para sugerir adaptações. "
                    "Tente adicionar mais ingredientes ao seu inventário."
                ),
            )

        for rec in result:
            if rec.recipe.title.lower() == recipe_title.lower():
                return AssistantMessage(
                    role="assistant",
                    content=(
                        f"Sugestão de adaptação para **{rec.recipe.title}**:\n\n"
                        f"{suggestion}\n\n"
                        "*Esta é uma sugestão baseada nos seus ingredientes. "
                        "A receita original permanece inalterada no catálogo.*"
                    ),
                    source_references=[rec.source.url],
                )

        return AssistantMessage(
            role="assistant",
            content=f"Não encontrei a receita \"{recipe_title}\" para sugerir adaptações.",
        )
