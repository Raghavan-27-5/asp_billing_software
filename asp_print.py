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

from asp_utils import amount_words, fmt_amt

PAGE_MARGIN = 3 * mm
CONTENT_W = A4[0] - (2 * PAGE_MARGIN)
THIN = 0.8
BOX = 1.05

S_DEITY   = ParagraphStyle("deity",   fontName="Times-Italic",  fontSize=9, alignment=TA_CENTER, leading=11)
S_CO_NAME = ParagraphStyle("coname",  fontName="Times-Bold",    fontSize=38, alignment=TA_CENTER, leading=41)
S_CO_ADDR = ParagraphStyle("coaddr",  fontName="Times-Roman",   fontSize=12, alignment=TA_CENTER, leading=14.5)
S_SECTION = ParagraphStyle("section", fontName="Times-Bold",    fontSize=15, alignment=TA_CENTER, leading=17)
S_NORMAL  = ParagraphStyle("normal",  fontName="Times-Roman",   fontSize=11, leading=13)
S_SMALL   = ParagraphStyle("small",   fontName="Times-Roman",   fontSize=10.25, leading=12.25)
S_BOLD    = ParagraphStyle("bold",    fontName="Times-Bold",    fontSize=12, leading=13.5)
S_RIGHT   = ParagraphStyle("right",   fontName="Times-Roman",   fontSize=11, alignment=TA_RIGHT, leading=13)
S_RIGHT_B = ParagraphStyle("rightb",  fontName="Times-Bold",    fontSize=11, alignment=TA_RIGHT, leading=13)
S_CENTER  = ParagraphStyle("center",  fontName="Times-Roman",   fontSize=11, alignment=TA_CENTER, leading=13)
S_SMALL_B = ParagraphStyle("smallb",  fontName="Times-Bold",    fontSize=10.5, leading=12.25)

# Proforma-specific styles (slightly larger than regular bill)
S_PF_NORMAL = ParagraphStyle("pf_normal", fontName="Times-Roman", fontSize=12, leading=13.8)
S_PF_BOLD   = ParagraphStyle("pf_bold",   fontName="Times-Bold",  fontSize=12, leading=13.8)
S_PF_RIGHT  = ParagraphStyle("pf_right",  fontName="Times-Roman", fontSize=12, alignment=TA_RIGHT, leading=13.8)
S_PF_RIGHT_B= ParagraphStyle("pf_rightb", fontName="Times-Bold",  fontSize=12, alignment=TA_RIGHT, leading=13.8)
S_PF_CENTER = ParagraphStyle("pf_center", fontName="Times-Roman", fontSize=12, alignment=TA_CENTER, leading=13.8)
S_PF_SMALL  = ParagraphStyle("pf_small",  fontName="Times-Roman", fontSize=11, leading=12.8)
S_PF_SMALL_B= ParagraphStyle("pf_smallb", fontName="Times-Bold",  fontSize=11, leading=12.8)
S_PF_SECTION= ParagraphStyle("pf_sect",   fontName="Times-Bold",  fontSize=17, alignment=TA_CENTER, leading=19)
S_DC_REF    = ParagraphStyle("dc_ref",    fontName="Times-Bold",  fontSize=11, leading=13)
S_TOT_LBL   = ParagraphStyle("totlbl",    fontName="Times-Roman", fontSize=10.5, leading=12)
S_TOT_VAL   = ParagraphStyle("totval",    fontName="Times-Roman", fontSize=10.5, alignment=TA_RIGHT, leading=12)
S_TOT_B_LBL = ParagraphStyle("totblbl",   fontName="Times-Bold",  fontSize=11, leading=12.5)
S_TOT_B_VAL = ParagraphStyle("totbval",   fontName="Times-Bold",  fontSize=11, alignment=TA_RIGHT, leading=12.5)

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
    section = Table([[
        Paragraph(f"<b>{doc_type}</b>", S_SECTION),
        Paragraph("ORIGINAL COPY" if doc_type == "JOB WORK BILL" else "", S_CENTER),
    ]], colWidths=[CONTENT_W * 0.69, CONTENT_W * 0.31])
    section.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), BOX, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(section)
    story.append(Spacer(1, 1.2 * mm))

    date_no = (f"Date : <b>{data.get('date','')}</b><br/>"
               f"{no_label} : <b>{data.get('no','')}</b>")
    hdr = Table([[
        Paragraph("Customer Name and Address", S_SMALL_B),
        Paragraph(date_no, S_RIGHT),
    ]], colWidths=[CONTENT_W * 0.65, CONTENT_W * 0.35])
    hdr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.8 * mm))

    story.append(Paragraph(f"<b>{data.get('pname','')}</b>", S_BOLD))
    if data.get("padd"):
        story.append(Paragraph(data["padd"], S_SMALL))
    if data.get("gstno"):
        story.append(Paragraph(f"GST No. : {data['gstno']}", S_SMALL))
    if data.get("sdpdc"):
        story.append(Paragraph(f"ASP D.C. No. : {data['sdpdc']}", S_DC_REF))
    if data.get("ref"):
        story.append(Paragraph(f"Ref.:&nbsp;&nbsp; {data['ref']}", S_SMALL))
    if data.get("sub"):
        story.append(Paragraph(f"Sub.:&nbsp;&nbsp; {data['sub']}", S_SMALL))
    story.append(Spacer(1, 1.4 * mm))


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
    while len(data) < 12:
        data.append([Paragraph("", S_NORMAL)] * 6)

    row_heights = [10.5 * mm] + [11.4 * mm] * (len(data) - 1)
    t = Table(data, colWidths=col_w, rowHeights=row_heights, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 10.8),
        ("BOX",           (0, 0), (-1, -1), BOX, colors.black),
        ("GRID",          (0, 0), (-1, -1), THIN, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2.2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2.2),
    ]))
    return t


def _line_items_table_dc(rows: list[dict[str, Any]]) -> Table:
    """DC layout: no amount column — quantities and items only."""
    header = [
        Paragraph("<b>SL No</b>", S_CENTER),
        Paragraph("<b>Item</b>", S_NORMAL),
        Paragraph("<b>Qty.</b>", S_CENTER),
    ]
    col_w = [20 * mm, 146 * mm, 38 * mm]
    data: list[list] = [header]
    for i, row in enumerate(rows):
        data.append([
            Paragraph(str(i + 1), S_CENTER),
            Paragraph(str(row.get("part", "")), S_NORMAL),
            Paragraph(str(row.get("qty", 1)), S_CENTER),
        ])
    while len(data) < 15:
        data.append([Paragraph("", S_NORMAL)] * 3)

    row_heights = [10.5 * mm] + [9.6 * mm] * (len(data) - 1)
    t = Table(data, colWidths=col_w, rowHeights=row_heights, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 10.8),
        ("BOX",           (0, 0), (-1, -1), BOX, colors.black),
        ("GRID",          (0, 0), (-1, -1), THIN, colors.black),
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
    while len(data) < 12:
        data.append([Paragraph("", S_PF_NORMAL)] * 6)

    row_heights = [10.5 * mm] + [11.4 * mm] * (len(data) - 1)
    t = Table(data, colWidths=col_w, rowHeights=row_heights, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 11.2),
        ("BOX",           (0, 0), (-1, -1), BOX, colors.black),
        ("GRID",          (0, 0), (-1, -1), THIN, colors.black),
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

    gst_rows = [
        [Paragraph("Taxable Amount :", label_style),
         Paragraph(fmt_amt(tamt), value_style)],
        [Paragraph("IGST @ 18% :", label_style),
         Paragraph(fmt_amt(igst) if igst else "", value_style)],
        [Paragraph("CGST @ 9% :", label_style),
         Paragraph(fmt_amt(cgst) if cgst else "", value_style)],
        [Paragraph("SGST @ 9% :", label_style),
         Paragraph(fmt_amt(sgst) if sgst else "", value_style)],
        [Paragraph("<b>Grand Total</b>", bold_label_style),
         Paragraph(f"<b>{fmt_amt(total)}</b>", bold_value_style)],
    ]
    right_t = Table(gst_rows, colWidths=[58 * mm, 30 * mm])
    right_t.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 10.5),
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
    left_t = Table(left_items, colWidths=[112 * mm])
    left_t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 1.6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 1.6),
    ]))

    combined = Table([[left_t, right_t]], colWidths=[112 * mm, 88 * mm])
    combined.setStyle(TableStyle([
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), BOX, colors.black),
    ]))
    story.append(combined)
    story.append(Spacer(1, 1.4 * mm))


def _signature_block(story: list) -> None:
    story.append(Table(
        [["", Paragraph(f"For {COMPANY['name']}", S_RIGHT)]],
        colWidths=[112 * mm, 88 * mm],
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(Table(
        [["", Paragraph(f"<b>{COMPANY['sign']}</b>", S_RIGHT_B)]],
        colWidths=[112 * mm, 88 * mm],
    ))


def _build_story(data: dict[str, Any], doc_type: str, no_label: str) -> list:
    story: list = []
    _company_header(story)
    _party_block(story, data, doc_type, no_label)
    story.append(_line_items_table(data.get("rows", [])))
    story.append(Spacer(1, 0.8 * mm))
    _totals_block(story, data)
    _signature_block(story)
    return story


def _build_story_dc(data: dict[str, Any]) -> list:
    """DC story: no amount column, goods_value in party block, no totals block."""
    story: list = []
    _company_header(story)

    section = Table([[
        Paragraph("<b>DELIVERY CHALLAN</b>", S_SECTION),
        Paragraph("ORIGINAL COPY", S_CENTER),
    ]], colWidths=[CONTENT_W * 0.69, CONTENT_W * 0.31])
    section.setStyle(TableStyle([
        ("LINEABOVE",     (0, 0), (-1, 0), BOX, colors.black),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(section)
    story.append(Spacer(1, 1.1 * mm))

    date_no = (f"DC Date : <b>{data.get('date','')}</b><br/>"
               f"DC No. : <b>{data.get('no','')}</b>")
    hdr = Table([[
        Paragraph("To", S_SMALL_B),
        Paragraph(date_no, S_RIGHT),
    ]], colWidths=[CONTENT_W * 0.65, CONTENT_W * 0.35])
    hdr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.8 * mm))

    story.append(Paragraph(f"<b>{data.get('pname','')}</b>", S_BOLD))
    if data.get("padd"):
        story.append(Paragraph(data["padd"], S_SMALL))
    if data.get("gstno"):
        story.append(Paragraph(f"GST No. : {data['gstno']}", S_SMALL))
    if data.get("ref"):
        story.append(Paragraph(f"Ref.:&nbsp;&nbsp; {data['ref']}", S_SMALL))
    if data.get("sub"):
        story.append(Paragraph(f"Sub.:&nbsp;&nbsp; {data['sub']}", S_SMALL))
    if data.get("goods_value"):
        story.append(Paragraph(f"Goods Value :&nbsp;&nbsp; {data['goods_value']}", S_SMALL))

    story.append(Spacer(1, 1.2 * mm))
    story.append(_line_items_table_dc(data.get("rows", [])))
    story.append(Spacer(1, 1.2 * mm))
    story.append(Paragraph("Only Job Work Not For Sale", S_BOLD))
    story.append(Spacer(1, 1.6 * mm))
    _signature_block(story)
    return story


def _build_story_proforma(data: dict[str, Any]) -> list:
    story: list = []
    _company_header(story)

    story.append(Paragraph("<b>PROFORMA INVOICE</b>", S_PF_SECTION))
    story.append(Spacer(1, 1 * mm))

    date_no = (f"Date : <b>{data.get('date','')}</b><br/>"
               f"I No. : <b>{data.get('no','')}</b>")
    hdr = Table([[
        Paragraph("To", S_PF_SMALL_B),
        Paragraph(date_no, S_PF_RIGHT),
    ]], colWidths=[CONTENT_W * 0.65, CONTENT_W * 0.35])
    hdr.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.8 * mm))

    story.append(Paragraph(f"<b>{data.get('pname','')}</b>", S_PF_BOLD))
    if data.get("padd"):
        story.append(Paragraph(data["padd"], S_PF_SMALL))
    if data.get("gstno"):
        story.append(Paragraph(f"GST No. : {data['gstno']}", S_PF_SMALL))
    if data.get("ref"):
        story.append(Paragraph(f"Ref.:&nbsp;&nbsp; {data['ref']}", S_PF_SMALL))
    if data.get("sub"):
        story.append(Paragraph(f"Sub.:&nbsp;&nbsp; {data['sub']}", S_PF_SMALL))

    story.append(Spacer(1, 1.2 * mm))
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
    path = str(reports_dir / f"DC_{data['no']}.pdf")
    _render(_build_story_dc(data), path)
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
