"""Run sql/NN_*.sql in order with DuckDB (in memory), export every out_* table to data/output/<name>.csv,
then sql/99_tests.sql (table `tests`: test, passed, detail) to data/output/tests.csv.
Exit code 1 if any test fails. Run from the repository root:  python src/run_sql.py
"""
from __future__ import annotations

import os
import sys

import duckdb

from common import OUT, ROOT


def main() -> int:
    os.chdir(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for f in sorted((ROOT / "sql").glob("[0-9][0-9]_*.sql")):
        try:
            con.execute(f.read_text(encoding="utf-8"))
        except duckdb.Error as exc:
            print("ERROR in", f.name, "->", str(exc)[:300])
            return 1
        print("ran", f.name)
    tables = [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'out_%' ORDER BY 1").fetchall()]
    for t in tables:
        con.execute(f"COPY {t} TO 'data/output/{t[4:]}.csv' (HEADER)")
    print("exported", len(tables), "tables to data/output/")
    if not con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tests'").fetchone()[0]:
        print("no `tests` table: sql/99_tests.sql must create it")
        return 1
    res = con.execute("SELECT test, passed, detail FROM tests ORDER BY test").fetchall()
    failed = [r for r in res if not r[1]]
    print(f"tests: {len(res) - len(failed)}/{len(res)} passed")
    for r in failed:
        print("  FAIL", r[0], "|", r[2])
    con.execute("COPY tests TO 'data/output/tests.csv' (HEADER)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
