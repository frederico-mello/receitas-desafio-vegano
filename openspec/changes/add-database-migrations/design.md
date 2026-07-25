## Context

`src/recipes/infra/database.py:74-77` cria schema em toda chamada de `create_session` via `Base.metadata.create_all(engine)`. Sem versionamento, sem histórico, sem revisão. `tests/conftest.py` injeta `src` no `sys.path` mas não força URL — testes confiam no fluxo implícito de `create_all` para provisionar SQLite temporário. OpenWiki lista migrations + DB de produção como item de backlog que destrava API externa, ingestão RAG e troca de banco. Mudança precisa adicionar versionamento sem quebrar a conveniência de dev/test que o projeto já tem.

## Goals / Non-Goals

**Goals:**
- Versionar o schema atual de `Base.metadata` via Alembic, integrando ao mesmo `Base` declarado em `src/recipes/infra/database.py`.
- Manter o caminho de dev/test funcionando: testes novos e existentes continuam a provisionar SQLite temporário sem etapa de migration.
- Detectar bancos já migrados e suprimir o `create_all` redundante, sem introduzir env var ou feature flag.
- Fornecer um teste de contrato que falha se migrations e `create_all` divergirem em tabelas ou colunas.
- Documentar o runbook operacional em `openwiki/operations/database-migrations.md`.

**Non-Goals:**
- Suporte a Postgres ou outro backend além de SQLite. Migrations usam tipos neutros (`String`, `Integer`, `Float`, `DateTime`, `JSON`) que mapeiam para SQLite; sem dialect-specific features.
- Execução automática de migrations no startup da aplicação. Migrations são ação operacional explícita.
- Backfill de dados existentes. A migration inicial trata schema vazio como baseline via `alembic stamp head`; dados em bancos pré-existentes ficam sob responsabilidade do operador.
- Ferramentas de expansão/contrato (expand-contract pattern) ou zero-downtime migrations. Migrations lineares.
- Mudanças nos serviços `RecipeCatalog`, `IngredientInventory`, `RecommendationEngine`, `RecipeAssistant`. A assinatura de `create_session(db_url)` permanece.

## Decisions

### 1. Tooling: Alembic
**Choice:** Alembic (autor do projeto SQLAlchemy).
**Rationale:** Integração nativa com `Base.metadata` via `target_metadata`. CLI padrão (`alembic init`, `revision --autogenerate`, `upgrade head`, `downgrade -1`, `stamp head`). Sem dependências transitivas além de SQLAlchemy já presente.
**Alternatives considered:**
- **yoyo-migrations** — portável entre SQL backends (SQLAlchemy, Alembic, raw SQL). Rejected: adiciona abstração extra sem ganho real para projeto single-backend. Autogenerate de SQLAlchemy é exatamente o que precisamos.
- **Migration escrita à mão sem ferramenta** — viável mas perde autogenerate, diff contra `Base.metadata`, e padrão de equipe. Rejected.

### 2. Layout: `alembic/` na raiz do repositório
**Choice:** Diretório `alembic/` na raiz do repo, contendo `env.py`, `script.py.mako`, `versions/`. Arquivo `alembic.ini` na raiz.
**Rationale:** Convenção padrão do Alembic. Permite `alembic upgrade head` a partir da raiz sem mudar diretório. Não colide com `src/recipes/`.
**Alternatives considered:**
- **Aninhar em `src/recipes/infra/migrations/`** — manteria migrations "dentro" do pacote Python. Rejected: Alembic espera `alembic/` + `alembic.ini` lado a lado; aninhar quebra convenção e exige paths customizados em `env.py` para `script_location`.

### 3. env.py wiring
**Choice:** `alembic/env.py` importa `Base` de `src/recipes/infra/database.py` e define `target_metadata = Base.metadata`. URL do banco vem de variável de ambiente `RECIPES_DB_URL` com fallback para `sqlite:///data/recipes.db` (mesmo default de `create_session`).
**Rationale:** Reaproveita o `Base` existente sem duplicação. `RECIPES_DB_URL` alinha com o uso já implícito de `pydantic-settings` no `pyproject.toml` e abre caminho para `prod-db-config` futuro sem nova renomeação.
**Alternatives considered:**
- **Ler URL de `alembic.ini`** — Alembic suporta `sqlalchemy.url` no ini. Rejected: ini vira source of truth duplicado; env var é mais flexível e combina com setup baseado em settings.
- **Ler URL de um settings object Pydantic** — over-engineering pra esta mudança. Rejected.

### 4. Mecanismo de detecção do fallback `create_all`
**Choice:** Antes de chamar `Base.metadata.create_all(engine)`, `create_session` inspeciona o banco via `sqlalchemy.inspect(engine).get_table_names()`. Se a lista contém `alembic_version`, suprime o `create_all`. Caso contrário, chama `create_all` (cobre banco vazio E banco pré-existente com schema via `create_all` antigo, ambos sem versão Alembic).
**Rationale:** Sem env var, sem feature flag, sem mudança de assinatura. Detecção via introspection usa a própria metadata do Alembic (`alembic_version` é o nome canônico da tabela de versões). Comportamento idêntico ao atual para bancos novos; silencioso para bancos migrados.
**Alternatives considered:**
- **Variável de ambiente `RECIPES_PRODUCTION=1`** suprimiria fallback. Rejected: cria estado implícito fora do schema; mistura config de deployment com config de aplicação.
- **Detectar apenas banco vazio** (zero tabelas). Rejected: bancos já criados via `create_all` antigo ficariam órfãos — todo dev que rodou o sistema uma vez precisaria de `alembic stamp head` manual. Inspeção por `alembic_version` é mais robusta.

### 5. Migration inicial: autogenerate contra `Base.metadata`
**Choice:** Primeira migration gerada via `alembic revision --autogenerate -m "initial schema"` contra um banco vazio. Captura `recipes`, `recipe_sources`, `ingredients`, `inventory_items` como estado baseline.
**Rationale:** Garante que a migration inicial reflete exatamente o schema que `create_all` produziria. Aproxima o ponto de partida de uma instalação existente.
**Alternatives considered:**
- **Escrever migration inicial à mão** — risco de divergência silenciosa com `Base.metadata`. Rejected.
- **Não criar migration inicial e exigir stamp manual em todo banco existente** — empurra trabalho para o operador. Rejected.

### 6. Estratégia de teste de paridade
**Choice:** Teste em `tests/test_database_migrations.py` que (a) cria SQLite temporário A e roda `alembic upgrade head` programaticamente, (b) cria SQLite temporário B e chama `Base.metadata.create_all`, (c) usa `sqlalchemy.inspect` em ambos para extrair `get_table_names()` e `get_columns(table)`, (d) compara conjuntos de tabelas e, por tabela, os pares `(nome, tipo, nullable)`. Falha se houver divergência.
**Rationale:** Cobre o requisito do spec "Schema parity contract" sem dependência de rede ou serviços externos. Roda em <1s em SQLite in-memory.
**Alternatives considered:**
- **Comparar DDL emitido** (`CREATE TABLE` strings) — frágil, ordem de colunas pode variar entre backends. Rejected.
- **Comparar dumps SQL via `sqlite3 .schema`** — binário externo, exige shell. Rejected.

### 7. Onde a checagem de `alembic_version` mora
**Choice:** Dentro de `create_session` em `src/recipes/infra/database.py`. Função privada `_should_create_schema(engine)` encapsula a lógica de inspeção.
**Rationale:** Mantém a mudança contida em um arquivo. Testes existentes que passam `db_url` continuam funcionando; o único efeito observável é que bancos com `alembic_version` não recebem `CREATE TABLE` redundante.
**Alternatives considered:**
- **Criar hook em cada serviço** (`RecipeCatalog`, `IngredientInventory`) para decidir se chamam `create_session` com flag. Rejected: espalha a lógica, viola encapsulamento de `create_session`.
- **Substituir `create_session` por uma fábrica maior** (`DatabaseSession`). Rejected: muda assinatura e quebra todos os call sites sem benefício.

## Risks / Trade-offs

- **Risco:** `alembic_version` table inexistente em produção → `create_all` roda silenciosamente em prod. **Mitigação:** o teste de paridade não cobre este caminho (testa apenas dev/test vs migrations); o runbook em `openwiki/operations/database-migrations.md` documenta `alembic stamp head` como passo obrigatório antes de qualquer deploy em banco pré-existente. Segunda mudança (`prod-db-config`) deve adicionar varredura automatizada.
- **Trade-off:** Manter `create_all` como fallback cria dois caminhos de provisionamento. **Mitigação:** isolados por detecção de `alembic_version`; comportamento observável para o consumidor (`create_session`) é idêntico exceto pela ausência de DDL redundante.
- **Risco:** Autogenerate pode produzir migration com tipos não portáveis se SQLite for trocado por Postgres no futuro. **Mitigação:** documentado em não-objetivos. Mudança futura de backend reescreve migrations.
- **Risco:** `tests/conftest.py` não força URL; testes podem colidir com `sqlite:///data/recipes.db` em CWD de quem roda pytest. **Mitigação:** fora do escopo desta mudança. Pré-existente. Pode ser endereçado em mudança de fixture.
- **Trade-off:** Adicionar `alembic` como dependência obrigatória (`[project.dependencies]`) e não opcional. **Mitigação:** justificado — produção precisa do CLI; tests precisam do módulo para chamar `upgrade` programaticamente.
