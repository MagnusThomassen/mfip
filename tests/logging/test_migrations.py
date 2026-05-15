"""Tests for the mfip/logging/migrations/ package and the
discovery runner in scripts/init_db.py.

Discovery semantics:
- Files matching ``[0-9][0-9][0-9]_*.py`` are migration modules.
- Sort key is the integer prefix (so ``009`` precedes ``010`` and
  the sort still works if a future contributor accidentally types a
  one- or two-digit prefix).
- Each module exports ``description: str`` and
  ``transform(row, table_name) -> dict | None``.

`scripts/` is not a Python package; we load `init_db.py` by file
path via importlib.util so the test doesn't depend on shell PYTHONPATH.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INIT_DB_PATH = REPO_ROOT / "scripts" / "init_db.py"


def _load_init_db_module():
    """Load scripts/init_db.py as a module without polluting sys.path."""
    spec = importlib.util.spec_from_file_location(
        "_test_init_db", INIT_DB_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("_test_init_db", module)
    spec.loader.exec_module(module)
    return module


def test_discover_migrations_returns_migration_001_with_required_exports():
    """Migration 001 (severity Title-case) is the first entry and
    exports both `description` and a callable `transform`."""
    init_db = _load_init_db_module()
    migrations = init_db._discover_migrations()
    assert len(migrations) >= 1, "expected at least migration 001"

    name, module = migrations[0]
    assert name == "001_severity_title_case.py"
    assert hasattr(module, "description")
    assert isinstance(module.description, str) and module.description.strip()
    assert hasattr(module, "transform") and callable(module.transform)


def test_discover_migrations_returns_numeric_order():
    """Migrations are discovered in numeric prefix order, not
    alphabetic. Verifies 001 < 002 < … < 010 < … < 099 < 100.

    Within the zero-padded 001-999 namespace, lexical sort and
    integer sort agree, but the discovery contract is integer
    sort. The assertion below would still pass under a lexical
    sort today; it serves as a regression guard if the discovery
    function is ever weakened or if a non-padded prefix slips in.
    """
    init_db = _load_init_db_module()
    migrations = init_db._discover_migrations()
    filenames = [name for name, _ in migrations]
    int_prefixes = [int(name.split("_", 1)[0]) for name in filenames]
    assert int_prefixes == sorted(int_prefixes), (
        f"migrations not in numeric order: {filenames}"
    )
