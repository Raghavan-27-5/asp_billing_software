"""
test_asp.py — Full test suite for Adhwaitha Sri Plating system.
Run: python3 test_asp.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PASS = []
FAIL = []

def ok(name):
    PASS.append(name)
    print(f"  PASS  {name}")

def fail(name, reason):
    FAIL.append((name, reason))
    print(f"  FAIL  {name}: {reason}")

def run(name, fn):
    try:
        fn()
        ok(name)
    except AssertionError as e:
        fail(name, str(e) or "AssertionError")
    except Exception:
        fail(name, traceback.format_exc().strip().splitlines()[-1])

# ── asp_utils ─────────────────────────────────────────────────────────────────

def test_to_float_normal():
    from asp_utils import to_float
    assert to_float("1234.56") == 1234.56
    assert to_float("1,234.56") == 1234.56
    assert to_float(0) == 0.0

def test_to_float_edge():
    from asp_utils import to_float
    assert to_float(None) == 0.0
    assert to_float("") == 0.0
    assert to_float("abc") == 0.0
    assert to_float("  ") == 0.0

def test_parse_date():
    from asp_utils import parse_date
    assert parse_date("21/03/2026") == "21/03/2026"
    assert parse_date("21-03-2026") == "21/03/2026"
    assert parse_date("2026-03-21") == "21/03/2026"
    assert parse_date("garbage") == "garbage"  # pass-through

def test_parse_date_short_year():
    from asp_utils import parse_date
    assert parse_date("21/03/26") == "21/03/2026"

def test_amount_words_basic():
    from asp_utils import amount_words
    w = amount_words(14921.10).lower()
    assert "fourteen thousand" in w
    assert "nine hundred" in w
    assert "twenty one" in w

def test_amount_words_zero():
    from asp_utils import amount_words
    assert "zero" in amount_words(0).lower()

def test_amount_words_crore():
    from asp_utils import amount_words
    w = amount_words(10_000_000).lower()
    assert "one crore" in w

def test_amount_words_paise():
    from asp_utils import amount_words
    w = amount_words(100.50).lower()
    assert "paise fifty" in w

def test_calc_gst_intrastate():
    from asp_utils import calc_gst
    r = calc_gst(12645, 18, "33AATCS1265K1ZY")
    assert r["cgst"] == 1138.05
    assert r["sgst"] == 1138.05
    assert r["igst"] == 0.0
    assert r["total"] == 14921.10

def test_calc_gst_interstate():
    from asp_utils import calc_gst
    r = calc_gst(10000, 18, "29AABCP1234K1ZX")  # Karnataka GSTIN
    assert r["cgst"] == 0.0
    assert r["sgst"] == 0.0
    assert r["igst"] == 1800.0
    assert r["total"] == 11800.0

def test_calc_gst_interstate_maharashtra():
    from asp_utils import calc_gst
    r = calc_gst(1000, 18, "27AACFG6404A1Z2")  # Maharashtra GSTIN
    assert r["cgst"] == 0.0
    assert r["sgst"] == 0.0
    assert r["igst"] == 180.0

def test_calc_gst_no_gstin():
    from asp_utils import calc_gst
    r = calc_gst(1000, 18, "")
    # blank GSTIN → intrastate
    assert r["cgst"] > 0
    assert r["igst"] == 0.0

def test_calc_gst_zero_taxable():
    from asp_utils import calc_gst
    r = calc_gst(0, 18, "33XXXXX")
    assert r["total"] == 0.0

def test_calc_gst_negative_clamp():
    from asp_utils import calc_gst
    r = calc_gst(-100, 18, "33XXXXX")
    assert r["taxable"] == 0.0

def test_calc_gst_malformed_safe():
    from asp_utils import calc_gst
    r = calc_gst(1000, 18, "??bad gst")
    # No crash; treated as non-TN/non-blank => IGST path.
    assert r["igst"] == 180.0

def test_fmt_amt():
    from asp_utils import fmt_amt
    assert fmt_amt(1138.05) == "1138.05"
    assert fmt_amt(0.0) == "0.00"
    assert fmt_amt(14921.1, 2) == "14921.10"

def test_normalize_gstno():
    from asp_utils import normalize_gstno
    assert normalize_gstno(" 29-aabcp1234k1zx ") == "29AABCP1234K1ZX"
    assert normalize_gstno("33 AATCS1265K1ZY") == "33AATCS1265K1ZY"

# ── asp_db ────────────────────────────────────────────────────────────────────

TMP_FOLDER = "TESTDB_SUITE"

def _get_test_con():
    import asp_db
    con = asp_db.get_year_db(TMP_FOLDER)
    return con

def test_db_schema_tables():
    import asp_db
    con = _get_test_con()
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    required = {"AutoNo","BILL","DC","Quotation","inward","ItemInward",
                "HD","CAT","Stock","purchase","PO","CqPay","Data",
                "ServTax","EMAIL","ProductMaster","Sales"}
    missing = required - tables
    assert not missing, f"Missing tables: {missing}"
    con.close()

def test_db_cat_seeded():
    con = _get_test_con()
    n = con.execute("SELECT COUNT(*) FROM CAT").fetchone()[0]
    assert n == 7, f"Expected 7 CAT rows, got {n}"
    con.close()

def test_db_hd_seeded():
    con = _get_test_con()
    n = con.execute("SELECT COUNT(*) FROM HD").fetchone()[0]
    assert n > 10, f"HD should have >10 rows, got {n}"
    con.close()

def test_db_autonumber():
    import asp_db
    con = _get_test_con()
    n = asp_db.next_no(con, "BILL")
    assert n == 1
    asp_db.advance_no(con, "BILL", 5)
    assert asp_db.next_no(con, "BILL") == 6
    asp_db.advance_no(con, "BILL", 3)  # should NOT retreat
    assert asp_db.next_no(con, "BILL") == 6
    con.close()

def test_db_invalid_auto_field():
    import asp_db
    con = _get_test_con()
    try:
        asp_db.next_no(con, "INVALID")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    con.close()

def test_db_upsert_party():
    import asp_db
    con = _get_test_con()
    asp_db.upsert_party(con, "TEST PARTY", "Test Address", "33TESTGST1234")
    row = con.execute("SELECT * FROM HD WHERE Party='TEST PARTY'").fetchone()
    assert row is not None
    assert row["sub"] == "Test Address"
    # Update
    asp_db.upsert_party(con, "TEST PARTY", "New Address", "33NEWGST")
    row2 = con.execute("SELECT * FROM HD WHERE Party='TEST PARTY'").fetchone()
    assert row2["sub"] == "New Address"
    con.close()

def test_db_upsert_party_normalizes_gst():
    import asp_db
    con = _get_test_con()
    asp_db.upsert_party(con, "GST NORMALIZE PARTY", "Addr", " 29-aabcp1234k1zx ")
    row = con.execute("SELECT GSTNO FROM HD WHERE Party='GST NORMALIZE PARTY'").fetchone()
    assert row is not None
    assert row["GSTNO"] == "29AABCP1234K1ZX"
    con.close()

def test_db_upsert_blank_party():
    import asp_db
    con = _get_test_con()
    # Blank party should be silently ignored
    asp_db.upsert_party(con, "", "Address", "GST")
    con.close()

def test_db_lookup_party():
    import asp_db
    con = _get_test_con()
    asp_db.upsert_party(con, "ALPHA INDUSTRIES", "Chennai", "33ALPHA")
    results = asp_db.lookup_party(con, "ALPHA")
    assert any(r["Party"] == "ALPHA INDUSTRIES" for r in results)
    con.close()

def test_db_lookup_party_case_insensitive():
    import asp_db
    con = _get_test_con()
    asp_db.upsert_party(con, "BETA CORP", "Mumbai", "27BETA")
    results = asp_db.lookup_party(con, "beta")
    assert any(r["Party"] == "BETA CORP" for r in results)
    con.close()

def test_db_lookup_party_by_gst_legacy_format():
    import asp_db
    con = _get_test_con()
    legacy_gst = "24-abcde1234f1z5"
    con.execute(
        "INSERT OR REPLACE INTO HD(Party, sub, GSTNO) VALUES (?,?,?)",
        ("LEGACY GST PARTY", "Bangalore", legacy_gst),
    )
    con.commit()
    row = asp_db.lookup_party_by_gst(con, "24ABCDE1234F1Z5")
    assert row is not None
    assert row["Party"] == "LEGACY GST PARTY"
    con.close()

def test_db_save_and_load_doc():
    import asp_db
    con = _get_test_con()
    header = {
        "inwno": "999", "inwdate": "19/03/2026",
        "pname": "SAVE TEST PARTY", "padd": "Chennai",
        "PGSTNO": "33TEST", "ref": "TestRef",
        "SUB": "Hard Chrome", "TAMT": 1000.0,
        "CGST": 90.0, "SGST": 90.0, "IGST": 0.0, "NETAMT": 1180.0,
    }
    rows = [{"slno":1,"part":"Test Part","od":50,"guage":20,
             "qty":2,"rate":500.0,"AMT":1000.0}]
    asp_db.save_rows(con, "Quotation", header, rows)
    loaded = asp_db.load_doc(con, "Quotation", "999")
    assert len(loaded) == 1
    assert loaded[0]["pname"] == "SAVE TEST PARTY"
    assert loaded[0]["AMT"] == 1000.0
    con.close()

def test_db_delete_doc():
    import asp_db
    con = _get_test_con()
    header = {"inwno":"888","inwdate":"01/04/2026","pname":"DEL TEST",
              "padd":"","PGSTNO":"","ref":"","SUB":"",
              "TAMT":0,"CGST":0,"SGST":0,"IGST":0,"NETAMT":0}
    rows = [{"slno":1,"part":"X","od":0,"guage":0,"qty":1,"rate":0,"AMT":0}]
    asp_db.save_rows(con, "DC", header, rows)
    n = asp_db.delete_doc(con, "DC", "888")
    assert n == 1
    assert asp_db.load_doc(con, "DC", "888") == []
    con.close()

def test_db_invalid_table_save():
    import asp_db
    con = _get_test_con()
    try:
        asp_db.save_rows(con, "HACK_TABLE", {}, [{"slno":1,"part":"x","od":0,"guage":0,"qty":1,"rate":0,"AMT":0}])
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    con.close()

def test_db_get_cat_rate():
    import asp_db
    con = _get_test_con()
    rate = asp_db.get_cat_rate(con, 50, "B")
    assert rate == 450.0, f"Expected 450.0 got {rate}"
    rate_none = asp_db.get_cat_rate(con, 999, "B")
    assert rate_none is None
    con.close()

def test_db_list_docs_empty():
    import asp_db
    con = _get_test_con()
    # BILL table is empty in test DB
    docs = asp_db.list_docs(con, "BILL")
    assert isinstance(docs, list)
    con.close()

def test_db_list_docs_with_search():
    import asp_db
    con = _get_test_con()
    docs = asp_db.list_docs(con, "Quotation", "SAVE TEST")
    assert any(d["pname"] == "SAVE TEST PARTY" for d in docs)
    con.close()

# ── asp_print ─────────────────────────────────────────────────────────────────

def _make_print_data(no: str = "1") -> dict:
    return {
        "no": no, "date": "21/03/26",
        "pname": "SHIVA ENTERPRISES RUBBER AND TEFLON (I)",
        "padd": "Plot No 5, Chennai 600 044",
        "gstno": "33AATCS1265K1ZY",
        "sub": "Hard Chrome Plating and Diamond Polishing",
        "ref": "Challan No: 1854",
        "sdpdc": "130",
        "rows": [
            {"part": "GROMMET MOULD", "od": 0, "rate": 11745, "qty": 1, "AMT": 11745},
            {"part": "MSS TRANSPORT", "od": 0, "rate": 200,   "qty": 1, "AMT": 200},
        ],
        "tamt": 11945, "cgst": 1075.05, "sgst": 1075.05, "igst": 0.0, "total": 14095.10
    }

TMP_PDF = Path(tempfile.mkdtemp())

def test_pdf_job_work_bill():
    import asp_print
    p = asp_print.print_job_work_bill(_make_print_data("107"), TMP_PDF, open_pdf=False)
    assert os.path.exists(p)
    assert os.path.getsize(p) > 1000
    with open(p, "rb") as f:
        assert f.read(4) == b"%PDF"

def test_pdf_proforma():
    import asp_print
    p = asp_print.print_proforma(_make_print_data("154"), TMP_PDF, open_pdf=False)
    assert os.path.exists(p)
    assert os.path.getsize(p) > 1000

def test_pdf_quotation():
    import asp_print
    p = asp_print.print_quotation(_make_print_data("50"), TMP_PDF, open_pdf=False)
    assert os.path.exists(p)
    assert os.path.getsize(p) > 1000

def test_pdf_dc():
    import asp_print
    p = asp_print.print_dc(_make_print_data("200"), TMP_PDF, open_pdf=False)
    assert os.path.exists(p)
    assert os.path.getsize(p) > 1000

def test_pdf_empty_rows():
    import asp_print
    data = _make_print_data("0")
    data["rows"] = []
    data["tamt"] = data["cgst"] = data["sgst"] = data["igst"] = data["total"] = 0.0
    p = asp_print.print_proforma(data, TMP_PDF, open_pdf=False)
    assert os.path.exists(p)

def test_pdf_interstate_igst():
    import asp_print
    data = _make_print_data("999")
    data["gstno"] = "29AABCP1234K1ZX"  # Karnataka
    data["cgst"] = 0.0
    data["sgst"] = 0.0
    data["igst"] = 2149.0
    p = asp_print.print_job_work_bill(data, TMP_PDF, open_pdf=False)
    assert os.path.exists(p)

def test_pdf_deterministic():
    """Same input → same file size (ReportLab embeds a timestamp so raw bytes differ,
    but structure and size must be stable to within 2 bytes)."""
    import asp_print
    tmp2 = Path(tempfile.mkdtemp())
    d = _make_print_data("DET")
    p1 = asp_print.print_proforma(d, TMP_PDF, open_pdf=False)
    p2 = asp_print.print_proforma(d, tmp2, open_pdf=False)  # different dir, no overwrite
    s1, s2 = os.path.getsize(p1), os.path.getsize(p2)
    shutil.rmtree(tmp2, ignore_errors=True)
    assert abs(s1 - s2) <= 2, (
        f"PDF sizes differ by {abs(s1-s2)} bytes — layout is not stable"
    )

# ── Performance ───────────────────────────────────────────────────────────────

def test_perf_bulk_insert():
    import asp_db
    con = _get_test_con()
    t0 = time.perf_counter()
    header = {"inwno":"PERF","inwdate":"01/04/2026","pname":"PERF TEST",
              "padd":"","PGSTNO":"","ref":"","SUB":"",
              "TAMT":0,"CGST":0,"SGST":0,"IGST":0,"NETAMT":0}
    rows = [{"slno":i,"part":f"Part {i}","od":50,"guage":25,
             "qty":1,"rate":100.0,"AMT":100.0}
            for i in range(1, 101)]
    asp_db.save_rows(con, "Quotation", header, rows)
    elapsed = time.perf_counter() - t0
    asp_db.delete_doc(con, "Quotation", "PERF")
    con.close()
    assert elapsed < 2.0, f"100-row insert took {elapsed:.2f}s (too slow)"

def test_perf_pdf_generation():
    import asp_print
    t0 = time.perf_counter()
    for i in range(5):
        asp_print.print_job_work_bill(_make_print_data(str(i)), TMP_PDF, open_pdf=False)
    elapsed = time.perf_counter() - t0
    assert elapsed < 10.0, f"5 PDFs took {elapsed:.2f}s"

def test_perf_gst_calc_1000():
    from asp_utils import calc_gst
    t0 = time.perf_counter()
    for i in range(1000):
        calc_gst(float(i * 100), 18, "33AATCS1265K1ZY")
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.5, f"1000 GST calcs took {elapsed:.2f}s"

# ── Cleanup ───────────────────────────────────────────────────────────────────

def cleanup():
    import asp_db
    shutil.rmtree(str(asp_db.DATA_DIR / TMP_FOLDER), ignore_errors=True)
    shutil.rmtree(str(TMP_PDF), ignore_errors=True)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Adhwaitha Sri Plating — Test Suite")
    print("="*60 + "\n")

    groups = [
        ("asp_utils — to_float", [
            test_to_float_normal, test_to_float_edge]),
        ("asp_utils — dates", [
            test_parse_date, test_parse_date_short_year]),
        ("asp_utils — amount_words", [
            test_amount_words_basic, test_amount_words_zero,
            test_amount_words_crore, test_amount_words_paise]),
        ("asp_utils — GST", [
            test_calc_gst_intrastate, test_calc_gst_interstate,
            test_calc_gst_interstate_maharashtra,
            test_calc_gst_no_gstin, test_calc_gst_zero_taxable,
            test_calc_gst_negative_clamp, test_calc_gst_malformed_safe,
            test_fmt_amt,
            test_normalize_gstno]),
        ("asp_db — schema", [
            test_db_schema_tables, test_db_cat_seeded, test_db_hd_seeded]),
        ("asp_db — autonumber", [
            test_db_autonumber, test_db_invalid_auto_field]),
        ("asp_db — party CRUD", [
            test_db_upsert_party, test_db_upsert_blank_party,
            test_db_lookup_party, test_db_lookup_party_case_insensitive,
            test_db_upsert_party_normalizes_gst,
            test_db_lookup_party_by_gst_legacy_format]),
        ("asp_db — documents", [
            test_db_save_and_load_doc, test_db_delete_doc,
            test_db_invalid_table_save, test_db_get_cat_rate,
            test_db_list_docs_empty, test_db_list_docs_with_search]),
        ("asp_print — PDFs", [
            test_pdf_job_work_bill, test_pdf_proforma,
            test_pdf_quotation, test_pdf_dc,
            test_pdf_empty_rows, test_pdf_interstate_igst,
            test_pdf_deterministic]),
        ("Performance", [
            test_perf_bulk_insert, test_perf_pdf_generation,
            test_perf_gst_calc_1000]),
    ]

    for group_name, tests in groups:
        print(f"\n── {group_name} {'─'*(50-len(group_name))}")
        for t in tests:
            run(t.__name__.replace("test_", ""), t)

    cleanup()

    print("\n" + "="*60)
    print(f"  Results: {len(PASS)} passed, {len(FAIL)} failed")
    print("="*60)

    if FAIL:
        print("\nFAILED TESTS:")
        for name, reason in FAIL:
            print(f"  ✗ {name}")
            print(f"    {reason}")
        sys.exit(1)
    else:
        print("\n  All tests passed.")
        sys.exit(0)
