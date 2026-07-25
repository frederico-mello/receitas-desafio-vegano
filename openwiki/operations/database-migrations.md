---
type: Operations Guide
title: Database migrations runbook
description: Operational reference for Alembic migrations in the receitas-desafio-vegano project: install, generate, apply, and baseline-stamp a database.
tags: [operations, migrations, alembic, sqlite]
---

# Database migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for versioned schema migrations. `Base.metadata` from `src/recipes/infra/database.py` is the source of truth; the initial migration captures the existing schema as the baseline. The `create_session` helper still falls back to `Base.metadata.create_all` when the database is unmanaged (no `alembic_version` table) so that tests and local dev keep working without a migration step.

All commands run from the repository root. Set `RECIPES_DB_URL` to point at the target database; the default is `sqlite:///data/recipes.db`.

## Install

**Prerequisite:** Python environment with the project installed (`pip install -e '.[dev]'`). Alembic is declared in `[project.dependencies]` of `pyproject.toml`, so the editable install pulls it in.

**Expected outcome:** `.venv/bin/alembic --version` prints the Alembic release.

## Generate a migration

**Prerequisite:** A clean or empty database (the autogenerate diff is taken against the database referenced by `RECIPES_DB_URL`).

```bash
RECIPES_DB_URL="sqlite:///tmp/empty.db" \
  alembic revision --autogenerate -m "describe the change"
```

The new revision lands under `alembic/versions/` with the next sequential prefix.

**Expected outcome:** a new file appears under `alembic/versions/` with `upgrade()` and `downgrade()` functions. Inspect the file before committing; autogenerate cannot detect renames, column type changes within the same dialect, or check constraints.

## Apply a migration

**Prerequisite:** the target database exists and is reachable via `RECIPES_DB_URL`.

```bash
RECIPES_DB_URL="sqlite:///data/recipes.db" alembic upgrade head
```

For incremental application, replace `head` with a target revision id.

**Expected outcome:** the database schema advances to the requested revision; the `alembic_version` table records the current head.

## Rollback

**Prerequisite:** the database is at or beyond the revision you want to revert.

```bash
RECIPES_DB_URL="sqlite:///data/recipes.db" alembic downgrade -1
```

Use a specific revision id to roll back further than one step.

**Expected outcome:** schema reverts one revision; the `alembic_version` row updates accordingly.

## Baseline an existing database

Use this when a database was previously provisioned by `Base.metadata.create_all` and has no `alembic_version` table yet. The command marks the database as equivalent to the current head without running any DDL.

```bash
RECIPES_DB_URL="sqlite:///data/recipes.db" alembic stamp head
```

**Expected outcome:** the `alembic_version` table is created with the current head revision. Subsequent `create_session` calls no longer invoke `create_all`, and future schema changes flow through `alembic upgrade head`.
