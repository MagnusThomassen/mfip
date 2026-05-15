"""
Migration registry for the MFIP logging schema.

Each migration lives in a numbered file (NNN_description.py) and
exports:

- description: str
- transform(row: dict, table_name: str) -> dict | None

Migrations are discovered by scripts/init_db.py's --migrate
runner and applied in numeric order. See decisions.md
2026-05-15 entry "Migrations module refactor: discoverable
package" for rationale.
"""
