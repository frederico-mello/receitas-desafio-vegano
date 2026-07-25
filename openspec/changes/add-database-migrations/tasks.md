## 1. Bootstrap Alembic and configuration

- [x] 1.1 Add `alembic` to `[project.dependencies]` in `pyproject.toml` and reinstall with `pip install -e '.[dev]'`
- [x] 1.2 Run `alembic init alembic` at the repository root to scaffold `alembic/` and `alembic.ini`
- [x] 1.3 Edit `alembic/env.py` to import `Base` from `src.recipes.infra.database` and assign `target_metadata = Base.metadata`
- [x] 1.4 Replace the hardcoded `sqlalchemy.url` in `alembic.ini` with an env-driven read of `RECIPES_DB_URL` (falling back to `sqlite:///data/recipes.db`)
- [x] 1.5 Verify `alembic current` runs against an empty temporary SQLite URL without errors

## 2. Initial schema migration

- [x] 2.1 Generate the baseline migration with `alembic revision --autogenerate -m "initial schema"` against a fresh SQLite file
- [x] 2.2 Inspect the generated file under `alembic/versions/` and confirm it creates `recipes`, `recipe_sources`, `ingredients`, and `inventory_items` with the columns declared by `Base.metadata`
- [x] 2.3 Confirm `alembic upgrade head` against an empty SQLite produces those four tables and that `alembic downgrade base` removes them

## 3. Fallback detection in `create_session`

- [x] 3.1 Add a private helper `_should_create_schema(engine)` in `src/recipes/infra/database.py` that returns `False` when `sqlalchemy.inspect(engine).get_table_names()` contains `alembic_version`, and `True` otherwise
- [x] 3.2 Wrap the existing `Base.metadata.create_all(engine)` call inside `create_session` with `_should_create_schema(engine)`
- [x] 3.3 Add unit tests in `tests/test_database.py` (or extend an existing test module) that assert: fresh DB → `create_all` runs; DB with `alembic_version` table present → `create_all` is skipped

## 4. Schema parity contract test

- [x] 4.1 Create `tests/test_database_migrations.py` with helpers that provision two temporary SQLite files (one via `alembic upgrade head`, one via `Base.metadata.create_all`)
- [x] 4.2 Implement the parity assertion: both files must expose the same set of table names and, per table, the same `(name, type, nullable)` tuples for every column, using `sqlalchemy.inspect`
- [x] 4.3 Run the new test together with the existing suite and confirm all tests pass without regression

## 5. Operational runbook and wiki links

- [x] 5.1 Create `openwiki/operations/database-migrations.md` documenting the four actions (install Alembic, generate a migration with `alembic revision --autogenerate`, apply with `alembic upgrade head`, baseline an existing database with `alembic stamp head`), each with prerequisites, command, and expected outcome
- [x] 5.2 Add a link to the new runbook from `openwiki/quickstart.md` and `openwiki/operations/index.md` so operators can discover it
