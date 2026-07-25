from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from recipes.infra.database import Base, create_session

REPO_ROOT = Path(__file__).resolve().parent.parent


def _alembic_bin() -> str:
    candidate = shutil.which("alembic")
    if candidate is not None:
        return candidate
    venv_bin = Path(sys.executable).parent / "alembic"
    if venv_bin.is_file():
        return str(venv_bin)
    project_venv = REPO_ROOT / ".venv" / "bin" / "alembic"
    if project_venv.is_file():
        return str(project_venv)
    raise RuntimeError("alembic not found on PATH or in .venv/bin")


def _column_signature(engine, table_name: str) -> set[tuple[str, str, bool]]:
    columns = inspect(engine).get_columns(table_name)
    return {(c["name"], str(c["type"]), bool(c["nullable"])) for c in columns}


def _list_tables(db_path) -> set[str]:
    inspector_engine = create_engine(f"sqlite:///{db_path}")
    try:
        with inspector_engine.connect() as conn:
            return {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
    finally:
        inspector_engine.dispose()


def test_create_session_skips_create_all_when_alembic_version_exists(tmp_path):
    db_path = tmp_path / "managed.db"
    bootstrap_engine = create_engine(f"sqlite:///{db_path}")
    try:
        with bootstrap_engine.begin() as conn:
            conn.execute(
                text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
            )
            conn.execute(
                text("INSERT INTO alembic_version (version_num) VALUES ('abc123')")
            )
    finally:
        bootstrap_engine.dispose()

    create_session(f"sqlite:///{db_path}")
    tables = _list_tables(db_path)

    assert "alembic_version" in tables
    assert "recipes" not in tables
    assert "recipe_sources" not in tables
    assert "ingredients" not in tables
    assert "inventory_items" not in tables


def test_create_session_creates_tables_when_database_is_empty(tmp_path):
    db_path = tmp_path / "fresh.db"

    create_session(f"sqlite:///{db_path}")
    tables = _list_tables(db_path)

    assert {"recipes", "recipe_sources", "ingredients", "inventory_items"}.issubset(
        tables
    )


def test_schema_parity_between_alembic_upgrade_and_create_all(tmp_path):
    migration_path = tmp_path / "migration.db"
    create_all_path = tmp_path / "create_all.db"

    env = os.environ.copy()
    env["RECIPES_DB_URL"] = f"sqlite:///{migration_path}"
    result = subprocess.run(
        [_alembic_bin(), "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"alembic upgrade head failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    create_all_engine = create_engine(f"sqlite:///{create_all_path}")
    try:
        Base.metadata.create_all(create_all_engine)
    finally:
        create_all_engine.dispose()

    migration_engine = create_engine(f"sqlite:///{migration_path}")
    create_all_engine = create_engine(f"sqlite:///{create_all_path}")
    try:
        migration_tables = {
            t
            for t in inspect(migration_engine).get_table_names()
            if t != "alembic_version"
        }
        create_all_tables = set(inspect(create_all_engine).get_table_names())

        assert migration_tables == create_all_tables, (
            f"table set differs: migration={migration_tables} create_all={create_all_tables}"
        )

        for table in migration_tables:
            assert _column_signature(migration_engine, table) == _column_signature(
                create_all_engine, table
            ), f"column signature differs for {table}"
    finally:
        migration_engine.dispose()
        create_all_engine.dispose()
