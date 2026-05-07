"""Stage 0.2 smoke test - verifies all v1-required packages import and basic functionality works."""
import sys

print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")
print("-" * 60)

checks = []

def check(name, fn):
    try:
        result = fn()
        checks.append((name, "OK", result))
    except Exception as e:
        checks.append((name, "FAIL", f"{type(e).__name__}: {e}"))

check("pandas",            lambda: __import__("pandas").__version__)
check("numpy",             lambda: __import__("numpy").__version__)
check("scipy",             lambda: __import__("scipy").__version__)
check("pydantic",          lambda: __import__("pydantic").VERSION)
check("yfinance",          lambda: __import__("yfinance").__version__)
check("pandas_datareader", lambda: __import__("pandas_datareader").__version__)
check("duckdb",            lambda: __import__("duckdb").__version__)
check("dash",              lambda: __import__("dash").__version__)
check("plotly",            lambda: __import__("plotly").__version__)
check("dash_ag_grid",      lambda: __import__("dash_ag_grid").__version__)
check("docx (python-docx)",lambda: getattr(__import__("docx"), "__version__", "imported"))
check("openpyxl",          lambda: __import__("openpyxl").__version__)
check("camelot",           lambda: __import__("camelot").__version__)
check("fitz (pymupdf)",    lambda: __import__("fitz").__doc__.splitlines()[0])

# Functional checks - not just imports
check("duckdb in-memory query", lambda: __import__("duckdb").connect().execute("SELECT 42 AS x").fetchone()[0])
check("pydantic BaseModel",     lambda: __import__("pydantic").BaseModel.__name__)

print(f"{'Package':<28} {'Status':<6} Detail")
print("-" * 60)
for name, status, detail in checks:
    print(f"{name:<28} {status:<6} {detail}")

failed = [c for c in checks if c[1] == "FAIL"]
sys.exit(1 if failed else 0)
