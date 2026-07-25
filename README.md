# Receitas Desafio Vegano

Sistema de recomendacao de receitas veganas baseado no conteudo publicado no
Desafio Vegano, da Vegan Outreach. A pessoa informa os ingredientes que possui
e recebe receitas compativeis, com itens ausentes e referencia a fonte original.

## Como Funciona

O projeto usa um RAG hibrido como primeira versao:

- Dados estruturados para receitas, ingredientes, inventario e filtros.
- Busca lexical e por ingredientes para recuperar receitas.
- Ranking deterministico por cobertura, restricoes e preferencias.
- Assistente fundamentado apenas nas receitas recuperadas e no inventario.
- Respostas com URL e identificacao da receita original.

GraphRAG fica como evolucao futura, caso relacoes como substituicoes, tecnicas,
utensilios e alergenicos demonstrem valor mensuravel.

## Capacidades

- **Catalogo de receitas**: ingestao, normalizacao, consulta e versionamento idempotente.
- **Inventario de ingredientes**: cadastro, remocao, aliases, quantidades e unidades opcionais.
- **Recomendacoes personalizadas**: cobertura, ingredientes ausentes, restricoes e explicacao do ranking.
- **Assistente de receitas**: explicacoes, priorizacao e sugestoes de adaptacao separadas da receita oficial.

O sistema nao inventa receitas nem preenche automaticamente informacoes ausentes
na fonte. Adaptacoes sao sugestoes e nao alteram o catalogo oficial.

## Estrutura

```text
src/recipes/
  domain/           Modelos de dominio com Pydantic
  infra/            Persistencia SQLite com SQLAlchemy
  catalog/          Ingestao, versionamento e busca de receitas
  inventory/        Gerenciamento do inventario da pessoa
  recommendations/ Ranking e elegibilidade deterministica
  assistant/        Respostas fundamentadas e atribuicao de fontes
tests/              Testes de catalogo, inventario, recomendacoes e assistente
```

## Requisitos

- Python 3.11 ou superior

## Instalacao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Testes

```bash
PYTHONPATH=src pytest
```

O conjunto atual contem 25 testes cobrindo ingestao e versionamento de receitas,
normalizacao de ingredientes, inventario, recomendacoes, atribuicao de fontes
e sugestoes de adaptacao.

## Exemplo de Uso

```python
from recipes.catalog.service import RecipeCatalog
from recipes.domain import IngredientAmount
from recipes.inventory.service import IngredientInventory
from recipes.recommendations.engine import RecommendationEngine

catalog = RecipeCatalog("sqlite:///data/recipes.db")
inventory = IngredientInventory("sqlite:///data/recipes.db")

ingredient = inventory.add_to_inventory("pessoa-1", "arroz")
catalog.ingest_recipe(
    url="https://exemplo.org/receita",
    title="Arroz com legumes",
    ingredients=[IngredientAmount(ingredient_id=ingredient.ingredient_id)],
    preparation_steps=["Cozinhar e servir."],
)

engine = RecommendationEngine(catalog=catalog, inventory=inventory)
recommendations = engine.recommend("pessoa-1")
```

## Dados e Fontes

As receitas devem ser ingeridas somente de fontes aprovadas do Desafio Vegano.
Cada receita mantém URL, titulo da fonte, data de coleta e versao do conteudo
para permitir auditoria, atualizacao e rollback.

## Status

Este repositorio contem a base funcional inicial do dominio. A interface de
produto, a ingestao automatica das paginas oficiais, embeddings e integracao
com um modelo de linguagem sao proximos passos de evolucao.
