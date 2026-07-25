## Why

O schema do banco é criado com `Base.metadata.create_all()` em toda chamada de `create_session`, sem versionamento nem trilha de evolução. Não existe caminho para alterar tabelas existentes sem perder dados, não há suporte a SQLite+Postgres coexistindo, e qualquer deploy novo roda `create_all` contra o banco de produção sem chance de revisão. Sem migrations, o backlog do projeto não consegue avançar para API externa, ingestão via RAG, ou troca de banco.

## What Changes

- Adiciona **Alembic** como ferramenta de migrations versionadas, integrada ao `Base.metadata` declarado em `src/recipes/infra/database.py`.
- Cria a primeira migration (autogenerate ou manual) que materializa o schema atual de `recipes`, `recipe_sources`, `ingredients` e `inventory_items` como ponto de partida versionado.
- Mantém `Base.metadata.create_all()` em `create_session` apenas como fallback de desenvolvimento e teste (quando o banco está vazio e não há tabela `alembic_version`); produção usa exclusivamente `alembic upgrade head`.
- Documenta o fluxo operacional (instalar, gerar migration, aplicar, reverter) em uma nova seção de `openwiki/operations/`.
- Adiciona dependência `alembic` ao `[project.dependencies]` de `pyproject.toml` e entradas de dev (CLI já vem com o pacote).
- Adiciona teste de contrato: aplicar migrations em SQLite temporário produz o mesmo schema que `create_all`.

Nenhuma mudança em `RecipeCatalog`, `IngredientInventory`, `RecommendationEngine` ou `RecipeAssistant`. Os serviços continuam consumindo `create_session` sem alteração de assinatura.

## Capabilities

### New Capabilities

- `database-migrations`: migrations versionadas via Alembic, integrando `Base.metadata` de `src/recipes/infra/database.py`, com fluxo de upgrade/downgrade e fallback documentado para dev/test.

### Modified Capabilities

Nenhuma capacidade existente tem mudança de requisito — a substituição de `create_all` por migrations em produção é detalhe de implementação. Os requisitos observáveis (persistência via SQLAlchemy, sessão por serviço, isolamento por `db_url`) permanecem.

## Impact

- **Código de produção:** `src/recipes/infra/database.py` (criar `src/recipes/infra/migrations/` ou `alembic/` na raiz, decidir no design), nova dependência `alembic`.
- **Código de teste:** `tests/conftest.py` pode ganhar fixture opcional para rodar migrations; nenhum teste existente quebra porque o fallback `create_all` permanece.
- **Operações:** novo runbook de migrations; primeira execução em banco existente precisa de `alembic stamp head` para marcar o estado atual como baseline.
- **Dependências:** `alembic` em `pyproject.toml` `[project.dependencies]` (não opcional — produção precisa).
- **Sem impacto** em: domínios Pydantic, lógica de ranking, formato de `AssistantMessage`, contratos de `RecipeCatalog`/`IngredientInventory`/`RecommendationEngine`/`RecipeAssistant`.

### Non-Goals

- **Não** adicionar Postgres ou outro banco além de SQLite nesta mudança. O suporte multi-backend vem em mudança posterior.
- **Não** criar sistema automático de execução de migrations no startup da aplicação. Migrations são ação operacional explícita (`alembic upgrade head`).
- **Não** migrar dados existentes de bancos SQLite já implantados. Decisão de backfill é responsabilidade do operador (a migration inicial trata schema vazio como baseline via `alembic stamp head`).
- **Não** introduzir ferramentas de expansão/contrato ou zero-downtime migrations. Escopo cobre migrations versionadas lineares.
- **Não** alterar assinatura de `create_session` nem os pontos de injeção de `db_url` usados pelos testes.
