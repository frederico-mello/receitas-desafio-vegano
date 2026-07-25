from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, inspect

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


EXPECTED_TABLES = {
    "recipes",
    "recipe_sources",
    "ingredients",
    "inventory_items",
    "alembic_version",
}


def _run_alembic(args: list[str], db_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["RECIPES_DB_URL"] = f"sqlite:///{db_path}"
    return subprocess.run(
        [_alembic_bin(), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_alembic_current_runs_with_env_url() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "smoke.db"
        result = _run_alembic(["current"], db_path)
        assert result.returncode == 0, (
            f"alembic current failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )


def test_alembic_upgrade_head_creates_application_tables() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "upgrade.db"
        result = _run_alembic(["upgrade", "head"], db_path)
        assert result.returncode == 0, (
            f"alembic upgrade head failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )

        engine = create_engine(f"sqlite:///{db_path}")
        try:
            tables = set(inspect(engine).get_table_names())
        finally:
            engine.dispose()

        assert EXPECTED_TABLES.issubset(tables), (
            f"missing tables: {EXPECTED_TABLES - tables}; got {tables}"
        )
