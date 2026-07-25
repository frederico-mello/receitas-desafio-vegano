## Purpose

Defines the versioned schema migration system for the receitas-desafio-vegano project using Alembic, including production/development schema provisioning contracts and operational runbook requirements.

## Requirements

### Requirement: Versioned migrations via Alembic
The project MUST include Alembic configured against the SQLAlchemy `Base.metadata` declared in `src/recipes/infra/database.py`. A first migration MUST exist that creates the `recipes`, `recipe_sources`, `ingredients`, and `inventory_items` tables to match the current `Base.metadata` schema.

#### Scenario: First migration brings an empty database to current schema
- **WHEN** an operator runs `alembic upgrade head` against an empty database
- **THEN** the database contains the `recipes`, `recipe_sources`, `ingredients`, and `inventory_items` tables
- **AND** each table exposes the columns declared by its corresponding SQLAlchemy model

#### Scenario: Alembic environment targets the project metadata
- **WHEN** an operator inspects `alembic/env.py`
- **THEN** `target_metadata` references the `Base` from `src/recipes/infra/database.py`
- **AND** `alembic revision --autogenerate -m <message>` detects schema drift against a migrated database

### Requirement: Production schema provisioning via migrations
In production paths, schema changes MUST be applied through `alembic upgrade head`. The `create_session(db_url)` function MUST NOT invoke `Base.metadata.create_all(engine)` when the target database already contains an `alembic_version` table.

#### Scenario: Production service starts against a migrated database
- **WHEN** `create_session` is called with a `db_url` whose database has an `alembic_version` table
- **THEN** `Base.metadata.create_all(engine)` is NOT invoked
- **AND** no `CREATE TABLE` or `ALTER TABLE` statement is emitted by the service session factory

#### Scenario: Production service starts against an un-migrated database
- **WHEN** `create_session` is called with a `db_url` whose database has no `alembic_version` table and no application tables
- **THEN** the absence is detectable by operators via documented commands
- **AND** the system does NOT silently fall back to `create_all` in production mode (no `PRODUCTION_MODE` env var exists; behavior is governed by the presence of `alembic_version`)

### Requirement: Development and test fallback for schema creation
For development and test workflows, `create_session` MUST invoke `Base.metadata.create_all(engine)` when the target database has no `alembic_version` table, regardless of whether application tables already exist. This preserves the existing convenience flow for tests in `tests/conftest.py` and local SQLite usage.

#### Scenario: Local SQLite dev workflow creates schema implicitly
- **WHEN** a developer runs a service against `sqlite:///data/recipes.db` for the first time
- **THEN** `Base.metadata.create_all(engine)` creates the application tables
- **AND** the developer can use the service without running Alembic first

#### Scenario: Test session continues to provision schema via create_all
- **WHEN** a test instantiates a service with a temporary SQLite URL
- **THEN** `create_session` provisions schema via `Base.metadata.create_all(engine)`
- **AND** the existing test suite passes without any migration pre-step

### Requirement: Baseline stamping for existing databases
Operators MUST be able to mark a database created via `create_all` (with no migration history) as equivalent to the current Alembic head via `alembic stamp head`. After stamping, the production rule applies: subsequent service starts do NOT invoke `create_all`.

#### Scenario: Operator stamps an existing database as baseline
- **WHEN** an operator runs `alembic stamp head` against a database that has the application tables but no `alembic_version` table
- **THEN** the `alembic_version` table is created with the current head revision
- **AND** subsequent `create_session` calls do NOT invoke `create_all`

### Requirement: Schema parity contract test
A test MUST assert that applying migrations on a fresh SQLite database produces a schema equivalent to the one produced by `Base.metadata.create_all()`. "Equivalent" means the same set of tables, and for each table the same set of columns with the same declared types and nullability.

#### Scenario: Parity test on fresh SQLite
- **WHEN** the test provisions one database via `alembic upgrade head` and another via `Base.metadata.create_all(engine)`
- **THEN** both databases expose the same table names
- **AND** for each table, both databases expose the same column names, declared types, and nullability
- **AND** the test fails if any divergence exists

### Requirement: Operational runbook for migrations
A runbook MUST exist at `openwiki/operations/database-migrations.md` documenting the four operational actions: install, generate migration, apply migration, baseline stamp. Each action MUST include the command, its prerequisites, and the expected outcome.

#### Scenario: Operator reads the runbook to apply a migration
- **WHEN** an operator consults `openwiki/operations/database-migrations.md`
- **THEN** the document lists the commands for `alembic upgrade head`, `alembic downgrade -1`, `alembic revision --autogenerate -m "..."`, and `alembic stamp head`
- **AND** each command is preceded by its prerequisite state and followed by its expected outcome
