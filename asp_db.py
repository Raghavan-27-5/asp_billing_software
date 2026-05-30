"""
asp_db.py — Database layer for Adhwaitha Sri Plating Management System.
All schema creation, seeding, and query helpers live here.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from asp_utils import normalize_gstno

# ── Paths ──────────────────────────────────────────────────────────────────────
import sys

if getattr(sys, "frozen", False):
    BASE_DIR: Path = Path(sys.executable).parent
else:
    BASE_DIR: Path = Path(__file__).parent

DATA_DIR: Path = BASE_DIR / "Data"
CPYDB_PATH: Path = BASE_DIR / "cpydb.sqlite"
REPORTS_DIR: Path = BASE_DIR / "Reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── CAT seed data (rate tiers by OD range, extracted from real DB) ─────────────
_CAT_SEED: list[tuple] = [
    ("I",   0,   40,  225.0, 425.0, 450.0, 475.0, 650.0),
    ("II",  41,  50,  225.0, 450.0, 475.0, 550.0, 650.0),
    ("III", 51,  60,  275.0, 525.0, 575.0, 650.0, 725.0),
    ("IV",  61,  85,  325.0, 575.0, 675.0, 750.0, 825.0),
    ("V",   86,  125, 375.0, 725.0, 825.0, 875.0, 925.0),
    ("VI",  126, 150, 450.0, 825.0, 875.0, 925.0, 975.0),
    ("VII", 151, 200, 525.0, 925.0, 950.0, 975.0, 975.0),
]

# ── HD (ledger master) seed from real MDB ────────────────────────────────────
_HD_SEED: list[tuple[str, str, str]] = [
    ("A.Dhanalakshmi(Partner)", "", ""),
    ("Acid Purchase", "", ""),
    ("Advertise ment A/C", "", ""),
    ("Auto Charges", "", ""),
    ("Bank Charges A/C", "", ""),
    ("C.Alagarsamy (Partner)", "", ""),
    ("C.ALAGARSAMY CURRENT A/C", "", ""),
    ("cash", "", ""),
    ("CRYSTAL IND", "MDU", "035456789012345"),
    ("HI TECH ARAI (P) LIMITED", "K Pudur, Madurai", "033456789012345"),
    ("HNM RUBBER PRODUCTS PVT.LTD", "COIMBATORE-641108", "33AABCH7071G1ZS"),
    ("ICICI BANK LTD", "", ""),
    ("JAYAKANTH RUBBER PRIVATE LIMITED",
     "15/A6,1ST PHASE,JIGANI,BANGALORE", "29AACCJ3317N1ZA"),
    ("Job Work", "", ""),
    ("KPM PLASTO RUBBER CO",
     "11/66-E,TRICHY ROAD,RAVATHUR PIRIVU,KANNAMPALAYAM(PO),SULUR,COIMBATORE-641402",
     "33AHTPM1272E1ZD"),
    ("KR INDUSTRIES",
     "A-18, SIPCOT Industrial Park, Irungattukottai, Sriperumbudur Tk., Kancheepuram - 602105",
     "33AACPG4374K1ZS"),
    ("HI-TECH ARAI PRIVATE LIMITED",
     "Shed No.44/1, Sidco Kappalur", "33AAACH3917N1ZJ"),
    ("SHIVA ENTERPRISES RUBBER AND TEFLON (I)",
     "Plot No 5, Survey No. 587/1, Mahakavi Bharathiyar Nagar, Thirumudivakkam Village, Chennai 600 044",
     "33AATCS1265K1ZY"),
    ("Machine A/C", "", ""),
    ("Partner Salary A/c", "", ""),
    ("Petrol Exp", "", ""),
    ("Printing and Stationary Exp", "", ""),
    ("Rent Account", "", ""),
    ("Salary a/C", "", ""),
    ("Wages A/C", "", ""),
]

# ── Stock seed ────────────────────────────────────────────────────────────────
_STOCK_SEED: list[tuple[str, int, str]] = [
    ("COPPER ROD", 0, "Kg"),
    ("COPPER SULPHATE", 0, "Kg"),
    ("NICE POWDER (400)", 0, "Kg"),
    ("EMERY POWDER", 0, "Kg"),
    ("EMERY BRUSH", 0, "Nos"),
    ("AIR BRUSH (BIG & SMALL)", 0, "Nos"),
    ("CHROME SALT", 0, "Kg"),
    ("HCL", 0, "Ltrs"),
    ("COSTIC", 0, "Kg"),
    ("CHROME MIFIRY", 0, "Ltrs"),
    ("HAND CLOVES", 0, "Nos"),
    ("GUMBOOT", 0, "Nos"),
    ("CELLO TAPE", 0, "Nos"),
    ("OIL", 0, "Ltrs"),
]


# ─────────────────────────────────────────────────────────────────────────────
#  Connection helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_cpydb() -> sqlite3.Connection:
    """Return connection to company-selector database."""
    con = sqlite3.connect(str(CPYDB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    _init_cpydb(con)
    return con


def get_year_db(folder: str) -> sqlite3.Connection:
    """Return connection to a year-specific transaction database."""
    path = DATA_DIR / folder / "invsdi.sqlite"
    (DATA_DIR / folder).mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    _init_year_db(con)
    return con


# ─────────────────────────────────────────────────────────────────────────────
#  Schema initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_cpydb(con: sqlite3.Connection) -> None:
    con.executescript("""
    CREATE TABLE IF NOT EXISTS cpydb (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        cpyname TEXT    NOT NULL,
        cpyf    TEXT    NOT NULL UNIQUE,
        syear   INTEGER NOT NULL,
        eyear   INTEGER NOT NULL
    );
    """)
    # Seed default years
    seed = [
        ("Adhwaitha Sri Plating", "ASP2122", 2021, 2022),
        ("Adhwaitha Sri Plating", "ASP2324", 2023, 2024),
        ("Adhwaitha Sri Plating", "ASP2425", 2024, 2025),
    ]
    con.executemany(
        "INSERT OR IGNORE INTO cpydb(cpyname,cpyf,syear,eyear) VALUES (?,?,?,?)",
        seed
    )
    con.commit()


def _init_year_db(con: sqlite3.Connection) -> None:  # noqa: C901
    con.executescript("""
    CREATE TABLE IF NOT EXISTS AutoNo (
        id      INTEGER PRIMARY KEY CHECK (id=1),
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
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        Party   TEXT    NOT NULL UNIQUE,
        sub     TEXT    DEFAULT '',
        PB      INTEGER DEFAULT 0,
        GSTNO   TEXT    DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS CAT (
        CATEGORY TEXT    NOT NULL,
        CAVODF   INTEGER NOT NULL,
        CAVODT   INTEGER NOT NULL,
        A        REAL    DEFAULT 0,
        B        REAL    DEFAULT 0,
        C        REAL    DEFAULT 0,
        D        REAL    DEFAULT 0,
        E        REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS Quotation (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        inwno    TEXT    NOT NULL,
        inwdate  TEXT    DEFAULT '',
        pname    TEXT    DEFAULT '',
        padd     TEXT    DEFAULT '',
        PGSTNO   TEXT    DEFAULT '',
        ref      TEXT    DEFAULT '',
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
        SUB      TEXT    DEFAULT '',
        TAMT     REAL    DEFAULT 0,
        CGST     REAL    DEFAULT 0,
        SGST     REAL    DEFAULT 0,
        IGST     REAL    DEFAULT 0,
        GST      REAL    DEFAULT 0,
        NETAMT   REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS inward (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        inwno    TEXT    NOT NULL,
        inwdate  TEXT    DEFAULT '',
        pname    TEXT    DEFAULT '',
        padd     TEXT    DEFAULT '',
        PGSTNO   TEXT    DEFAULT '',
        ref      TEXT    DEFAULT '',
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
        SUB      TEXT    DEFAULT '',
        TAMT     REAL    DEFAULT 0,
        CGST     REAL    DEFAULT 0,
        SGST     REAL    DEFAULT 0,
        IGST     REAL    DEFAULT 0,
        GST      REAL    DEFAULT 0,
        NETAMT   REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS ItemInward (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        inwno    TEXT    NOT NULL,
        inwdate  TEXT    DEFAULT '',
        pname    TEXT    DEFAULT '',
        padd     TEXT    DEFAULT '',
        PGSTNO   TEXT    DEFAULT '',
        ref      TEXT    DEFAULT '',
        PDC      TEXT    DEFAULT '',
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
        SUB      TEXT    DEFAULT '',
        TAMT     REAL    DEFAULT 0,
        CGST     REAL    DEFAULT 0,
        SGST     REAL    DEFAULT 0,
        IGST     REAL    DEFAULT 0,
        GST      REAL    DEFAULT 0,
        NETAMT   REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS DC (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        inwno    TEXT    NOT NULL,
        inwdate  TEXT    DEFAULT '',
        pname    TEXT    DEFAULT '',
        padd     TEXT    DEFAULT '',
        PGSTNO   TEXT    DEFAULT '',
        ref      TEXT    DEFAULT '',
        PDC      TEXT    DEFAULT '',
        CUSTOMER_DC_NO TEXT DEFAULT '',
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
        SUB      TEXT    DEFAULT '',
        TAMT     REAL    DEFAULT 0,
        CGST     REAL    DEFAULT 0,
        SGST     REAL    DEFAULT 0,
        IGST     REAL    DEFAULT 0,
        GST      REAL    DEFAULT 0,
        NETAMT   REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS BILL (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        inwno    TEXT    NOT NULL,
        inwdate  TEXT    DEFAULT '',
        pname    TEXT    DEFAULT '',
        padd     TEXT    DEFAULT '',
        PGSTNO   TEXT    DEFAULT '',
        ref      TEXT    DEFAULT '',
        PDC      TEXT    DEFAULT '',
        CUSTOMER_DC_NO TEXT DEFAULT '',
        SDPDC    TEXT    DEFAULT '',
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
        SUB      TEXT    DEFAULT '',
        TAMT     REAL    DEFAULT 0,
        CGST     REAL    DEFAULT 0,
        SGST     REAL    DEFAULT 0,
        IGST     REAL    DEFAULT 0,
        GST      REAL    DEFAULT 0,
        NETAMT   REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS purchase (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        pinvno  INTEGER DEFAULT 0,
        pdt     TEXT    NOT NULL,
        pfrom   TEXT    DEFAULT '',
        padd    TEXT    DEFAULT '',
        pname   TEXT    DEFAULT '',
        qty     INTEGER DEFAULT 1,
        amt     REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS PO (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        pono    TEXT    NOT NULL,
        podate  TEXT    NOT NULL,
        vcode   TEXT    DEFAULT '',
        qno     TEXT    DEFAULT '',
        qdate   TEXT    DEFAULT '',
        ref     TEXT    DEFAULT '',
        pname   TEXT    DEFAULT '',
        padd    TEXT    DEFAULT '',
        part    TEXT    DEFAULT '',
        qty     INTEGER DEFAULT 1,
        rate    REAL    DEFAULT 0,
        taxamt  REAL    DEFAULT 0,
        netamt  REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS CqPay (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        vcode    TEXT    DEFAULT '',
        payrecno INTEGER DEFAULT 0,
        pname    TEXT    DEFAULT '',
        padd     TEXT    DEFAULT '',
        bankname TEXT    DEFAULT '',
        cno      TEXT    DEFAULT '',
        cdate    TEXT    DEFAULT '',
        camt     REAL    DEFAULT 0,
        billno   TEXT    DEFAULT '',
        billdate TEXT    DEFAULT '',
        billamt  REAL    DEFAULT 0,
        amtpaid  REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS Data (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        VDate   TEXT    NOT NULL,
        LF      INTEGER DEFAULT 0,
        Part    TEXT    DEFAULT '',
        Part1   TEXT    DEFAULT '',
        Debit   REAL    DEFAULT 0,
        Credit  REAL    DEFAULT 0,
        PrBl    INTEGER DEFAULT 0,
        slno    INTEGER DEFAULT 0,
        Bond    TEXT    DEFAULT '',
        OPBAL   TEXT    DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS Stock (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        pname   TEXT    NOT NULL UNIQUE,
        stock   INTEGER DEFAULT 0,
        units   TEXT    DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS ServTax (
        id   INTEGER PRIMARY KEY CHECK (id=1),
        STax REAL DEFAULT 18,
        SUR  REAL DEFAULT 0,
        HS   REAL DEFAULT 0
    );
    INSERT OR IGNORE INTO ServTax(id,STax,SUR,HS) VALUES (1,18,0,0);

    CREATE TABLE IF NOT EXISTS EMAIL (
        id     INTEGER PRIMARY KEY CHECK (id=1),
        EMAIL  TEXT DEFAULT '',
        PWD    TEXT DEFAULT '',
        SEMAIL TEXT DEFAULT ''
    );
    INSERT OR IGNORE INTO EMAIL(id,EMAIL,PWD,SEMAIL) VALUES (1,'','','');

    CREATE TABLE IF NOT EXISTS KeyT (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        Keydesc TEXT    NOT NULL,
        rate    REAL    DEFAULT 0,
        sq      REAL    DEFAULT 0,
        sq1     REAL    DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS ProductMaster (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        pname   TEXT    NOT NULL UNIQUE,
        hsncode TEXT    DEFAULT '',
        rate    REAL    DEFAULT 0,
        units   TEXT    DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS Sales (
        id    INTEGER PRIMARY KEY AUTOINCREMENT,
        pdt   TEXT NOT NULL,
        pname TEXT DEFAULT '',
        qty   INTEGER DEFAULT 0
    );
    """)

    # Seed CAT if empty
    if con.execute("SELECT COUNT(*) FROM CAT").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO CAT(CATEGORY,CAVODF,CAVODT,A,B,C,D,E) VALUES (?,?,?,?,?,?,?,?)",
            _CAT_SEED
        )

    # Seed HD if empty
    if con.execute("SELECT COUNT(*) FROM HD").fetchone()[0] == 0:
        con.executemany(
            "INSERT OR IGNORE INTO HD(Party,sub,GSTNO) VALUES (?,?,?)",
            _HD_SEED
        )

    # Seed Stock if empty
    if con.execute("SELECT COUNT(*) FROM Stock").fetchone()[0] == 0:
        con.executemany(
            "INSERT OR IGNORE INTO Stock(pname,stock,units) VALUES (?,?,?)",
            _STOCK_SEED
        )

    # Schema migration: add GOODS_VALUE to DC if not present (backward-compat)
    existing_dc_cols = {row[1] for row in con.execute("PRAGMA table_info(DC)").fetchall()}
    if "CUSTOMER_DC_NO" not in existing_dc_cols:
        con.execute("ALTER TABLE DC ADD COLUMN CUSTOMER_DC_NO TEXT DEFAULT ''")
    if "GOODS_VALUE" not in existing_dc_cols:
        con.execute("ALTER TABLE DC ADD COLUMN GOODS_VALUE TEXT DEFAULT ''")

    # Schema migration: add MOULD_VALUE to DC if not present (backward-compat)
    if "MOULD_VALUE" not in existing_dc_cols:
        con.execute("ALTER TABLE DC ADD COLUMN MOULD_VALUE REAL DEFAULT 0")

    # Schema migration: add CUSTOMER_DC_NO to BILL if not present (backward-compat)
    existing_bill_cols = {row[1] for row in con.execute("PRAGMA table_info(BILL)").fetchall()}
    if "CUSTOMER_DC_NO" not in existing_bill_cols:
        con.execute("ALTER TABLE BILL ADD COLUMN CUSTOMER_DC_NO TEXT DEFAULT ''")

    # Schema migration: add IGST to ItemInward if not present (backward-compat)
    existing_ii_cols = {row[1] for row in con.execute("PRAGMA table_info(ItemInward)").fetchall()}
    if "IGST" not in existing_ii_cols:
        con.execute("ALTER TABLE ItemInward ADD COLUMN IGST REAL DEFAULT 0")

    con.commit()


# ─────────────────────────────────────────────────────────────────────────────
#  Query helpers
# ─────────────────────────────────────────────────────────────────────────────

def next_no(con: sqlite3.Connection, field: str) -> int:
    """Atomic increment and return next document number."""
    allowed = {"BILL", "DC", "INW", "Quo", "ItemInw", "PO", "Vch"}
    if field not in allowed:
        raise ValueError(f"Unknown AutoNo field: {field}")
    row = con.execute(f"SELECT {field} FROM AutoNo WHERE id=1").fetchone()
    current: int = row[field] if row and row[field] else 0
    return current + 1


def advance_no(con: sqlite3.Connection, field: str, value: int) -> None:
    """Set AutoNo field to value (only advances, never retreats)."""
    allowed = {"BILL", "DC", "INW", "Quo", "ItemInw", "PO", "Vch"}
    if field not in allowed:
        raise ValueError(f"Unknown AutoNo field: {field}")
    con.execute(
        f"UPDATE AutoNo SET {field}=MAX({field},?) WHERE id=1",
        (value,)
    )
    con.commit()


def upsert_party(con: sqlite3.Connection,
                 party: str, address: str, gstno: str) -> None:
    """Insert or update party in HD master."""
    if not party.strip():
        return
    gst_clean = normalize_gstno(gstno)
    con.execute(
        "INSERT INTO HD(Party,sub,GSTNO) VALUES (?,?,?) "
        "ON CONFLICT(Party) DO UPDATE SET sub=excluded.sub, GSTNO=excluded.GSTNO",
        (party.strip(), address.strip(), gst_clean)
    )
    con.commit()


def lookup_party(con: sqlite3.Connection, prefix: str) -> list[sqlite3.Row]:
    """Return up to 10 parties matching prefix (case-insensitive)."""
    return con.execute(
        "SELECT Party, sub, GSTNO FROM HD "
        "WHERE UPPER(Party) LIKE UPPER(?) ORDER BY Party LIMIT 10",
        (f"{prefix}%",)
    ).fetchall()


def lookup_party_by_gst(con: sqlite3.Connection,
                         gstno: str) -> Optional[sqlite3.Row]:
    """
    Reverse lookup: GST number → party name + address.
    GST numbers are 15 chars; skip inputs shorter than 6 to avoid
    spurious matches while the user is still typing.
    Returns None if not found.
    """
    gstno = normalize_gstno(gstno)
    if len(gstno) < 6:
        return None
    return con.execute(
        "SELECT Party, sub, GSTNO FROM HD "
        "WHERE UPPER(REPLACE(REPLACE(TRIM(GSTNO), ' ', ''), '-', '')) = ? LIMIT 1",
        (gstno,)
    ).fetchone()


def lookup_party_by_gst_external(gstno: str) -> Optional[dict[str, str]]:
    """
    Optional external GST lookup hook.
    Return {'party': ..., 'address': ..., 'gstno': ...} when integrated.
    Current architecture has no configured provider, so this returns None.
    """
    _ = normalize_gstno(gstno)
    return None


def get_all_parties(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute("SELECT Party, sub, GSTNO FROM HD ORDER BY Party").fetchall()


def save_rows(con: sqlite3.Connection, table: str, header: dict,
              rows: list[dict]) -> None:
    """
    Bulk-insert line items for a document.
    header: common fields (inwno, inwdate, pname, padd, PGSTNO, ref, SUB, ...)
    rows: per-line dicts with slno, part, od, guage, qty, rate, AMT keys.
    """
    allowed = {"Quotation", "inward", "ItemInward", "DC", "BILL"}
    if table not in allowed:
        raise ValueError(f"Invalid table: {table}")
    if not rows:
        return

    tamt: float = header.get("TAMT", 0.0)
    cgst: float = header.get("CGST", 0.0)
    sgst: float = header.get("SGST", 0.0)
    igst: float = header.get("IGST", 0.0)
    gst:  float = cgst + sgst + igst
    netamt: float = header.get("NETAMT", 0.0)

    base_cols = ["inwno", "inwdate", "pname", "padd", "PGSTNO",
                 "ref", "SUB", "slno", "part", "od", "guage",
                 "qty", "rate", "AMT", "TAMT", "CGST", "SGST",
                 "IGST", "GST", "NETAMT"]

    extra: dict[str, list[str]] = {
        "ItemInward": ["PDC", "sdidcno", "sdidt"],
        "DC":         ["CUSTOMER_DC_NO", "GOODS_VALUE", "sdidcno", "sdidt"],
        "BILL":       ["PDC", "CUSTOMER_DC_NO", "SDPDC", "sdidcno", "sdidt"],
    }
    extra_cols = extra.get(table, [])
    all_cols = base_cols + extra_cols
    placeholders = ",".join("?" * len(all_cols))
    col_str = ",".join(all_cols)

    # Per-row extra columns (stored per line item, not from header)
    row_extra: dict[str, list[str]] = {
        "DC": ["MOULD_VALUE"],
    }
    row_extra_cols = row_extra.get(table, [])
    all_cols = all_cols + row_extra_cols
    placeholders = ",".join("?" * len(all_cols))
    col_str = ",".join(all_cols)

    records: list[tuple] = []
    for row in rows:
        base_vals: list = [
            header["inwno"], header["inwdate"],
            header.get("pname", ""), header.get("padd", ""),
            header.get("PGSTNO", ""), header.get("ref", ""),
            header.get("SUB", ""),
            row["slno"], row["part"], row["od"], row["guage"],
            row["qty"], row["rate"], row["AMT"],
            tamt, cgst, sgst, igst, gst, netamt,
        ]
        for ec in extra_cols:
            base_vals.append(header.get(ec, ""))
        for rc in row_extra_cols:
            base_vals.append(row.get(rc, 0))
        records.append(tuple(base_vals))

    con.executemany(
        f"INSERT INTO {table}({col_str}) VALUES ({placeholders})",
        records
    )
    con.commit()


def delete_doc(con: sqlite3.Connection, table: str, inwno: str) -> int:
    """Delete all rows for a document number. Returns rows deleted."""
    allowed = {"Quotation", "inward", "ItemInward", "DC", "BILL",
               "purchase", "PO", "CqPay", "Data"}
    if table not in allowed:
        raise ValueError(f"Invalid table: {table}")
    cur = con.execute(f"DELETE FROM {table} WHERE inwno=?", (inwno,))
    con.commit()
    return cur.rowcount


def load_doc(con: sqlite3.Connection, table: str,
             inwno: str) -> list[sqlite3.Row]:
    allowed = {"Quotation", "inward", "ItemInward", "DC", "BILL"}
    if table not in allowed:
        raise ValueError(f"Invalid table: {table}")
    return con.execute(
        f"SELECT * FROM {table} WHERE inwno=? ORDER BY slno",
        (inwno,)
    ).fetchall()


def list_docs(con: sqlite3.Connection, table: str,
              search: str = "") -> list[sqlite3.Row]:
    """Return distinct document summaries, optionally filtered by party name."""
    allowed = {"Quotation", "inward", "ItemInward", "DC", "BILL",
               "purchase", "PO", "Data"}
    if table not in allowed:
        raise ValueError(f"Invalid table: {table}")
    if search:
        return con.execute(
            f"SELECT DISTINCT inwno,inwdate,pname,NETAMT FROM {table} "
            f"WHERE pname LIKE ? ORDER BY CAST(inwno AS INTEGER) DESC LIMIT 300",
            (f"%{search}%",)
        ).fetchall()
    return con.execute(
        f"SELECT DISTINCT inwno,inwdate,pname,NETAMT FROM {table} "
        f"ORDER BY CAST(inwno AS INTEGER) DESC LIMIT 300"
    ).fetchall()


def get_gst_rate(con: sqlite3.Connection) -> float:
    row = con.execute("SELECT STax FROM ServTax WHERE id=1").fetchone()
    return float(row[0]) if row and row[0] else 18.0


def get_cat_rate(con: sqlite3.Connection, od: int,
                 category: str = "B") -> Optional[float]:
    """Look up rate from CAT table for given OD and category column."""
    col_map = {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"}
    col = col_map.get(category.upper(), "B")
    row = con.execute(
        f"SELECT {col} FROM CAT WHERE CAVODF<=? AND CAVODT>=?",
        (od, od)
    ).fetchone()
    return float(row[0]) if row and row[0] else None
