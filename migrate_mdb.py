"""
migrate_mdb.py — One-time migration from original Access .mdb files → SQLite.

This script ONLY needs to be run ONCE, by the developer (Raghavan),
before building the final .exe. The client never runs this.

Requirements on the machine running this script:
  - mdbtools installed  (Linux: apt install mdbtools)
  - The original MDB files present (from the client's old machine)

Usage:
  python3 migrate_mdb.py --mdb-dir /path/to/folder/containing/Data/and/CpyDB.mdb

What it does:
  1. Reads CpyDB.mdb  → populates cpydb.sqlite  (company/year registry)
  2. Reads each year's invsdi.mdb → populates Data/<folder>/invsdi.sqlite
  3. Migrates: HD (party master), CAT (rate tiers), Quotation, DC, BILL,
               inward, ItemInward, purchase, PO, CqPay, Data, Stock,
               ServTax, EMAIL, KeyT, AutoNo, Sales, ProductMaster

After this script finishes, the Data/ folder and cpydb.sqlite are ready
to be bundled into the final .exe via build_exe.bat.
"""

from __future__ import annotations

import argparse
import csv
import io
import sqlite3
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent


def mdb_tables(mdb_path: str) -> list[str]:
    r = subprocess.run(
        ["mdb-tables", "-1", mdb_path],
        capture_output=True, text=True
    )
    return [t.strip() for t in r.stdout.splitlines() if t.strip()]


def mdb_export(mdb_path: str, table: str) -> list[dict[str, str]]:
    r = subprocess.run(
        ["mdb-export", mdb_path, table],
        capture_output=True, text=True
    )
    if not r.stdout.strip():
        return []
    reader = csv.DictReader(io.StringIO(r.stdout))
    return list(reader)


def safe_val(v: str) -> object:
    """Return None for empty strings, else the raw string."""
    return None if v.strip() == "" else v.strip()


def migrate_table(mdb_path: str, table: str,
                  sqlite_con: sqlite3.Connection) -> int:
    rows = mdb_export(mdb_path, table)
    if not rows:
        return 0
    cols = list(rows[0].keys())
    col_str   = ", ".join(f'"{c}"' for c in cols)
    place_str = ", ".join("?" * len(cols))
    inserted  = 0
    for row in rows:
        vals = [safe_val(row[c]) for c in cols]
        try:
            sqlite_con.execute(
                f'INSERT OR IGNORE INTO "{table}"({col_str}) VALUES ({place_str})',
                vals
            )
            inserted += 1
        except sqlite3.Error as e:
            print(f"      ROW SKIP [{table}]: {e}")
    sqlite_con.commit()
    return inserted


def migrate_year(mdb_path: str, folder: str) -> None:
    """Migrate one financial year's invsdi.mdb into SQLite."""
    if not Path(mdb_path).exists():
        print(f"  SKIP — not found: {mdb_path}")
        return

    # Init schema via asp_db (creates all tables + seeds CAT/HD/Stock)
    sys.path.insert(0, str(BASE_DIR))
    import asp_db
    con = asp_db.get_year_db(folder)

    available = mdb_tables(mdb_path)
    print(f"  Tables in MDB: {available}")

    PRIORITY = ["HD", "CAT", "AutoNo", "ServTax", "EMAIL", "Stock",
                "KeyT", "KeyT2", "ProductMaster",
                "Quotation", "inward", "ItemInward", "DC", "BILL",
                "purchase", "PO", "CqPay", "Data", "Sales"]

    ordered = [t for t in PRIORITY if t in available]
    rest    = [t for t in available if t not in PRIORITY]

    for table in ordered + rest:
        n = migrate_table(mdb_path, table, con)
        print(f"    {table:<20} {n:>4} rows")

    con.close()


def migrate_cpydb(mdb_path: str) -> None:
    """Migrate CpyDB.mdb → cpydb.sqlite."""
    if not Path(mdb_path).exists():
        print(f"  SKIP — not found: {mdb_path}")
        return

    sys.path.insert(0, str(BASE_DIR))
    import asp_db
    con = asp_db.get_cpydb()

    rows = mdb_export(mdb_path, "cpydb")
    for r in rows:
        try:
            con.execute(
                "INSERT OR IGNORE INTO cpydb(cpyname,cpyf,syear,eyear) "
                "VALUES (?,?,?,?)",
                (safe_val(r.get("cpyname", "")),
                 safe_val(r.get("cpyf", "")),
                 int(r.get("syear") or 0),
                 int(r.get("eyear") or 0))
            )
        except (sqlite3.Error, ValueError) as e:
            print(f"  cpydb row skip: {e}")
    con.commit()
    print(f"  cpydb: {len(rows)} rows migrated")
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate Adhwaitha Sri Plating MDB → SQLite"
    )
    parser.add_argument(
        "--mdb-dir", default=".",
        help="Directory containing CpyDB.mdb and the Data/ subfolder "
             "(default: current directory)"
    )
    args = parser.parse_args()
    mdb_dir = Path(args.mdb_dir).resolve()

    print(f"\nMigrating from: {mdb_dir}")
    print("=" * 60)

    # 1. Company registry
    cpydb_mdb = mdb_dir / "CpyDB.mdb"
    print(f"\n[1/2] CpyDB: {cpydb_mdb}")
    migrate_cpydb(str(cpydb_mdb))

    # 2. Each financial year
    import asp_db  # type: ignore
    years = asp_db.get_cpydb().execute(
        "SELECT cpyf, syear, eyear FROM cpydb ORDER BY syear"
    ).fetchall()

    for i, yr in enumerate(years, start=2):
        folder  = yr["cpyf"]
        mdb_path = mdb_dir / "Data" / folder / "invsdi.mdb"
        print(f"\n[{i}] FY {yr['syear']}-{yr['eyear']}  ({folder})")
        print(f"     MDB : {mdb_path}")
        print(f"     SQLite: {asp_db.DATA_DIR / folder / 'invsdi.sqlite'}")
        migrate_year(str(mdb_path), folder)

    print("\n" + "=" * 60)
    print("Migration complete.")
    print(f"SQLite files are in: {asp_db.DATA_DIR}")
    print("You can now run  build_exe.bat  to package the .exe.")


if __name__ == "__main__":
    main()
