"""
asp_print.py — PDF generation for all document types.
Legacy industrial print geometry tuned for dense A4 utilization.
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

from asp_utils import amount_words, fmt_amt, normalize_gstno

PAGE_MARGIN = 3 * mm
CONTENT_W = A4[0] - (2 * PAGE_MARGIN)
THIN = 0.8
BOX = 1.05

S_DEITY   = ParagraphStyle("deity",   fontName="Times-Italic",  fontSize=12, alignment=TA_CENTER, leading=14)
S_CO_NAME = ParagraphStyle("coname",  fontName="Times-Bold",    fontSize=42, alignment=TA_CENTER, leading=46)
S_CO_ADDR = ParagraphStyle("coaddr",  fontName="Times-Roman",   fontSize=11.5, alignment=TA_CENTER, leading=14)
S_SECTION = ParagraphStyle("section", fontName="Times-Bold",    fontSize=26, alignment=TA_CENTER, leading=30)
S_NORMAL  = ParagraphStyle("normal",  fontName="Times-Roman",   fontSize=15.5, leading=19)
S_SMALL   = ParagraphStyle("small",   fontName="Times-Roman",   fontSize=14, leading=17)
S_BOLD    = ParagraphStyle("bold",    fontName="Times-Bold",    fontSize=16, leading=19.5)
S_RIGHT   = ParagraphStyle("right",   fontName="Times-Roman",   fontSize=15.5, alignment=TA_RIGHT, leading=19)
S_RIGHT_B = ParagraphStyle("rightb",  fontName="Times-Bold",    fontSize=15.5, alignment=TA_RIGHT, leading=19)
S_CENTER  = ParagraphStyle("center",  fontName="Times-Roman",   fontSize=15.5, alignment=TA_CENTER, leading=19)
S_SMALL_B = ParagraphStyle("smallb",  fontName="Times-Bold",    fontSize=15, leading=18)

# Proforma-specific styles (slightly larger than regular bill)
S_PF_NORMAL = ParagraphStyle("pf_normal", fontName="Times-Roman", fontSize=16.5, leading=20)
S_PF_BOLD   = ParagraphStyle("pf_bold",   fontName="Times-Bold",  fontSize=17, leading=20.5)
S_PF_RIGHT  = ParagraphStyle("pf_right",  fontName="Times-Roman", fontSize=16.5, alignment=TA_RIGHT, leading=20)
S_PF_RIGHT_B= ParagraphStyle("pf_rightb", fontName="Times-Bold",  fontSize=16.5, alignment=TA_RIGHT, leading=20)
S_PF_CENTER = ParagraphStyle("pf_center", fontName="Times-Roman", fontSize=16.5, alignment=TA_CENTER, leading=20)
S_PF_SMALL  = ParagraphStyle("pf_small",  fontName="Times-Roman", fontSize=15.5, leading=19)
S_PF_SMALL_B= ParagraphStyle("pf_smallb", fontName="Times-Bold",  fontSize=15.5, leading=19)
S_PF_SECTION= ParagraphStyle("pf_sect",   fontName="Times-Bold",  fontSize=28, alignment=TA_CENTER, leading=32)
S_DC_REF    = ParagraphStyle("dc_ref",    fontName="Times-Bold",  fontSize=15, leading=18)
S_TOT_LBL   = ParagraphStyle("totlbl",    fontName="Times-Roman", fontSize=15, leading=18)
S_TOT_VAL   = ParagraphStyle("totval",    fontName="Times-Roman", fontSize=15, alignment=TA_RIGHT, leading=18)
S_TOT_B_LBL = ParagraphStyle("totblbl",   fontName="Times-Bold",  fontSize=16, leading=19)
S_TOT_B_VAL = ParagraphStyle("totbval",   fontName="Times-Bold",  fontSize=16, alignment=TA_RIGHT, leading=19)

COMPANY: dict[str, str] = {
    "name":  "Adhwaitha Sri Plating",
    "deity": "Thiruvattai Iyanar Thunai",
    "addr1": "Fac.: SF.No.233, Plot No.: C 26 , Electro Plating Industrial Park,",
    "addr2": "D.Karisalkulam, Manamadurai Taluk ,Sivagangai District.",
    "addr3": "Tamilnadu, 630411. Mobile No. 63693 73649, 99944 43530",
    "addr4": "Off.: Old No.86 J/2, New No.76, Arunaohalam Street, S.S.Colony North Gate,Madurai-18.",
    "gstno": "33ADZPA3791Q2ZP",
    "state": "33",
    "hsn":   "75089010",
    "sign":  "A. Dhanalakshmi",  # legacy — no longer printed
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
    from reportlab.platypus import Image
    logo_path = Path(__file__).parent / "ref" / "old_ui" / "asp_logo.jpg"
    
    if logo_path.exists():
        # Enlarge logo: 56mm width (2.15x original size)
        logo_w = 56 * mm
        logo_h = logo_w / 1.24675
        logo_img = Image(str(logo_path), width=logo_w, height=logo_h)
        
        # Company name and deity title flowables
        mid_flowables = [
            Paragraph(COMPANY["deity"], S_DEITY),
            Spacer(1, 0.4 * mm),
            Paragraph(f"<b>{COMPANY['name']}</b>", S_CO_NAME)
        ]
        
        # Address block flowables
        addr_flowables = []
        for k in ("addr1", "addr2", "addr3", "addr4"):
            addr_flowables.append(Paragraph(COMPANY[k], S_CO_ADDR))
            
        # Combine Deity, Company name, and Addresses in the right column
        details_flowables = mid_flowables + [Spacer(1, 0.7 * mm)] + addr_flowables
        
        # 2-column table: Left holds logo, Right holds details
        col_w = [56 * mm, CONTENT_W - 56 * mm]
        header_table = Table([
            [logo_img, details_flowables]
        ], colWidths=col_w)
        
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
    else:
        # Fallback to legacy text-only layout if logo image is missing
        story.append(Paragraph(COMPANY["deity"], S_DEITY))
        story.append(Spacer(1, 0.4 * mm))
        story.append(Paragraph(f"<b>{COMPANY['name']}</b>", S_CO_NAME))
        story.append(Spacer(1, 0.7 * mm))
        for k in ("addr1", "addr2", "addr3", "addr4"):
            story.append(Paragraph(COMPANY[k], S_CO_ADDR))

    story.append(Spacer(1, 1.4 * mm))

    t = Table([[
        Paragraph(f"State Code : {COMPANY['state']}", S_SMALL),
        Paragraph(f"GST No. : {COMPANY['gstno']}", S_RIGHT),
    ]], colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    t.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), BOX, colors.black),
        ("LINEBELOW",     (0, 0), (-1, 0), BOX, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 1.4 * mm))


def _party_block(story: list, data: dict[str, Any],
                 doc_type: str, no_label: str) -> None:
    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph(f"<b>{doc_type}</b>", S_SECTION))
    story.append(Spacer(1, 1.2 * mm))
    if doc_type == "JOB WORK BILL":
        story.append(Paragraph("ORIGINAL COPY", S_CENTER))
        story.append(Spacer(1, 1.2 * mm))

    cust_details = [
        Paragraph("To", S_SMALL_B),
        Spacer(1, 0.8 * mm),
        Paragraph(f"<b>{data.get('pname','')}</b>", S_BOLD),
    ]
    if data.get("padd"):
        cust_details.append(Paragraph(data["padd"], S_NORMAL))
    if data.get("gstno"):
        cust_details.append(Paragraph(f"GST No. : <b>{data['gstno']}</b>", S_NORMAL))
    if data.get("sdpdc"):
        cust_details.append(Paragraph(f"ASP D.C. No. : {data['sdpdc']}", S_DC_REF))

    meta_rows = [
        [Paragraph(f"{no_label}", S_BOLD), Paragraph(f": <b>{data.get('no','')}</b>", S_BOLD)],
        [Paragraph("Date", S_BOLD), Paragraph(f": <b>{data.get('date','')}</b>", S_BOLD)],
    ]
    meta_table = Table(meta_rows, colWidths=[35 * mm, 45 * mm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    party_table = Table([[cust_details, meta_table]], colWidths=[CONTENT_W * 0.63, CONTENT_W * 0.37])
    party_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, -1), BOX, colors.black),
        ("LINEBELOW", (0, 0), (-1, -1), BOX, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(party_table)

    # Ref and Sub — centered with well spacing, below the party block
    _ref_sub_block(story, data)
    story.append(Spacer(1, 1.4 * mm))


def _ref_sub_block(story: list, data: dict[str, Any],
                   style: ParagraphStyle = S_DC_REF) -> None:
    """Centered Ref / Sub lines below the party block — shared across all forms."""
    ref_sub_items: list = []
    if data.get("ref"):
        ref_sub_items.append(
            Paragraph(f"Ref.:    {data['ref']}", style))
    if data.get("sub"):
        ref_sub_items.append(
            Paragraph(f"Sub.:    {data['sub']}", style))
    if ref_sub_items:
        story.append(Spacer(1, 1.5 * mm))
        ref_table = Table(
            [[item] for item in ref_sub_items],
            colWidths=[CONTENT_W],
        )
        ref_table.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 1.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 20),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
        ]))
        story.append(ref_table)


def _line_items_table(rows: list[dict[str, Any]]) -> Table:
    header = [
        Paragraph("<b>SL\nNo.</b>", S_CENTER),
        Paragraph("<b>Item</b>", S_NORMAL),
        Paragraph("<b>OD</b>", S_CENTER),
        Paragraph("<b>Rate</b>", S_RIGHT),
        Paragraph("<b>Qty.</b>", S_CENTER),
        Paragraph("<b>Amt.</b>", S_RIGHT),
    ]
    col_w = [14 * mm, 96 * mm, 21 * mm, 23 * mm, 16 * mm, 34 * mm]
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
    min_rows = max(len(data), min(len(data) + 2, 8))
    while len(data) < min_rows:
        data.append([Paragraph("", S_NORMAL)] * 6)

    row_heights = [12.5 * mm] + [13.5 * mm] * (len(data) - 1)
    t = Table(data, colWidths=col_w, rowHeights=row_heights, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 15.5),
        # Outer border: top of first row, bottom of last row only
        ("LINEABOVE",     (0, 0), (-1, 0), BOX, colors.black),
        ("LINEBELOW",     (0, 0), (-1, 0), THIN, colors.black),    # header underline
        ("LINEBELOW",     (0, -1), (-1, -1), BOX, colors.black),   # bottom border
        # Vertical column separators (no horizontal row lines)
        ("LINEBEFORE",    (0, 0), (0, -1), BOX, colors.black),     # left edge
        ("LINEBEFORE",    (1, 0), (-1, -1), THIN, colors.black),   # between columns
        ("LINEAFTER",     (-1, 0), (-1, -1), BOX, colors.black),   # right edge
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.2),
    ]))
    return t


def _line_items_table_dc(rows: list[dict[str, Any]]) -> Table:
    """DC layout: no amount column — items, mould value, and quantities."""
    header = [
        Paragraph("<b>SL No</b>", S_CENTER),
        Paragraph("<b>Item</b>", S_NORMAL),
        Paragraph("<b>Mould<br/>Value</b>", S_CENTER),
        Paragraph("<b>Qty.</b>", S_CENTER),
    ]
    col_w = [18 * mm, 126 * mm, 30 * mm, 30 * mm]
    data: list[list] = [header]
    for i, row in enumerate(rows):
        mv = row.get("mould_value", row.get("MOULD_VALUE", 0))
        mv_str = fmt_amt(float(mv)) if mv else ""
        data.append([
            Paragraph(str(i + 1), S_CENTER),
            Paragraph(str(row.get("part", "")), S_NORMAL),
            Paragraph(mv_str, S_CENTER),
            Paragraph(str(row.get("qty", 1)), S_CENTER),
        ])
    min_rows = max(len(data), min(len(data) + 2, 10))
    while len(data) < min_rows:
        data.append([Paragraph("", S_NORMAL)] * 4)

    row_heights = [12.5 * mm] + [11.5 * mm] * (len(data) - 1)
    t = Table(data, colWidths=col_w, rowHeights=row_heights, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 15.5),
        # Outer border: top of first row, bottom of last row only
        ("LINEABOVE",     (0, 0), (-1, 0), BOX, colors.black),
        ("LINEBELOW",     (0, 0), (-1, 0), THIN, colors.black),    # header underline
        ("LINEBELOW",     (0, -1), (-1, -1), BOX, colors.black),   # bottom border
        # Vertical column separators (no horizontal row lines)
        ("LINEBEFORE",    (0, 0), (0, -1), BOX, colors.black),     # left edge
        ("LINEBEFORE",    (1, 0), (-1, -1), THIN, colors.black),   # between columns
        ("LINEAFTER",     (-1, 0), (-1, -1), BOX, colors.black),   # right edge
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.1),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.2),
    ]))
    return t


def _line_items_table_proforma(rows: list[dict[str, Any]]) -> Table:
    header = [
        Paragraph("<b>SL\nNo.</b>", S_PF_CENTER),
        Paragraph("<b>Item</b>", S_PF_BOLD),
        Paragraph("<b>OD</b>", S_PF_CENTER),
        Paragraph("<b>Rate</b>", S_PF_RIGHT),
        Paragraph("<b>Qty.</b>", S_PF_CENTER),
        Paragraph("<b>Amt.</b>", S_PF_RIGHT),
    ]
    col_w = [14 * mm, 96 * mm, 21 * mm, 23 * mm, 16 * mm, 34 * mm]
    data: list[list] = [header]
    for i, row in enumerate(rows):
        data.append([
            Paragraph(str(i + 1), S_PF_CENTER),
            Paragraph(str(row.get("part", "")), S_PF_NORMAL),
            Paragraph(str(row.get("od", "")) if row.get("od") else "", S_PF_CENTER),
            Paragraph(fmt_amt(float(row.get("rate", 0))), S_PF_RIGHT),
            Paragraph(str(row.get("qty", 1)), S_PF_CENTER),
            Paragraph(fmt_amt(float(row.get("AMT", 0))), S_PF_RIGHT),
        ])
    min_rows = max(len(data), min(len(data) + 2, 8))
    while len(data) < min_rows:
        data.append([Paragraph("", S_PF_NORMAL)] * 6)

    row_heights = [12.5 * mm] + [13.5 * mm] * (len(data) - 1)
    t = Table(data, colWidths=col_w, rowHeights=row_heights, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 16.5),
        # Outer border: top of first row, bottom of last row only
        ("LINEABOVE",     (0, 0), (-1, 0), BOX, colors.black),
        ("LINEBELOW",     (0, 0), (-1, 0), THIN, colors.black),    # header underline
        ("LINEBELOW",     (0, -1), (-1, -1), BOX, colors.black),   # bottom border
        # Vertical column separators (no horizontal row lines)
        ("LINEBEFORE",    (0, 0), (0, -1), BOX, colors.black),     # left edge
        ("LINEBEFORE",    (1, 0), (-1, -1), THIN, colors.black),   # between columns
        ("LINEAFTER",     (-1, 0), (-1, -1), BOX, colors.black),   # right edge
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.2),
    ]))
    return t


def _totals_block(story: list, data: dict[str, Any],
                  left_style: ParagraphStyle = S_NORMAL,
                  small_style: ParagraphStyle = S_SMALL,
                  right_style: ParagraphStyle = S_RIGHT,
                  right_bold: ParagraphStyle = S_RIGHT_B,
                  small_bold: ParagraphStyle = S_SMALL_B) -> None:
    tamt  = float(data.get("tamt",  0.0))
    cgst  = float(data.get("cgst",  0.0))
    sgst  = float(data.get("sgst",  0.0))
    igst  = float(data.get("igst",  0.0))
    total = float(data.get("total", 0.0))

    label_style = S_TOT_LBL if small_style is S_SMALL else small_style
    value_style = S_TOT_VAL if right_style is S_RIGHT else right_style
    bold_label_style = S_TOT_B_LBL if small_bold is S_SMALL_B else small_bold
    bold_value_style = S_TOT_B_VAL if right_bold is S_RIGHT_B else right_bold

    gstno = normalize_gstno(data.get("gstno", ""))
    state_code = gstno[:2]
    intrastate = (state_code == "33") or (not gstno)

    gst_rows = [
        [Paragraph("Taxable Amount :", label_style),
         Paragraph(fmt_amt(tamt), value_style)],
        [Paragraph("IGST @ 18% :", label_style),
         Paragraph(fmt_amt(igst) if igst else "", value_style)],
        [Paragraph("CGST @ 9% :", label_style),
         Paragraph(fmt_amt(cgst) if cgst else "", value_style)],
        [Paragraph("SGST @ 9% :", label_style),
         Paragraph(fmt_amt(sgst) if sgst else "", value_style)],
    ]

    gst_rows.append([Paragraph("<b>Grand Total</b>", bold_label_style),
                     Paragraph(f"<b>{fmt_amt(total)}</b>", bold_value_style)])
    right_t = Table(gst_rows, colWidths=[58 * mm, 34 * mm])
    right_t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 15),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
        ("TOPPADDING",    (0, -1), (-1, -1), 2.1),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 2.1),
        ("LINEABOVE",     (0, -1), (-1, -1), BOX, colors.black),
        ("LINEBELOW",     (0, -1), (-1, -1), BOX, colors.black),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))

    left_items = [
        [Paragraph("Labour Charges", left_style)],
        [Paragraph(f"HSN / SAC Code : {COMPANY['hsn']}", small_style)],
        [Spacer(1, 1 * mm)],
        [Paragraph(amount_words(total), small_style)],
    ]
    left_t = Table(left_items, colWidths=[CONTENT_W - 94 * mm])
    left_t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 1.6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1.6),
    ]))

    combined = Table([[left_t, right_t]], colWidths=[CONTENT_W - 94 * mm, 94 * mm])
    combined.setStyle(TableStyle([
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), BOX, colors.black),
    ]))
    story.append(combined)
    story.append(Spacer(1, 1.4 * mm))


def _signature_block(story: list) -> None:
    """Dark thick line, 'For Adhwaitha Sri Plating' right-aligned, signature space."""
    # Dark thick horizontal rule
    sig_line = Table(
        [[""]],
        colWidths=[CONTENT_W],
    )
    sig_line.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 2.0, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(sig_line)
    story.append(Spacer(1, 2 * mm))
    # "For Adhwaitha Sri Plating" right-aligned
    story.append(Table(
        [["", Paragraph(f"For {COMPANY['name']}", S_RIGHT_B)]],
        colWidths=[CONTENT_W - 94 * mm, 94 * mm],
    ))
    # Signature space
    story.append(Spacer(1, 14 * mm))


def _build_story(data: dict[str, Any], doc_type: str, no_label: str) -> list:
    story: list = []
    _company_header(story)
    _party_block(story, data, doc_type, no_label)
    story.append(_line_items_table(data.get("rows", [])))
    story.append(Spacer(1, 0.8 * mm))
    _totals_block(story, data)
    _signature_block(story)
    return story


def _build_story_dc(data: dict[str, Any], copy_label: str = "ORIGINAL") -> list:
    """DC story: no amount column, no goods value, no totals block."""
    story: list = []
    _company_header(story)

    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph("<b>DELIVERY CHALLAN</b>", S_SECTION))
    story.append(Spacer(1, 1.2 * mm))
    # Copy label: ORIGINAL COPY / DUPLICATE COPY / TRIPLICATE COPY
    S_COPY_LABEL = ParagraphStyle(
        "copylabel", fontName="Times-Bold", fontSize=18,
        alignment=TA_CENTER, leading=22,
    )
    story.append(Paragraph(f"<b>{copy_label} COPY</b>", S_COPY_LABEL))
    story.append(Spacer(1, 1.2 * mm))

    cust_details = [
        Paragraph("To", S_SMALL_B),
        Spacer(1, 0.8 * mm),
        Paragraph(f"<b>{data.get('pname','')}</b>", S_BOLD),
    ]
    if data.get("padd"):
        cust_details.append(Paragraph(data["padd"], S_NORMAL))
    if data.get("gstno"):
        cust_details.append(Paragraph(f"GST No. : <b>{data['gstno']}</b>", S_NORMAL))

    meta_rows = [
        [Paragraph("DC Date", S_BOLD), Paragraph(f":  <b>{data.get('date','')}</b>", S_BOLD)],
        [Paragraph("DC No.", S_BOLD), Paragraph(f":  <b>{data.get('no','')}</b>", S_BOLD)],
    ]
    meta_table = Table(meta_rows, colWidths=[28 * mm, 52 * mm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    party_table = Table([[cust_details, meta_table]], colWidths=[CONTENT_W * 0.63, CONTENT_W * 0.37])
    party_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, -1), BOX, colors.black),
        ("LINEBELOW", (0, 0), (-1, -1), BOX, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(party_table)

    # Ref and Sub — centered with well spacing
    _ref_sub_block(story, data)
    story.append(Spacer(1, 1.4 * mm))

    story.append(_line_items_table_dc(data.get("rows", [])))
    story.append(Spacer(1, 1.2 * mm))
    story.append(Paragraph("Only Job Work Not For Sale", S_BOLD))
    story.append(Spacer(1, 1.6 * mm))
    _signature_block(story)
    return story


def _build_story_proforma(data: dict[str, Any]) -> list:
    story: list = []
    _company_header(story)

    story.append(Spacer(1, 1 * mm))
    story.append(Paragraph("<b>PROFORMA INVOICE</b>", S_PF_SECTION))
    story.append(Spacer(1, 1.2 * mm))

    cust_details = [
        Paragraph("To", S_PF_SMALL_B),
        Spacer(1, 0.8 * mm),
        Paragraph(f"<b>{data.get('pname','')}</b>", S_PF_BOLD),
    ]
    if data.get("padd"):
        cust_details.append(Paragraph(data["padd"], S_PF_NORMAL))
    if data.get("gstno"):
        cust_details.append(Paragraph(f"GST No. : <b>{data['gstno']}</b>", S_PF_NORMAL))

    meta_rows = [
        [Paragraph("Proforma No.", S_PF_BOLD), Paragraph(f": <b>{data.get('no','')}</b>", S_PF_BOLD)],
        [Paragraph("Date", S_PF_BOLD), Paragraph(f": <b>{data.get('date','')}</b>", S_PF_BOLD)],
    ]
    meta_table = Table(meta_rows, colWidths=[38 * mm, 45 * mm])
    meta_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    party_table = Table([[cust_details, meta_table]], colWidths=[CONTENT_W * 0.63, CONTENT_W * 0.37])
    party_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, -1), BOX, colors.black),
        ("LINEBELOW", (0, 0), (-1, -1), BOX, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(party_table)

    # Ref and Sub — centered with well spacing
    _ref_sub_block(story, data, S_DC_REF)
    story.append(Spacer(1, 1.4 * mm))

    story.append(_line_items_table_proforma(data.get("rows", [])))
    story.append(Spacer(1, 0.8 * mm))

    _totals_block(
        story,
        data,
        left_style=S_PF_NORMAL,
        small_style=S_PF_SMALL,
        right_style=S_PF_RIGHT,
        right_bold=S_PF_RIGHT_B,
        small_bold=S_PF_SMALL_B,
    )
    _signature_block(story)
    return story


def _render(story: list, filepath: str) -> str:
    def _draw_page_border(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setLineWidth(BOX)
        canvas.rect(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,  bottomMargin=PAGE_MARGIN,
    )
    doc.build(story, onFirstPage=_draw_page_border, onLaterPages=_draw_page_border)
    return filepath


def print_proforma(data: dict[str, Any], reports_dir: Path,
                   open_pdf: bool = True) -> str:
    path = str(reports_dir / f"ProformaInvoice_{data['no']}.pdf")
    _render(_build_story_proforma(data), path)
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
    """Generate TRIPLICATE + DUPLICATE + ORIGINAL DC PDFs.
    Opens in reverse order so ORIGINAL appears on top for the operator."""
    paths: list[str] = []
    for label in ("TRIPLICATE", "DUPLICATE", "ORIGINAL"):
        fname = f"DC_{data['no']}_{label}.pdf"
        path = str(reports_dir / fname)
        _render(_build_story_dc(data, copy_label=label), path)
        paths.append(path)
    if open_pdf:
        import time
        for p in paths:
            _open_pdf(p)
            time.sleep(0.3)
    return paths[-1]  # Return ORIGINAL path


def print_purchase_order(data: dict[str, Any], reports_dir: Path,
                         open_pdf: bool = True) -> str:
    path = str(reports_dir / f"PO_{data['no']}.pdf")
    _render(_build_story(data, "PURCHASE ORDER", "PO No."), path)
    if open_pdf:
        _open_pdf(path)
    return path
