"""
asp_print.py — PDF generation for all document types.
Layout reverse-engineered from high-quality scans (Images 9 & 10).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from asp_utils import amount_words, fmt_amt

S_DEITY   = ParagraphStyle("deity",   fontName="Times-Italic",  fontSize=8,  alignment=TA_CENTER, leading=10)
S_CO_NAME = ParagraphStyle("coname",  fontName="Times-Bold",    fontSize=22, alignment=TA_CENTER, leading=26)
S_CO_ADDR = ParagraphStyle("coaddr",  fontName="Times-Roman",   fontSize=8,  alignment=TA_CENTER, leading=11)
S_SECTION = ParagraphStyle("section", fontName="Times-Bold",    fontSize=11, alignment=TA_CENTER, leading=14)
S_NORMAL  = ParagraphStyle("normal",  fontName="Times-Roman",   fontSize=9,  leading=12)
S_SMALL   = ParagraphStyle("small",   fontName="Times-Roman",   fontSize=8,  leading=10)
S_BOLD    = ParagraphStyle("bold",    fontName="Times-Bold",    fontSize=9,  leading=12)
S_RIGHT   = ParagraphStyle("right",   fontName="Times-Roman",   fontSize=9,  alignment=TA_RIGHT, leading=12)
S_RIGHT_B = ParagraphStyle("rightb",  fontName="Times-Bold",    fontSize=9,  alignment=TA_RIGHT, leading=12)
S_CENTER  = ParagraphStyle("center",  fontName="Times-Roman",   fontSize=9,  alignment=TA_CENTER, leading=12)
S_SMALL_B = ParagraphStyle("smallb",  fontName="Times-Bold",    fontSize=8,  leading=10)

COMPANY: dict[str, str] = {
    "name":  "Adhwaitha Sri Plating",
    "deity": "Thiruvattai Iyanar Thunai",
    "addr1": "Fac.: SF.No.233, Plot No.: C 26 , Electro Plating Industrial Park,",
    "addr2": "D.Karisalkulam, Manamadurai Taluk ,Sivagangai District.",
    "addr3": "Tamilnadu, 630411. Mobile No. 63693 73649, 99944 43530",
    "addr4": "Off. : Old No.85 J/2, New No.76, Arunachalam Street, S.S.Colony North Gate,Madurai-16.",
    "gstno": "33ADZPA3791Q2ZP",
    "state": "33",
    "hsn":   "75089010",
    "sign":  "A. Dhanalakshmi",
}


def _open_pdf(path: str) -> None:
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _company_header(story: list) -> None:
    story.append(Paragraph(COMPANY["deity"], S_DEITY))
    story.append(Paragraph(f"<b>{COMPANY['name']}</b>", S_CO_NAME))
    for k in ("addr1", "addr2", "addr3", "addr4"):
        story.append(Paragraph(COMPANY[k], S_CO_ADDR))
    story.append(Spacer(1, 2 * mm))
    t = Table([[
        Paragraph(f"State Code : {COMPANY['state']}", S_SMALL),
        Paragraph(f"GST No. : {COMPANY['gstno']}", S_RIGHT),
    ]], colWidths=[90 * mm, 90 * mm])
    t.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    story.append(Spacer(1, 3 * mm))


def _party_block(story: list, data: dict[str, Any],
                 doc_type: str, no_label: str) -> None:
    story.append(Paragraph(f"<b>{doc_type}</b>", S_SECTION))
    if doc_type == "JOB WORK BILL":
        story.append(Paragraph("ORIGINAL COPY", S_CENTER))
    story.append(Spacer(1, 2 * mm))

    date_no = (f"Date : <b>{data.get('date','')}</b><br/>"
               f"{no_label} : <b>{data.get('no','')}</b>")
    hdr = Table([[
        Paragraph("Customer Name and Address", S_SMALL_B),
        Paragraph(date_no, S_RIGHT),
    ]], colWidths=[110 * mm, 70 * mm])
    hdr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(hdr)
    story.append(Spacer(1, 1 * mm))

    story.append(Paragraph(f"<b>{data.get('pname','')}</b>", S_BOLD))
    if data.get("padd"):
        story.append(Paragraph(data["padd"], S_SMALL))
    if data.get("gstno"):
        story.append(Paragraph(f"GST No. : {data['gstno']}", S_SMALL))
    if data.get("sdpdc"):
        story.append(Paragraph(f"ASP D.C. No. {data['sdpdc']}", S_SMALL))
    if data.get("ref"):
        story.append(Paragraph(f"Ref.:&nbsp;&nbsp; {data['ref']}", S_SMALL))
    if data.get("sub"):
        story.append(Paragraph(f"Sub.:&nbsp;&nbsp; {data['sub']}", S_SMALL))
    story.append(Spacer(1, 3 * mm))


def _line_items_table(rows: list[dict[str, Any]]) -> Table:
    header = [
        Paragraph("<b>SL\nNo.</b>", S_CENTER),
        Paragraph("<b>Item</b>", S_NORMAL),
        Paragraph("<b>OD</b>", S_CENTER),
        Paragraph("<b>Rate</b>", S_RIGHT),
        Paragraph("<b>Qty.</b>", S_CENTER),
        Paragraph("<b>Amt.</b>", S_RIGHT),
    ]
    col_w = [13 * mm, 80 * mm, 20 * mm, 24 * mm, 14 * mm, 24 * mm]
    data: list[list] = [header]
    for i, row in enumerate(rows):
        data.append([
            Paragraph(str(i + 1), S_CENTER),
            Paragraph(str(row.get("part", "")), S_NORMAL),
            Paragraph(str(row.get("od", "")) if row.get("od") else "", S_CENTER),
            Paragraph(fmt_amt(float(row.get("rate", 0))), S_RIGHT),
            Paragraph(str(row.get("qty", 1)), S_CENTER),
            Paragraph(fmt_amt(float(row.get("AMT", 0))), S_RIGHT),
        ])
    while len(data) < 5:
        data.append([Paragraph("", S_NORMAL)] * 6)

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.Color(0.97, 0.97, 1.0)]),
    ]))
    return t


def _totals_block(story: list, data: dict[str, Any]) -> None:
    tamt  = float(data.get("tamt",  0.0))
    cgst  = float(data.get("cgst",  0.0))
    sgst  = float(data.get("sgst",  0.0))
    igst  = float(data.get("igst",  0.0))
    total = float(data.get("total", 0.0))

    gst_rows = [
        [Paragraph("Taxable Amount :", S_SMALL),
         Paragraph(fmt_amt(tamt), S_RIGHT)],
        [Paragraph("IGST @ 18% :", S_SMALL),
         Paragraph(fmt_amt(igst) if igst else "", S_RIGHT)],
        [Paragraph("CGST @ 9% :", S_SMALL),
         Paragraph(fmt_amt(cgst) if cgst else "", S_RIGHT)],
        [Paragraph("SGST @ 9% :", S_SMALL),
         Paragraph(fmt_amt(sgst) if sgst else "", S_RIGHT)],
        [Paragraph("<b>Grand Total</b>", S_SMALL_B),
         Paragraph(f"<b>{fmt_amt(total)}</b>", S_RIGHT_B)],
    ]
    right_t = Table(gst_rows, colWidths=[44 * mm, 30 * mm])
    right_t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LINEABOVE",     (0, -1), (-1, -1), 0.5, colors.black),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.5, colors.black),
    ]))

    left_items = [
        [Paragraph("Labour Charges", S_NORMAL)],
        [Spacer(1, 2 * mm)],
        [Paragraph(f"HSN / SAC Code : {COMPANY['hsn']}", S_SMALL)],
        [Spacer(1, 3 * mm)],
        [Paragraph(amount_words(total), S_SMALL)],
    ]
    left_t = Table(left_items, colWidths=[96 * mm])
    left_t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    combined = Table([[left_t, right_t]], colWidths=[96 * mm, 84 * mm])
    combined.setStyle(TableStyle([
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0),  0.5, colors.black),
    ]))
    story.append(combined)
    story.append(Spacer(1, 6 * mm))


def _signature_block(story: list) -> None:
    story.append(Table(
        [["", Paragraph(f"For {COMPANY['name']}", S_RIGHT)]],
        colWidths=[90 * mm, 90 * mm],
    ))
    story.append(Spacer(1, 12 * mm))
    story.append(Table(
        [["", Paragraph(f"<b>{COMPANY['sign']}</b>", S_RIGHT_B)]],
        colWidths=[90 * mm, 90 * mm],
    ))


def _build_story(data: dict[str, Any], doc_type: str, no_label: str) -> list:
    story: list = []
    _company_header(story)
    _party_block(story, data, doc_type, no_label)
    story.append(_line_items_table(data.get("rows", [])))
    story.append(Spacer(1, 3 * mm))
    _totals_block(story, data)
    _signature_block(story)
    return story


def _render(story: list, filepath: str) -> str:
    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=10 * mm,  bottomMargin=10 * mm,
    )
    doc.build(story)
    return filepath


def print_proforma(data: dict[str, Any], reports_dir: Path,
                   open_pdf: bool = True) -> str:
    path = str(reports_dir / f"ProformaInvoice_{data['no']}.pdf")
    _render(_build_story(data, "PROFORMA INVOICE", "I No."), path)
    if open_pdf:
        _open_pdf(path)
    return path


def print_quotation(data: dict[str, Any], reports_dir: Path,
                    open_pdf: bool = True) -> str:
    path = str(reports_dir / f"Quotation_{data['no']}.pdf")
    _render(_build_story(data, "QUOTATION", "Quot. No."), path)
    if open_pdf:
        _open_pdf(path)
    return path


def print_job_work_bill(data: dict[str, Any], reports_dir: Path,
                        open_pdf: bool = True) -> str:
    path = str(reports_dir / f"JobWorkBill_{data['no']}.pdf")
    _render(_build_story(data, "JOB WORK BILL", "JWB No."), path)
    if open_pdf:
        _open_pdf(path)
    return path


def print_dc(data: dict[str, Any], reports_dir: Path,
             open_pdf: bool = True) -> str:
    path = str(reports_dir / f"DC_{data['no']}.pdf")
    _render(_build_story(data, "DELIVERY CHALLAN", "DC No."), path)
    if open_pdf:
        _open_pdf(path)
    return path


def print_purchase_order(data: dict[str, Any], reports_dir: Path,
                         open_pdf: bool = True) -> str:
    path = str(reports_dir / f"PO_{data['no']}.pdf")
    _render(_build_story(data, "PURCHASE ORDER", "PO No."), path)
    if open_pdf:
        _open_pdf(path)
    return path
