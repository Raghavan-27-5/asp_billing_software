"""
asp_db.py — Database layer for Adhwaitha Sri Plating Management System.
Schema matches original MDB exactly. Each document type has independent numbering.
Document chain: Quotation → ItemInward → DC → BILL
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

BASE_DIR: Path = Path(__file__).parent
DATA_DIR: Path = BASE_DIR / "Data"
CPYDB_PATH: Path = BASE_DIR / "cpydb.sqlite"
REPORTS_DIR: Path = BASE_DIR / "Reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

_CAT_SEED = [
    ("I",   0,   40,  225.0, 425.0, 450.0, 475.0, 650.0),
    ("II",  41,  50,  225.0, 450.0, 475.0, 550.0, 650.0),
    ("III", 51,  60,  275.0, 525.0, 575.0, 650.0, 725.0),
    ("IV",  61,  85,  325.0, 575.0, 675.0, 750.0, 825.0),
    ("V",   86,  125, 375.0, 725.0, 825.0, 875.0, 925.0),
    ("VI",  126, 150, 450.0, 825.0, 875.0, 925.0, 975.0),
    ("VII", 151, 200, 525.0, 925.0, 950.0, 975.0, 975.0),
]

_HD_SEED = [
    ("A.Dhanalakshmi(Partner)", "", ""),
    ("Acid Purchase", "", ""),
    ("Auto Charges", "", ""),
    ("Bank Charges A/C", "", ""),
    ("C.Alagarsamy (Partner)", "", ""),
    ("cash", "", ""),
    ("CRYSTAL IND", "MDU", "035456789012345"),
    ("HI TECH ARAI (P) LIMITED", "K Pudur, Madurai", "033456789012345"),
    ("HNM RUBBER PRODUCTS PVT.LTD", "COIMBATORE-641108", "33AABCH7071G1ZS"),
    ("ICICI BANK LTD", "", ""),
    ("JAYAKANTH RUBBER PRIVATE LIMITED",
     "15/A6,1ST PHASE,JIGANI,BANGALORE", "29AACCJ3317N1ZA"),
    ("KPM PLASTO RUBBER CO",
     "11/66-E,TRICHY ROAD,RAVATHUR PIRIVU,KANNAMPALAYAM(PO),SULUR,COIMBATORE-641402",
     "33AHTPM1272E1ZD"),
    ("KR INDUSTRIES",
     "A-18, SIPCOT Industrial Park, Irungattukottai", "33AACPG4374K1ZS"),
    ("HI-TECH ARAI PRIVATE LIMITED",
     "Shed No.44/1, Sidco Kappalur", "33AAACH3917N1ZJ"),
    ("HI TECH ARAI PVT LTD U-IV",
     "2726/1, Sidco Industrial Estate, K Pudur, Madurai-625007", "33AAACH3917N1ZJ"),
    ("SHIVA ENTERPRISES RUBBER AND TEFLON (I)",
     "Plot No 5, Survey No. 587/1, Mahakavi Bharathiyar Nagar, "
     "Thirumudivakkam Village, Chennai 600 044", "33AATCS1265K1ZY"),
    ("Machine A/C", "", ""),
    ("Partner Salary A/c", "", ""),
    ("Petrol Exp", "", ""),
    ("Printing and Stationary Exp", "", ""),
    ("Rent Account", "", ""),
    ("Salary a/C", "", ""),
    ("Wages A/C", "", ""),
    ("EDIZI TOOLS PVT.LTD.", "", ""),
]

_STOCK_SEED = [
    ("COPPER ROD", 0, "Kg"), ("COPPER SULPHATE", 0, "Kg"),
    ("NICE POWDER (400)", 0, "Kg"), ("EMERY POWDER", 0, "Kg"),
    ("EMERY BRUSH", 0, "Nos"), ("CHROME SALT", 0, "Kg"),
    ("HCL", 0, "Ltrs"), ("COSTIC", 0, "Kg"), ("OIL", 0, "Ltrs"),
]

# Shared transaction columns matching original MDB exactly
_TXN_BASE = """
    inwno    TEXT    DEFAULT '',
    inwdate  TEXT    DEFAULT '',
    pname    TEXT    DEFAULT '',
    padd     TEXT    DEFAULT '',
    PGSTNO   TEXT    DEFAULT '',
    ref      TEXT    DEFAULT '',
    SUB      TEXT    DEFAULT '',
    ono      TEXT    DEFAULT '',
    odt      TEXT    DEFAULT '',
    dcno     TEXT    DEFAULT '',
    dcdt     TEXT    DEFAULT '',
    dt       TEXT    DEFAULT '',
    dtdt     TEXT    DEFAULT '',
    slno     INTEGER DEFAULT 1,
    part     TEXT    DEFAULT '',
    od       INTEGER DEFAULT 0,
    guage    INTEGER DEFAULT 0,
    qty      INTEGER DEFAULT 1,
    sdidcno  TEXT    DEFAULT '',
    sdidt    TEXT    DEFAULT '',
    mcat     TEXT    DEFAULT '',
    gside    TEXT    DEFAULT '',
    rate     REAL    DEFAULT 0,
    AMT      REAL    DEFAULT 0,
    TOTAL    REAL    DEFAULT 0,
    TAMT     REAL    DEFAULT 0,
    CGST     REAL    DEFAULT 0,
    SGST     REAL    DEFAULT 0,
    IGST     REAL    DEFAULT 0,
    GST      REAL    DEFAULT 0,
    NETAMT   REAL    DEFAULT 0
"""


def get_cpydb() -> sqlite3.Connection:
    con = sqlite3.connect(str(CPYDB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    _init_cpydb(con)
    return con


def get_year_db(folder: str) -> sqlite3.Connection:
    path = DATA_DIR / folder / "invsdi.sqlite"
    (DATA_DIR / folder).mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    _init_year_db(con)
    return con


def _init_cpydb(con: sqlite3.Connection) -> None:
    con.executescript("""
    CREATE TABLE IF NOT EXISTS cpydb (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        cpyname TEXT NOT NULL,
        cpyf    TEXT NOT NULL UNIQUE,
        syear   INTEGER NOT NULL,
        eyear   INTEGER NOT NULL
    );
    """)
    for r in [
        ("Adhwaitha Sri Plating", "ASP2122", 2021, 2022),
        ("Adhwaitha Sri Plating", "ASP2324", 2023, 2024),
        ("Adhwaitha Sri Plating", "ASP2425", 2024, 2025),
    ]:
        con.execute(
            "INSERT OR IGNORE INTO cpydb(cpyname,cpyf,syear,eyear) "
            "VALUES (?,?,?,?)", r)
    con.commit()


def _init_year_db(con: sqlite3.Connection) -> None:
    con.executescript(f"""
    CREATE TABLE IF NOT EXISTS AutoNo (
        id      INTEGER PRIMARY KEY CHECK(id=1),
        BILL    INTEGER DEFAULT 0,
        DC      INTEGER DEFAULT 0,
        INW     INTEGER DEFAULT 0,
        Quo     INTEGER DEFAULT 0,
        ItemInw INTEGER DEFAULT 0,
        PO      INTEGER DEFAULT 0,
        Vch     INTEGER DEFAULT 0
    );
    INSERT OR IGNORE INTO AutoNo(id,BILL,DC,INW,Quo,ItemInw,PO,Vch)
        VALUES (1,0,0,0,0,0,0,0);

    CREATE TABLE IF NOT EXISTS HD (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        Party TEXT NOT NULL UNIQUE,
        sub   TEXT DEFAULT '',
        PB    INTEGER DEFAULT 0,
        GSTNO TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS CAT (
        CATEGORY TEXT, CAVODF INTEGER, CAVODT INTEGER,
        A REAL DEFAULT 0, B REAL DEFAULT 0, C REAL DEFAULT 0,
        D REAL DEFAULT 0, E REAL DEFAULT 0
    );

    -- Quotation: origin of the chain
    CREATE TABLE IF NOT EXISTS Quotation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {_TXN_BASE}
    );

    -- ItemInward: loads from Quotation, adds D.Slip No
    CREATE TABLE IF NOT EXISTS ItemInward (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        {_TXN_BASE},
        PDC      TEXT DEFAULT '',
        dslip    TEXT DEFAULT '',
        quot_ref TEXT DEFAULT ''
    );

    -- inward: legacy table kept for migration compatibility
    CREATE TABLE IF NOT EXISTS inward (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {_TXN_BASE}
    );

    -- DC: loads from ItemInward, adds D.Slip No
    CREATE TABLE IF NOT EXISTS DC (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        {_TXN_BASE},
        PDC      TEXT DEFAULT '',
        dslip    TEXT DEFAULT '',
        inw_ref  TEXT DEFAULT ''
    );

    -- BILL: loads from DC, adds ASP DC Details + Pro Inv No
    CREATE TABLE IF NOT EXISTS BILL (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        {_TXN_BASE},
        PDC      TEXT DEFAULT '',
        SDPDC    TEXT DEFAULT '',
        dslip    TEXT DEFAULT '',
        dc_ref   TEXT DEFAULT '',
        dc_date  TEXT DEFAULT '',
        pro_inv  TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS purchase (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pinvno INTEGER DEFAULT 0, pdt TEXT DEFAULT '',
        pfrom TEXT DEFAULT '', padd TEXT DEFAULT '',
        pname TEXT DEFAULT '', qty INTEGER DEFAULT 1,
        amt REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS PO (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pono TEXT DEFAULT '', podate TEXT DEFAULT '',
        pname TEXT DEFAULT '', padd TEXT DEFAULT '',
        part TEXT DEFAULT '', qty INTEGER DEFAULT 1,
        rate REAL DEFAULT 0, ref TEXT DEFAULT '',
        netamt REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS CqPay (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pname TEXT DEFAULT '', padd TEXT DEFAULT '',
        bankname TEXT DEFAULT '', cno TEXT DEFAULT '',
        cdate TEXT DEFAULT '', camt REAL DEFAULT 0,
        billno TEXT DEFAULT '', billdate TEXT DEFAULT '',
        billamt REAL DEFAULT 0, amtpaid REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS Data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        VDate TEXT DEFAULT '', LF INTEGER DEFAULT 0,
        Part TEXT DEFAULT '', Part1 TEXT DEFAULT '',
        Debit REAL DEFAULT 0, Credit REAL DEFAULT 0,
        PrBl INTEGER DEFAULT 0, slno INTEGER DEFAULT 0,
        Bond TEXT DEFAULT '', OPBAL TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS Stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pname TEXT NOT NULL UNIQUE,
        stock INTEGER DEFAULT 0,
        units TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS ServTax (
        id INTEGER PRIMARY KEY CHECK(id=1),
        STax REAL DEFAULT 18, SUR REAL DEFAULT 0, HS REAL DEFAULT 0
    );
    INSERT OR IGNORE INTO ServTax(id,STax,SUR,HS) VALUES (1,18,0,0);

    CREATE TABLE IF NOT EXISTS EMAIL (
        id INTEGER PRIMARY KEY CHECK(id=1),
        EMAIL TEXT DEFAULT '', PWD TEXT DEFAULT '',
        SEMAIL TEXT DEFAULT ''
    );
    INSERT OR IGNORE INTO EMAIL(id,EMAIL,PWD,SEMAIL) VALUES (1,'','','');

    CREATE TABLE IF NOT EXISTS KeyT (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Keydesc TEXT NOT NULL, rate REAL DEFAULT 0,
        sq REAL DEFAULT 0, sq1 REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS ProductMaster (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pname TEXT NOT NULL UNIQUE, hsncode TEXT DEFAULT '',
        rate REAL DEFAULT 0, units TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS Sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pdt TEXT DEFAULT '', pname TEXT DEFAULT '',
        qty INTEGER DEFAULT 0
    );
    """)

    if con.execute("SELECT COUNT(*) FROM CAT").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO CAT(CATEGORY,CAVODF,CAVODT,A,B,C,D,E) "
            "VALUES (?,?,?,?,?,?,?,?)", _CAT_SEED)
    if con.execute("SELECT COUNT(*) FROM HD").fetchone()[0] == 0:
        con.executemany(
            "INSERT OR IGNORE INTO HD(Party,sub,GSTNO) VALUES (?,?,?)",
            _HD_SEED)
    if con.execute("SELECT COUNT(*) FROM Stock").fetchone()[0] == 0:
        con.executemany(
            "INSERT OR IGNORE INTO Stock(pname,stock,units) VALUES (?,?,?)",
            _STOCK_SEED)
    con.commit()


# ── AutoNumber helpers ────────────────────────────────────────────────────────

def next_no(con: sqlite3.Connection, field: str) -> int:
    _ok = {"BILL", "DC", "INW", "Quo", "ItemInw", "PO", "Vch"}
    if field not in _ok:
        raise ValueError(f"Unknown AutoNo field: {field}")
    row = con.execute(f"SELECT {field} FROM AutoNo WHERE id=1").fetchone()
    return (row[field] or 0) + 1


def advance_no(con: sqlite3.Connection, field: str, value: int) -> None:
    _ok = {"BILL", "DC", "INW", "Quo", "ItemInw", "PO", "Vch"}
    if field not in _ok:
        raise ValueError(f"Unknown AutoNo field: {field}")
    con.execute(
        f"UPDATE AutoNo SET {field}=MAX({field},?) WHERE id=1", (value,))
    con.commit()


# ── Party helpers ─────────────────────────────────────────────────────────────

def upsert_party(con: sqlite3.Connection,
                  party: str, address: str, gstno: str) -> None:
    if not party.strip():
        return
    con.execute(
        "INSERT INTO HD(Party,sub,GSTNO) VALUES (?,?,?) "
        "ON CONFLICT(Party) DO UPDATE SET "
        "sub=excluded.sub, GSTNO=excluded.GSTNO",
        (party.strip(), address.strip(), gstno.strip()))
    con.commit()


def lookup_party(con: sqlite3.Connection,
                  prefix: str) -> list[sqlite3.Row]:
    return con.execute(
        "SELECT Party,sub,GSTNO FROM HD "
        "WHERE UPPER(Party) LIKE UPPER(?) ORDER BY Party LIMIT 20",
        (f"{prefix}%",)).fetchall()


def lookup_party_by_gst(con: sqlite3.Connection,
                         gstno: str) -> Optional[sqlite3.Row]:
    gstno = gstno.strip().upper()
    if len(gstno) < 6:
        return None
    return con.execute(
        "SELECT Party,sub,GSTNO FROM HD "
        "WHERE UPPER(TRIM(GSTNO))=? LIMIT 1",
        (gstno,)).fetchone()


def get_all_parties(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute(
        "SELECT Party,sub,GSTNO FROM HD ORDER BY Party").fetchall()


def get_all_party_names(con: sqlite3.Connection) -> list[str]:
    return [r["Party"] for r in con.execute(
        "SELECT Party FROM HD ORDER BY Party").fetchall()]


# ── Document CRUD ─────────────────────────────────────────────────────────────

_VALID_TABLES = {"Quotation", "inward", "ItemInward", "DC", "BILL",
                 "purchase", "PO", "CqPay", "Data"}

# Extra columns per table beyond the shared base
_EXTRA_COLS: dict[str, list[str]] = {
    "ItemInward": ["PDC", "dslip", "quot_ref"],
    "DC":         ["PDC", "dslip", "inw_ref"],
    "BILL":       ["PDC", "SDPDC", "dslip", "dc_ref", "dc_date", "pro_inv"],
}

_BASE_COLS = [
    "inwno", "inwdate", "pname", "padd", "PGSTNO", "ref", "SUB",
    "ono", "odt", "dcno", "dcdt", "dt", "dtdt",
    "slno", "part", "od", "guage", "qty",
    "sdidcno", "sdidt", "mcat", "gside",
    "rate", "AMT", "TOTAL", "TAMT", "CGST", "SGST", "IGST", "GST", "NETAMT",
]


def load_doc(con: sqlite3.Connection, table: str,
             inwno: str) -> list[sqlite3.Row]:
    if table not in _VALID_TABLES:
        raise ValueError(f"Invalid table: {table}")
    return con.execute(
        f"SELECT * FROM {table} WHERE inwno=? ORDER BY slno",
        (inwno,)).fetchall()


def list_docs(con: sqlite3.Connection, table: str,
              search: str = "") -> list[sqlite3.Row]:
    if table not in _VALID_TABLES:
        raise ValueError(f"Invalid table: {table}")
    if search:
        return con.execute(
            f"SELECT DISTINCT inwno,inwdate,pname,NETAMT FROM {table} "
            f"WHERE pname LIKE ? "
            f"ORDER BY CAST(inwno AS INTEGER) DESC LIMIT 300",
            (f"%{search}%",)).fetchall()
    return con.execute(
        f"SELECT DISTINCT inwno,inwdate,pname,NETAMT FROM {table} "
        f"ORDER BY CAST(inwno AS INTEGER) DESC LIMIT 300").fetchall()


def save_doc_rows(con: sqlite3.Connection, table: str,
                  header: dict, rows: list[dict]) -> None:
    """
    Atomic save: delete existing rows for inwno then bulk-insert.
    header: document-level fields (pname, dates, GST totals, chain refs…)
    rows: line items (slno, part, od, guage, qty, rate, AMT)
    """
    if table not in {"Quotation", "inward", "ItemInward", "DC", "BILL"}:
        raise ValueError(f"Invalid table: {table}")
    if not rows:
        return

    con.execute(f"DELETE FROM {table} WHERE inwno=?", (header["inwno"],))

    all_cols = _BASE_COLS + _EXTRA_COLS.get(table, [])
    col_str   = ",".join(f'"{c}"' for c in all_cols)
    place_str = ",".join("?" * len(all_cols))

    records: list[tuple] = []
    for row in rows:
        vals = []
        for col in all_cols:
            # Row-level fields take priority over header
            if col in row and row[col] is not None:
                vals.append(row[col])
            elif col in header:
                vals.append(header[col])
            else:
                vals.append(None)
        records.append(tuple(vals))

    con.executemany(
        f"INSERT INTO {table}({col_str}) VALUES ({place_str})", records)
    con.commit()


def delete_doc(con: sqlite3.Connection, table: str,
               inwno: str) -> int:
    if table not in _VALID_TABLES:
        raise ValueError(f"Invalid table: {table}")
    cur = con.execute(f"DELETE FROM {table} WHERE inwno=?", (inwno,))
    con.commit()
    return cur.rowcount


def get_gst_rate(con: sqlite3.Connection) -> float:
    row = con.execute("SELECT STax FROM ServTax WHERE id=1").fetchone()
    return float(row[0]) if row and row[0] else 18.0