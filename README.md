# receitas-desafio-vegano

RAG com receitas do Desafio Vegano.

## Requisitos

- Python 3.11+
- `make` (GNU Make)

## Uso Rápido

```bash
# Setup completo + testes em um comando
make dev

# Ou passo a passo
make install   # configura venv + instala dependências
make setup-db  # prepara diretório data/
make test      # executa pytest
make clean     # limpa .venv e __pycache__
```

## Estrutura

| Caminho | Descrição |
|---|---|
| `src/recipes/assistant/` | Assistente de receitas |
| `src/recipes/catalog/` | Catálogo de receitas |
| `src/recipes/domain/` | Modelos de domínio |
| `src/recipes/infra/` | Infraestrutura (banco) |
| `src/recipes/inventory/` | Inventário de ingredientes |
| `src/recipes/recommendations/` | Motor de recomendações |
| `tests/` | Testes automatizados |
| `data/` | Banco SQLite (`recipes.db`) |

## Modelo de Dados

- **Ingredient**: `id`, `canonical_name`, `display_name`, `aliases`, `restrictions`
- **Recipe**: `id`, `source_id`, `title`, `ingredients`, `preparation_steps`, `restrictions`
- **InventoryItem**: `ingredient_id`, `canonical_name`, `original_input`, `quantity`, `unit`, `restrictions`

## Motor de Recomendações

Recomenda receitas baseado nos ingredientes disponíveis na pessoa:

1. Coleta ingredientes do inventário (`person_id`)
2. Compara ingredientes da receita com os disponíveis
3. Verifica restrições alimentares (gluten, soja, castanhas, etc.)
4. Calcula score de cobertura mínimo de 30%
