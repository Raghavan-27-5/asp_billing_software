"""
Adhwaitha Sri Plating — Billing System
Developer: Raghavan (Freelance)
UI: exact match to original VB6 screenshots.
Architecture: Quotation → ItemInward → DC → BILL state machine.
"""

from __future__ import annotations

import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Any, Callable, Optional

import asp_db as db
import asp_print as pr
from asp_utils import (
    calc_gst, fmt_amt, parse_date, to_float, today_str, fy_start,
)

# ── Exact colours from screenshots ────────────────────────────────────────────
BG_DARK   = "#000080"   # dark navy — window/form background
BG_HEADER = "#FFFFCC"   # cream/yellow — top header strip
BTN_CY    = "#00FFFF"   # cyan — main menu buttons
BTN_GR    = "#00CC00"   # green — Save/Print Proforma
BTN_WH    = "#FFFFFF"   # white — standard form buttons
BTN_CYAN2 = "#00CCCC"   # teal — Update
FG_DARK   = "#000080"   # dark blue text on cream
FG_YEL    = "#FFFF00"   # yellow — sub-header "Adhwaitha Sri Plating"
FG_WH     = "#FFFFFF"
ENTRY_BG  = "#FFFFCC"   # cream entry fields
GRID_BG   = "#FFFFCC"   # cream grid rows
GRID_HDR  = "#000080"   # dark blue grid header
FORM_BG   = "#000080"   # form background

FONT_TITLE = ("Arial", 20, "bold")
FONT_HDR   = ("Arial", 10, "bold")
FONT_LBL   = ("Arial", 9)
FONT_LBL_B = ("Arial", 9, "bold")
FONT_BTN   = ("Arial", 9, "bold")
FONT_ENTRY = ("Arial", 9)
FONT_GRID  = ("Arial", 8)
FONT_SMALL = ("Arial", 8)


# ── Widget helpers ─────────────────────────────────────────────────────────────

def lbl(parent: tk.Widget, text: str = "", **kw: Any) -> tk.Label:
    return tk.Label(parent, text=text,
                    bg=kw.pop("bg", FORM_BG),
                    fg=kw.pop("fg", FG_WH),
                    font=kw.pop("font", FONT_LBL), **kw)


def ent(parent: tk.Widget, var: Optional[tk.Variable] = None,
        width: int = 20, **kw: Any) -> tk.Entry:
    return tk.Entry(parent, textvariable=var, width=width,
                    bg=ENTRY_BG, fg="#000000",
                    font=FONT_ENTRY, relief="sunken", bd=1, **kw)


def mkbtn(parent: tk.Widget, text: str, cmd: Callable,
          bg: str = BTN_WH, width: int = 12) -> tk.Button:
    return tk.Button(parent, text=text, command=cmd,
                     bg=bg, fg="#000000", font=FONT_BTN,
                     relief="raised", bd=2, width=width,
                     activebackground="#AAFFAA", cursor="hand2")


def _modal_input(parent: tk.Widget, prompt: str) -> str:
    """Show a small modal dialog exactly like the original 'Enter the Quotation No.'"""
    result = simpledialog.askstring("InvSDP", prompt, parent=parent)
    return (result or "").strip()


# ─────────────────────────────────────────────────────────────────────────────
#  Splash / Password
# ─────────────────────────────────────────────────────────────────────────────

class SplashScreen(tk.Toplevel):
    _password: str = "1234"

    def __init__(self, master: tk.Tk, on_success: Callable) -> None:
        super().__init__(master)
        self.on_success = on_success
        self.title("Adhwaitha Sri Plating")
        self.configure(bg=BG_DARK)
        self.geometry("700x480+200+100")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        # Left panel
        left = tk.Frame(self, bg="#000055", width=220)
        left.place(x=0, y=0, width=220, height=480)
        tk.Label(left, text="ASP", bg="#000055", fg="#FFFF00",
                 font=("Arial", 40, "bold")).place(x=55, y=120)
        tk.Label(left, text="Billing\nSystem", bg="#000055", fg="#AADDFF",
                 font=("Arial", 14, "bold")).place(x=35, y=210)
        tk.Label(left, text="💼", bg="#000055", fg=FG_WH,
                 font=("Arial", 28)).place(x=80, y=285)
        tk.Label(left, text="Developed By", bg="#000055", fg=FG_WH,
                 font=("Arial", 9, "bold")).place(x=10, y=370)
        tk.Label(left, text="Raghavan", bg="#000055", fg="#FFFF88",
                 font=("Arial", 12, "bold")).place(x=10, y=388)
        tk.Label(left, text="Freelance Developer", bg="#000055", fg="#AACCFF",
                 font=("Arial", 8)).place(x=10, y=410)
        tk.Label(left, text="Version 1.0  |  2025", bg="#000055", fg="#7799BB",
                 font=("Arial", 7)).place(x=10, y=430)

        # Right panel
        right = tk.Frame(self, bg=BG_DARK)
        right.place(x=220, y=0, width=480, height=480)

        tk.Label(right, text="Thiruvattai Iyanar Thunai",
                 bg=BG_DARK, fg=FG_WH,
                 font=("Arial", 11, "bold")).place(x=70, y=12)

        # Ganesha image
        self._img = None
        try:
            from PIL import Image as PILImage, ImageTk
            img_path = Path(__file__).parent / "ganesha.png"
            pil_img = PILImage.open(str(img_path)).resize((110, 128),
                                                           PILImage.LANCZOS)
            self._img = ImageTk.PhotoImage(pil_img)
            tk.Label(right, image=self._img, bg=BG_DARK).place(x=185, y=38)
        except Exception:
            tk.Label(right, text="🙏", bg=BG_DARK, fg="#FFDD88",
                     font=("Arial", 52)).place(x=190, y=38)

        tk.Label(right, text="Adhwaitha Sri Plating",
                 bg=BG_DARK, fg="#FFFF00",
                 font=("Arial", 20, "bold")).place(x=30, y=185)

        pf = tk.Frame(right, bg="#000055", bd=2, relief="groove")
        pf.place(x=100, y=260, width=275, height=115)
        tk.Label(pf, text="Password", bg="#000055", fg=FG_WH,
                 font=("Arial", 10, "bold")).grid(
            row=0, column=0, columnspan=2, pady=6)
        self._pwd = tk.StringVar()
        tk.Entry(pf, textvariable=self._pwd, show="*",
                 width=20, bg=ENTRY_BG, font=FONT_ENTRY).grid(
            row=1, column=0, columnspan=2, padx=12)
        tk.Button(pf, text="Ok", command=self._check,
                  bg=BTN_WH, font=FONT_BTN, width=8).grid(
            row=2, column=0, pady=8, padx=6)
        tk.Button(pf, text="Cancel", command=self.destroy,
                  bg=BTN_WH, font=FONT_BTN, width=8).grid(
            row=2, column=1, pady=8, padx=6)

        tk.Label(right,
                 text="Warning : This Computer Program is Protected by copyright law. Unauthorized\n"
                      "reproduction or distribution of this program, or any portion of it,  may  result  in\n"
                      "severe civil and criminal penalties, and will be prosecuted to the maximum extend\n"
                      "possible under law.",
                 bg=BG_DARK, fg="#00CC00",
                 font=("Arial", 7), wraplength=460, justify="left").place(x=8, y=395)

        self.bind("<Return>", lambda _: self._check())

    def _check(self) -> None:
        if self._pwd.get() == SplashScreen._password:
            self.destroy()
            self.on_success()
        else:
            messagebox.showerror("Invalid Password",
                                 "Incorrect password.", parent=self)
            self._pwd.set("")


# ─────────────────────────────────────────────────────────────────────────────
#  Company Selector
# ─────────────────────────────────────────────────────────────────────────────

class CompanySelector(tk.Toplevel):
    def __init__(self, master: tk.Tk,
                 cpycon: sqlite3.Connection,
                 on_select: Callable) -> None:
        super().__init__(master)
        self.cpycon    = cpycon
        self.on_select = on_select
        self.title("Select Company / Year")
        self.configure(bg=BG_DARK)
        self.geometry("460x320+280+150")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=BG_HEADER, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Adhwaitha Sri Plating",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 14, "bold")).place(x=60, y=8)
        tk.Label(hdr, text="Select Financial Year",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 9)).place(x=60, y=35)

        fr = tk.Frame(self, bg=BG_DARK)
        fr.pack(fill="both", expand=True, padx=16, pady=10)

        self.lb = tk.Listbox(fr, font=FONT_ENTRY, height=8,
                             bg=ENTRY_BG, fg="#000000",
                             selectbackground=BG_DARK,
                             selectforeground=FG_WH)
        self.lb.pack(fill="both", expand=True, pady=4)
        self.lb.bind("<Double-Button-1>", lambda _: self._select())

        rows = self.cpycon.execute(
            "SELECT cpyf,cpyname,syear,eyear FROM cpydb ORDER BY syear DESC"
        ).fetchall()
        self._data = list(rows)
        for r in rows:
            self.lb.insert("end",
                           f"  {r['cpyname']}  —  FY {r['syear']}-{r['eyear']}")
        if rows:
            self.lb.selection_set(0)

        bf = tk.Frame(fr, bg=BG_DARK)
        bf.pack(pady=4)
        mkbtn(bf, "Select", self._select, width=10).pack(side="left", padx=6)
        mkbtn(bf, "New Year", self._new_year, width=10).pack(side="left", padx=6)

    def _select(self) -> None:
        idx = self.lb.curselection()
        if not idx:
            return
        r = self._data[idx[0]]
        self.destroy()
        self.on_select(r["cpyf"], r["syear"], r["eyear"])

    def _new_year(self) -> None:
        sy = _modal_input(self, "Start Year (e.g. 2025):")
        ey = _modal_input(self, "End Year (e.g. 2026):")
        if not sy or not ey:
            return
        try:
            sy_i, ey_i = int(sy), int(ey)
        except ValueError:
            messagebox.showerror("Error", "Enter valid years.", parent=self)
            return
        folder = f"ASP{sy[-2:]}{ey[-2:]}"
        try:
            self.cpycon.execute(
                "INSERT INTO cpydb(cpyname,cpyf,syear,eyear) VALUES (?,?,?,?)",
                ("Adhwaitha Sri Plating", folder, sy_i, ey_i))
            self.cpycon.commit()
            con = db.get_year_db(folder)
            con.close()
            self.lb.delete(0, "end")
            rows = self.cpycon.execute(
                "SELECT cpyf,cpyname,syear,eyear FROM cpydb ORDER BY syear DESC"
            ).fetchall()
            self._data = list(rows)
            for r in rows:
                self.lb.insert("end",
                               f"  {r['cpyname']}  —  FY {r['syear']}-{r['eyear']}")
        except sqlite3.IntegrityError:
            messagebox.showwarning("Exists",
                                   "This financial year already exists.", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Main Menu — exact match to Image 1
# ─────────────────────────────────────────────────────────────────────────────

class MainMenu(tk.Toplevel):
    def __init__(self, master: tk.Tk, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.title(f"Adhwaitha Sri Plating-{app.eyear}")
        self.configure(bg=BG_DARK)
        self.geometry("900x640+60+30")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._exit)
        self._build()

    def _build(self) -> None:
        # ── Cream header ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_HEADER, height=130)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Left Ganesha
        self._gl = self._gr = None
        try:
            from PIL import Image as PILImage, ImageTk
            img_path = Path(__file__).parent / "ganesha.png"
            pil = PILImage.open(str(img_path)).resize((80, 95), PILImage.LANCZOS)
            self._gl = ImageTk.PhotoImage(pil)
            self._gr = ImageTk.PhotoImage(pil)
            tk.Label(hdr, image=self._gl, bg=BG_HEADER, bd=0).place(x=8, y=10)
            tk.Label(hdr, image=self._gr, bg=BG_HEADER, bd=0).place(x=808, y=10)
        except Exception:
            tk.Label(hdr, text="🕉", bg=BG_HEADER, fg="#CC6600",
                     font=("Arial", 38)).place(x=10, y=8)
            tk.Label(hdr, text="🕉", bg=BG_HEADER, fg="#CC6600",
                     font=("Arial", 38)).place(x=812, y=8)

        tk.Label(hdr, text="Thiruvattai Iyanar Thunai",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 10, "bold")).place(x=260, y=5)
        tk.Label(hdr, text="Adhwaitha Sri Plating",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 24, "bold")).place(x=160, y=25)
        tk.Label(hdr,
                 text="Fac.: SF.No.233, Plot No.:c26 ,Electro Plating Industrial Park,",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 8)).place(x=140, y=78)
        tk.Label(hdr,
                 text="D.Karisalkulam, Manamadurai Taluk ,Sivagangai District.",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 8)).place(x=195, y=93)

        tk.Label(hdr, text="GST No. : 33ADZPA3791Q2ZP",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 9, "bold")).place(x=630, y=5)

        # ── Dark blue sub-header ───────────────────────────────────────────────
        sub = tk.Frame(self, bg=BG_DARK, height=30)
        sub.pack(fill="x")
        sub.pack_propagate(False)
        tk.Label(sub, text="Adhwaitha Sri Plating",
                 bg=BG_DARK, fg=FG_YEL,
                 font=("Arial", 12, "bold", "italic")).place(
            relx=0.5, rely=0.5, anchor="center")

        # ── Body: 3 columns ───────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        # LEFT column — cyan buttons
        left = tk.Frame(body, bg=BG_DARK)
        left.pack(side="left", fill="y", padx=(0, 6))
        for text, cmd in [
            ("Quotation Entry",        self.app.open_quotation),
            ("Goods Inward Receipt",   self.app.open_inward),
            ("Delivery Challan",       self.app.open_dc),
            ("Cash / Credit Bill",     self.app.open_bill),
            ("Purchase Entry",         self.app.open_purchase),
            ("Usage Entry",            self.app.open_usage),
            ("Stock",                  self.app.open_stock),
            ("Product Master",         self.app.open_product_master),
            ("Ledger Creation",        self.app.open_ledger_creation),
            ("Purchase Order",         self.app.open_po),
            ("Cheque Payment Details", self.app.open_cheque_pay),
        ]:
            tk.Button(left, text=text, command=cmd,
                      bg=BTN_CY, fg="#000000", font=FONT_BTN,
                      relief="raised", bd=2, width=24,
                      activebackground="#88FFFF", cursor="hand2"
                      ).pack(pady=2, fill="x")

        # CENTER column
        center = tk.Frame(body, bg=BG_DARK)
        center.pack(side="left", fill="both", expand=True, padx=6)

        df = tk.Frame(center, bg=BG_DARK)
        df.pack(pady=4)
        lbl(df, "FROM", font=FONT_LBL_B).pack(side="left")
        self._frm = tk.StringVar(value=fy_start(self.app.syear))
        ent(df, self._frm, width=12).pack(side="left", padx=3)
        lbl(df, "TO", font=FONT_LBL_B).pack(side="left")
        self._to = tk.StringVar(value=today_str())
        ent(df, self._to, width=12).pack(side="left", padx=3)

        # Ganesha centre
        self._cimg = None
        try:
            from PIL import Image as PILImage, ImageTk
            img_path = Path(__file__).parent / "ganesha.png"
            pil = PILImage.open(str(img_path)).resize((90, 108), PILImage.LANCZOS)
            self._cimg = ImageTk.PhotoImage(pil)
            tk.Label(center, image=self._cimg, bg=BG_DARK).pack(pady=6)
        except Exception:
            tk.Label(center, text="🙏", bg=BG_DARK, fg="#FFDD88",
                     font=("Arial", 40)).pack(pady=6)

        mkbtn(center, "Change Date", self._change_date,
              bg=BTN_WH, width=14).pack(pady=3)
        mk_exit = tk.Button(center, text="Exit", command=self._exit,
                            bg=BTN_WH, fg="#000000", font=FONT_BTN,
                            relief="raised", bd=2, width=14,
                            cursor="hand2")
        mk_exit.pack(pady=3)

        # RIGHT column — cyan buttons
        right = tk.Frame(body, bg=BG_DARK)
        right.pack(side="right", fill="y", padx=(6, 0))
        for text, cmd in [
            ("Voucher Entry",           self.app.open_voucher),
            ("Edit Voucher Entry",      self.app.open_edit_voucher),
            ("Day book",                self.app.open_daybook),
            ("LEDGER",                  self.app.open_ledger),
            ("TRIAL BALANCE",           self.app.open_trial_balance),
            ("Inward Statement",        self.app.open_inward_stmt),
            ("Datewise Bill Statement", self.app.open_bill_stmt),
            ("Sales GST Statment",      self.app.open_gst_stmt),
            ("Delete",                  self.app.open_delete),
            ("Others",                  self.app.open_others),
        ]:
            tk.Button(right, text=text, command=cmd,
                      bg=BTN_CY, fg="#000000", font=FONT_BTN,
                      relief="raised", bd=2, width=24,
                      activebackground="#88FFFF", cursor="hand2"
                      ).pack(pady=2, fill="x")

        # ── Bottom bar ─────────────────────────────────────────────────────────
        bot = tk.Frame(self, bg=BG_HEADER, height=55)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)
        tk.Label(bot, text="Developed By  Raghavan — Freelance Developer",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 8, "bold")).place(x=10, y=8)
        tk.Label(bot, text="Version 1.0",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 8)).place(x=10, y=25)
        tk.Label(bot, text="Raghavan",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 10, "bold")).place(x=800, y=8)
        tk.Label(bot, text="Version 1.0\nUpdated 2025",
                 bg=BG_HEADER, fg=FG_DARK,
                 font=("Arial", 8)).place(x=795, y=28)

    def _change_date(self) -> None:
        d = _modal_input(self, "Enter FROM date (DD/MM/YYYY):")
        if d:
            self._frm.set(parse_date(d))
        d2 = _modal_input(self, "Enter TO date (DD/MM/YYYY):")
        if d2:
            self._to.set(parse_date(d2))

    def _exit(self) -> None:
        if messagebox.askyesno("Exit", "Exit Adhwaitha Sri Plating?", parent=self):
            self.app.root.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  Document Chain Base Form
#  Exact layout from screenshots: dark blue bg, cream fields,
#  combobox To field, right-side totals, compact density.
# ─────────────────────────────────────────────────────────────────────────────

class ChainForm(tk.Toplevel):
    """
    Base for all 4 chain forms: Quotation, ItemInward, DC, Bill.
    Subclasses define: TITLE, TABLE, AUTO_FIELD, NO_LBL, DATE_LBL,
    extra header fields, button bar, cross-load behaviour.
    """
    TITLE:      str = "Form"
    TABLE:      str = "Quotation"
    AUTO_FIELD: str = "Quo"
    NO_LBL:     str = "Quotation No."
    DATE_LBL:   str = "Date"

    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title(self.TITLE)
        self.geometry("990x660+40+20")
        self.resizable(True, True)
        self._grid_vars: list[dict[str, tk.StringVar]] = []
        self._build()
        self._new_record()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # Title bar
        tb = tk.Frame(self, bg=FORM_BG)
        tb.pack(fill="x", padx=4, pady=3)
        tk.Label(tb, text=self.TITLE, bg=FORM_BG, fg=FG_YEL,
                 font=("Arial", 11, "bold")).pack(side="left")
        tk.Label(tb, text="GST No. : 33ADZPA3791Q2ZP",
                 bg=FORM_BG, fg="#FFFF00",
                 font=("Arial", 9, "bold"),
                 relief="groove", bd=1, padx=4).pack(side="right")

        # Header fields
        hf = tk.Frame(self, bg=FORM_BG)
        hf.pack(fill="x", padx=4, pady=2)
        self._build_header(hf)

        # Extra fields from subclass
        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=4)
        self._build_extra_header(ef)

        # Column headers + grid
        gf = tk.Frame(self, bg=FORM_BG)
        gf.pack(fill="x", padx=4, pady=2)
        self._build_grid(gf)

        # Totals + buttons
        bf = tk.Frame(self, bg=FORM_BG)
        bf.pack(fill="x", padx=4, pady=2)
        self._build_totals_and_buttons(bf)

    def _build_header(self, hf: tk.Frame) -> None:
        # Row 0: No. | Date
        self._no_var   = tk.StringVar()
        self._date_var = tk.StringVar(value=today_str())

        lbl(hf, f"{self.NO_LBL}", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=0, column=0, sticky="e", padx=3, pady=2)
        ent(hf, self._no_var, width=10).grid(
            row=0, column=1, sticky="w", padx=3, pady=2)
        lbl(hf, self.DATE_LBL, fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=0, column=8, sticky="e", padx=3)
        # Date as combobox-style entry with dropdown arrow (original uses DatePicker)
        ent(hf, self._date_var, width=14).grid(
            row=0, column=9, sticky="w", padx=3)

        # Row 1: To (party combobox)
        self._pname = tk.StringVar()
        self._padd  = tk.StringVar()
        lbl(hf, "To", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=1, column=0, sticky="e", padx=3, pady=2)

        # Combobox backed by party master — matches original dropdown To field
        self._party_names: list[str] = []
        self._to_cb = ttk.Combobox(hf, textvariable=self._pname,
                                   width=56, font=FONT_ENTRY)
        self._to_cb.grid(row=1, column=1, columnspan=8,
                         sticky="ew", padx=3, pady=2)
        self._to_cb.bind("<<ComboboxSelected>>", self._on_party_selected)
        self._to_cb.bind("<KeyRelease>", self._on_party_keyrelease)
        self._to_cb.bind("<FocusOut>", self._on_party_focusout)

        # Row 2: address | GST No.
        self._gstno = tk.StringVar()
        ent(hf, self._padd, width=46).grid(
            row=2, column=1, columnspan=5, sticky="ew", padx=3, pady=2)
        lbl(hf, "GST No.", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=2, column=6, sticky="e", padx=3)
        gst_e = ent(hf, self._gstno, width=20)
        gst_e.grid(row=2, column=7, columnspan=2, sticky="w", padx=3)
        gst_e.bind("<KeyRelease>", self._on_gst_keyrelease)
        gst_e.bind("<FocusOut>",   self._on_gst_focusout)

        # Row 3: Sub
        self._sub = tk.StringVar(
            value="Hard Chrome Plating and Diamond Polishing")
        lbl(hf, "Sub.", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=3, column=0, sticky="e", padx=3, pady=2)
        ent(hf, self._sub, width=72).grid(
            row=3, column=1, columnspan=8, sticky="ew", padx=3)

        # Row 4: Ref
        self._ref = tk.StringVar()
        lbl(hf, "Ref.", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=4, column=0, sticky="e", padx=3, pady=2)
        ent(hf, self._ref, width=72).grid(
            row=4, column=1, columnspan=8, sticky="ew", padx=3)

    def _build_extra_header(self, ef: tk.Frame) -> None:
        """Subclasses add extra rows (D.Slip No, ASP DC Details, etc.)"""

    def _build_grid(self, gf: tk.Frame) -> None:
        # Column headers — exact widths from screenshot
        cols = [
            ("Sl.No.", 5), ("Particulars", 34), ("", 5),
            ("CAV OD", 7), ("Micron", 7),
            ("Rate", 9), ("Qty.", 6), ("Amount", 11),
        ]
        for c, (txt, w) in enumerate(cols):
            tk.Label(gf, text=txt, bg=FORM_BG, fg=FG_WH,
                     font=FONT_GRID, width=w,
                     relief="flat", bd=0,
                     anchor="center").grid(
                row=0, column=c, sticky="ew", padx=1)

        # One active entry row (row 1)
        self._active: dict[str, tk.Variable] = {
            "slno": tk.StringVar(value=""),
            "part": tk.StringVar(),
            "cat":  tk.StringVar(),
            "od":   tk.StringVar(),
            "mic":  tk.StringVar(),
            "rate": tk.StringVar(),
            "qty":  tk.StringVar(value="1"),
            "amt":  tk.StringVar(),
        }
        av = self._active
        ent(gf, av["slno"], width=5).grid(row=1, column=0, padx=1, pady=1)

        # Particulars is a combobox (the original shows a dropdown arrow)
        self._part_cb = ttk.Combobox(gf, textvariable=av["part"],
                                     width=34, font=FONT_GRID)
        self._part_cb.grid(row=1, column=1, padx=1, pady=1)

        ent(gf, av["cat"],  width=5).grid(row=1, column=2, padx=1, pady=1)
        ent(gf, av["od"],   width=7).grid(row=1, column=3, padx=1, pady=1)
        ent(gf, av["mic"],  width=7).grid(row=1, column=4, padx=1, pady=1)
        rate_e = ent(gf, av["rate"], width=9)
        rate_e.grid(row=1, column=5, padx=1, pady=1)
        rate_e.bind("<FocusOut>", lambda _: self._calc_active())
        qty_e = ent(gf, av["qty"], width=6)
        qty_e.grid(row=1, column=6, padx=1, pady=1)
        qty_e.bind("<FocusOut>", lambda _: self._calc_active())
        qty_e.bind("<Return>",   lambda _: self._add_row())
        ent(gf, av["amt"], width=11, state="readonly"
            ).grid(row=1, column=7, padx=1, pady=1)

        # Saved items listbox (the scrollable area below in original)
        self.items_tv = ttk.Treeview(
            gf,
            columns=("sl", "part", "od", "mic", "rate", "qty", "amt"),
            show="headings", height=5)
        for col, nm, w in [
            ("sl","Sl",35), ("part","Particulars",260),
            ("od","OD",55), ("mic","Micron",55),
            ("rate","Rate",75), ("qty","Qty",45), ("amt","Amount",85),
        ]:
            self.items_tv.heading(col, text=nm)
            self.items_tv.column(col, width=w, anchor="center")
        self.items_tv.grid(row=2, column=0, columnspan=8,
                           sticky="ew", padx=1, pady=2)
        self.items_tv.bind("<Double-Button-1>", self._edit_row)
        self.items_tv.bind("<Delete>", self._delete_row)

        # Two text lines below grid
        self._line1 = tk.StringVar()
        self._line2 = tk.StringVar()
        ent(gf, self._line1, width=90).grid(
            row=3, column=0, columnspan=8, padx=1, pady=1, sticky="ew")
        ent(gf, self._line2, width=90).grid(
            row=4, column=0, columnspan=8, padx=1, pady=1, sticky="ew")

        # Internal line item store
        self._rows: list[dict] = []

    def _build_totals_and_buttons(self, bf: tk.Frame) -> None:
        # Left: HSN + GST labels
        lf = tk.Frame(bf, bg=FORM_BG)
        lf.pack(side="left", fill="y")

        self._gst_pct  = tk.StringVar(value="18")
        self._cgst_pct = tk.StringVar(value="9")
        self._sgst_pct = tk.StringVar(value="9")
        self._igst_pct = tk.StringVar(value="18")

        lbl(lf, "HSN Code : 75089010", fg=FG_WH,
            font=FONT_SMALL).grid(row=0, column=0, columnspan=6,
                                   sticky="w", padx=4, pady=1)
        gr = tk.Frame(lf, bg=FORM_BG)
        gr.grid(row=1, column=0, columnspan=6, sticky="w", padx=4)
        lbl(gr, "GST", fg=FG_YEL, font=FONT_LBL_B).pack(side="left")
        ent(gr, self._gst_pct, width=3).pack(side="left", padx=2)
        lbl(gr, "%   CGST", fg=FG_WH, font=FONT_SMALL).pack(side="left")
        ent(gr, self._cgst_pct, width=3).pack(side="left", padx=2)
        lbl(gr, "%", fg=FG_WH, font=FONT_SMALL).pack(side="left")

        ir = tk.Frame(lf, bg=FORM_BG)
        ir.grid(row=2, column=0, columnspan=6, sticky="w", padx=4)
        lbl(ir, "SGST", fg=FG_YEL, font=FONT_LBL_B).pack(side="left")
        ent(ir, self._sgst_pct, width=3).pack(side="left", padx=2)
        lbl(ir, "%   IGST", fg=FG_WH, font=FONT_SMALL).pack(side="left")
        ent(ir, self._igst_pct, width=3).pack(side="left", padx=2)
        lbl(ir, "%", fg=FG_WH, font=FONT_SMALL).pack(side="left")

        # Right: amount stack — exactly as screenshots
        rf = tk.Frame(bf, bg=FORM_BG)
        rf.pack(side="right", padx=8)

        self._tamt   = tk.StringVar(value="")
        self._cgst_v = tk.StringVar(value="")
        self._sgst_v = tk.StringVar(value="")
        self._igst_v = tk.StringVar(value="")
        self._total  = tk.StringVar(value="")

        # Taxable amount (top-right, wider box)
        ent(rf, self._tamt, width=12, state="readonly"
            ).grid(row=0, column=1, padx=4, pady=2)
        # CGST row
        lbl(rf, "CGST 9 %", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=1, column=0, sticky="e", padx=4)
        ent(rf, self._cgst_v, width=12, state="readonly"
            ).grid(row=1, column=1, padx=4, pady=2)
        # SGST row
        lbl(rf, "SGST 9 %", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=2, column=0, sticky="e", padx=4)
        ent(rf, self._sgst_v, width=12, state="readonly"
            ).grid(row=2, column=1, padx=4, pady=2)
        # IGST row
        lbl(rf, "IGST 18 %", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=3, column=0, sticky="e", padx=4)
        ent(rf, self._igst_v, width=12, state="readonly"
            ).grid(row=3, column=1, padx=4, pady=2)
        # Grand total
        ent(rf, self._total, width=12, state="readonly",
            font=("Arial", 9, "bold")
            ).grid(row=4, column=1, padx=4, pady=2)

        # Button bar
        self._build_buttons(bf)

    def _build_buttons(self, parent: tk.Frame) -> None:
        """Override in subclasses for specific button bars."""
        pass

    # ── Party autocomplete ────────────────────────────────────────────────────

    def _refresh_party_list(self) -> None:
        names = db.get_all_party_names(self.app.db)
        self._party_names = names
        self._to_cb["values"] = names

    def _on_party_selected(self, _: Any) -> None:
        name = self._pname.get().strip()
        rows = db.lookup_party(self.app.db, name)
        if rows:
            r = rows[0]
            self._padd.set(r["sub"] or "")
            self._gstno.set(r["GSTNO"] or "")
            self._calc_totals()

    def _on_party_keyrelease(self, _: Any) -> None:
        txt = self._pname.get().strip()
        if len(txt) < 2:
            return
        matches = [n for n in self._party_names
                   if n.upper().startswith(txt.upper())]
        self._to_cb["values"] = matches or self._party_names
        rows = db.lookup_party(self.app.db, txt)
        if rows and len(txt) >= 3:
            r = rows[0]
            self._padd.set(r["sub"] or "")
            self._gstno.set(r["GSTNO"] or "")
            self._calc_totals()

    def _on_party_focusout(self, _: Any) -> None:
        self._on_party_keyrelease(_)
        self._autosave_party()

    def _on_gst_keyrelease(self, _: Any) -> None:
        if len(self._gstno.get().strip()) >= 15:
            self._reverse_gst_lookup()

    def _on_gst_focusout(self, _: Any) -> None:
        self._reverse_gst_lookup()
        self._autosave_party()

    def _reverse_gst_lookup(self) -> None:
        row = db.lookup_party_by_gst(self.app.db, self._gstno.get())
        if row:
            if not self._pname.get().strip():
                self._pname.set(row["Party"])
            if not self._padd.get().strip():
                self._padd.set(row["sub"] or "")
            self._gstno.set(row["GSTNO"])
            self._calc_totals()

    def _autosave_party(self) -> None:
        pname = self._pname.get().strip()
        if len(pname) >= 3:
            db.upsert_party(self.app.db, pname,
                            self._padd.get().strip(),
                            self._gstno.get().strip())
            self._refresh_party_list()

    # ── Grid item management ──────────────────────────────────────────────────

    def _calc_active(self) -> None:
        r = to_float(self._active["rate"].get())
        q = to_float(self._active["qty"].get()) or 1
        self._active["amt"].set(fmt_amt(r * q) if r else "")
        self._calc_totals()

    def _add_row(self) -> None:
        """Add current active row to the saved items list."""
        part = self._active["part"].get().strip()
        if not part:
            return
        sl = len(self._rows) + 1
        self._active["slno"].set(str(sl))
        row = {
            "slno":  sl,
            "part":  part,
            "cat":   self._active["cat"].get().strip(),
            "od":    int(to_float(self._active["od"].get())),
            "guage": int(to_float(self._active["mic"].get())),
            "rate":  to_float(self._active["rate"].get()),
            "qty":   max(1, int(to_float(self._active["qty"].get()))),
            "AMT":   to_float(self._active["amt"].get()),
        }
        self._rows.append(row)
        self.items_tv.insert("", "end", values=(
            sl, part,
            row["od"] or "",
            row["guage"] or "",
            fmt_amt(row["rate"]),
            row["qty"],
            fmt_amt(row["AMT"]),
        ))
        # Clear active row for next entry
        for k in ("part", "cat", "od", "mic", "rate", "amt"):
            self._active[k].set("")
        self._active["qty"].set("1")
        self._active["slno"].set(str(sl + 1))
        self._calc_totals()
        self._part_cb.focus_set()

    def _edit_row(self, _: Any) -> None:
        sel = self.items_tv.selection()
        if not sel:
            return
        idx = self.items_tv.index(sel[0])
        if idx >= len(self._rows):
            return
        row = self._rows[idx]
        # Put back into active for editing
        self._active["slno"].set(str(row["slno"]))
        self._active["part"].set(row["part"])
        self._active["od"].set(str(row["od"]) if row["od"] else "")
        self._active["mic"].set(str(row["guage"]) if row["guage"] else "")
        self._active["rate"].set(fmt_amt(row["rate"]))
        self._active["qty"].set(str(row["qty"]))
        self._active["amt"].set(fmt_amt(row["AMT"]))
        # Remove from list
        self._rows.pop(idx)
        self.items_tv.delete(sel[0])
        self._calc_totals()

    def _delete_row(self, _: Any) -> None:
        sel = self.items_tv.selection()
        if not sel:
            return
        idx = self.items_tv.index(sel[0])
        if idx < len(self._rows):
            self._rows.pop(idx)
        self.items_tv.delete(sel[0])
        # Renumber
        for i, row in enumerate(self._rows):
            row["slno"] = i + 1
        self._refresh_items_tv()
        self._calc_totals()

    def _refresh_items_tv(self) -> None:
        self.items_tv.delete(*self.items_tv.get_children())
        for row in self._rows:
            self.items_tv.insert("", "end", values=(
                row["slno"], row["part"],
                row["od"] or "",
                row["guage"] or "",
                fmt_amt(row["rate"]),
                row["qty"],
                fmt_amt(row["AMT"]),
            ))

    def _get_all_rows(self) -> list[dict]:
        """Return saved rows + active row if filled."""
        rows = list(self._rows)
        part = self._active["part"].get().strip()
        if part:
            self._calc_active()
            rows.append({
                "slno":  len(rows) + 1,
                "part":  part,
                "cat":   self._active["cat"].get().strip(),
                "od":    int(to_float(self._active["od"].get())),
                "guage": int(to_float(self._active["mic"].get())),
                "rate":  to_float(self._active["rate"].get()),
                "qty":   max(1, int(to_float(self._active["qty"].get()))),
                "AMT":   to_float(self._active["amt"].get()),
            })
        return rows

    # ── GST calculation ───────────────────────────────────────────────────────

    def _calc_totals(self) -> None:
        taxable = sum(to_float(r["AMT"]) for r in self._rows)
        taxable += to_float(self._active["amt"].get())
        if taxable == 0:
            for v in (self._tamt, self._cgst_v,
                      self._sgst_v, self._igst_v, self._total):
                v.set("")
            return
        gst_pct = to_float(self._gst_pct.get()) or 18.0
        result  = calc_gst(taxable, gst_pct, self._gstno.get())
        self._tamt.set(fmt_amt(result["taxable"]))
        self._cgst_v.set(fmt_amt(result["cgst"]) if result["cgst"] else "")
        self._sgst_v.set(fmt_amt(result["sgst"]) if result["sgst"] else "")
        self._igst_v.set(fmt_amt(result["igst"]) if result["igst"] else "")
        self._total.set(fmt_amt(result["total"]))

    # ── Record CRUD ───────────────────────────────────────────────────────────

    def _new_record(self) -> None:
        nxt = db.next_no(self.app.db, self.AUTO_FIELD)
        self._no_var.set(str(nxt))
        self._date_var.set(today_str())
        self._pname.set("")
        self._padd.set("")
        self._gstno.set("")
        self._sub.set("Hard Chrome Plating and Diamond Polishing")
        self._ref.set("")
        self._line1.set("")
        self._line2.set("")
        self._rows.clear()
        self.items_tv.delete(*self.items_tv.get_children())
        for k in ("slno", "part", "cat", "od", "mic", "rate", "amt"):
            self._active[k].set("")
        self._active["qty"].set("1")
        self._active["slno"].set("1")
        for v in (self._tamt, self._cgst_v, self._sgst_v,
                  self._igst_v, self._total):
            v.set("")
        self._reset_extra()
        self._refresh_party_list()

    def _reset_extra(self) -> None:
        """Subclasses reset their extra fields."""

    def _build_header_dict(self) -> dict:
        tamt  = to_float(self._tamt.get())
        cgst  = to_float(self._cgst_v.get())
        sgst  = to_float(self._sgst_v.get())
        igst  = to_float(self._igst_v.get())
        total = to_float(self._total.get())
        return {
            "inwno":   self._no_var.get().strip(),
            "inwdate": parse_date(self._date_var.get()),
            "pname":   self._pname.get().strip(),
            "padd":    self._padd.get().strip(),
            "PGSTNO":  self._gstno.get().strip(),
            "ref":     self._ref.get().strip(),
            "SUB":     self._sub.get().strip(),
            "TAMT":    tamt,
            "CGST":    cgst,
            "SGST":    sgst,
            "IGST":    igst,
            "GST":     cgst + sgst + igst,
            "NETAMT":  total,
        }

    def _extra_header_fields(self) -> dict:
        return {}

    def _save(self) -> None:
        rows = self._get_all_rows()
        if not rows:
            messagebox.showwarning("Empty",
                                   "Enter at least one item.", parent=self)
            return
        inwno = self._no_var.get().strip()
        if not inwno:
            messagebox.showwarning("No Number",
                                   "Document number missing.", parent=self)
            return
        header = self._build_header_dict()
        header.update(self._extra_header_fields())
        db.save_doc_rows(self.app.db, self.TABLE, header, rows)
        db.upsert_party(self.app.db, header["pname"],
                        header["padd"], header["PGSTNO"])
        db.advance_no(self.app.db, self.AUTO_FIELD, int(inwno))
        messagebox.showinfo("Saved",
                            f"Saved {self.TABLE} No. {inwno}", parent=self)

    def _update(self) -> None:
        self._save()

    def _delete(self) -> None:
        inwno = self._no_var.get().strip()
        if not inwno:
            return
        if messagebox.askyesno("Delete",
                                f"Delete {self.TABLE} No. {inwno}?",
                                parent=self):
            n = db.delete_doc(self.app.db, self.TABLE, inwno)
            messagebox.showinfo("Deleted",
                                f"{n} rows deleted.", parent=self)
            self._new_record()

    def _load_by_no(self, table: str, prompt: str) -> Optional[list[sqlite3.Row]]:
        no = _modal_input(self, prompt)
        if not no:
            return None
        rows = db.load_doc(self.app.db, table, no)
        if not rows:
            messagebox.showwarning("Not Found",
                                   f"No {table} record No. {no} found.",
                                   parent=self)
            return None
        return rows

    def _fill_from_rows(self, rows: list[sqlite3.Row],
                        clear_amounts: bool = False) -> None:
        """Populate form from loaded document rows."""
        if not rows:
            return
        r0 = rows[0]
        self._pname.set(r0["pname"] or "")
        self._padd.set(r0["padd"] or "")
        self._gstno.set(r0["PGSTNO"] or "")
        self._sub.set(r0["SUB"] or "")
        self._ref.set(r0["ref"] or "")
        self._date_var.set(today_str())  # new doc gets today's date

        self._rows.clear()
        self.items_tv.delete(*self.items_tv.get_children())

        for row in rows:
            part = str(row["part"] or "").strip()
            if not part:
                continue
            amt = 0.0 if clear_amounts else to_float(row["AMT"])
            rate = 0.0 if clear_amounts else to_float(row["rate"])
            r = {
                "slno":  int(row["slno"] or 1),
                "part":  part,
                "cat":   str(row["mcat"] or ""),
                "od":    int(row["od"] or 0),
                "guage": int(row["guage"] or 0),
                "rate":  rate,
                "qty":   int(row["qty"] or 1),
                "AMT":   amt,
            }
            self._rows.append(r)
            self.items_tv.insert("", "end", values=(
                r["slno"], part,
                r["od"] or "",
                r["guage"] or "",
                fmt_amt(rate) if rate else "",
                r["qty"],
                fmt_amt(amt) if amt else "",
            ))

        if clear_amounts:
            for v in (self._tamt, self._cgst_v, self._sgst_v,
                      self._igst_v, self._total):
                v.set("")
        else:
            self._tamt.set(fmt_amt(to_float(r0["TAMT"])))
            self._cgst_v.set(fmt_amt(to_float(r0["CGST"])) if r0["CGST"] else "")
            self._sgst_v.set(fmt_amt(to_float(r0["SGST"])) if r0["SGST"] else "")
            self._igst_v.set(fmt_amt(to_float(r0["IGST"])) if r0["IGST"] else "")
            self._total.set(fmt_amt(to_float(r0["NETAMT"])))

        self._fill_extra_from_rows(rows)
        self._refresh_party_list()

    def _fill_extra_from_rows(self, rows: list[sqlite3.Row]) -> None:
        """Subclasses fill their extra fields."""

    def _get_print_data(self) -> dict:
        rows = self._get_all_rows()
        return {
            "no":    self._no_var.get(),
            "date":  self._date_var.get(),
            "pname": self._pname.get(),
            "padd":  self._padd.get(),
            "gstno": self._gstno.get(),
            "sub":   self._sub.get(),
            "ref":   self._ref.get(),
            "rows":  rows,
            "tamt":  to_float(self._tamt.get()),
            "cgst":  to_float(self._cgst_v.get()),
            "sgst":  to_float(self._sgst_v.get()),
            "igst":  to_float(self._igst_v.get()),
            "total": to_float(self._total.get()),
        }

    def _email(self) -> None:
        messagebox.showinfo("Email",
                            "Configure email in Others → Settings.", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  1. QUOTATION
# ─────────────────────────────────────────────────────────────────────────────

class QuotationForm(ChainForm):
    TITLE      = "Adhwaitha Sri Plating- Quotation"
    TABLE      = "Quotation"
    AUTO_FIELD = "Quo"
    NO_LBL     = "Quotation No."
    DATE_LBL   = "Date"

    def _build_buttons(self, parent: tk.Frame) -> None:
        bb = tk.Frame(parent, bg=FORM_BG)
        bb.pack(side="bottom", fill="x", pady=4)
        for txt, cmd, bg in [
            ("New",                   self._new_record,    BTN_WH),
            ("Save",                  self._save,          BTN_GR),
            ("Print Proforma Invoice",self._print_proforma,BTN_GR),
            ("Load Quotation",        self._load_quot,     BTN_WH),
            ("Update",                self._update,        BTN_CYAN2),
            ("Print Quotation",       self._print_quot,    BTN_WH),
            ("Delete",                self._delete,        BTN_WH),
            ("Email",                 self._email,         BTN_WH),
            ("Close",                 self.destroy,        BTN_WH),
        ]:
            tk.Button(bb, text=txt, command=cmd, bg=bg, fg="#000000",
                      font=FONT_BTN, relief="raised", bd=2, padx=6,
                      cursor="hand2").pack(side="left", padx=2)

    def _load_quot(self) -> None:
        rows = self._load_by_no("Quotation", "Enter the Quotation No.")
        if rows:
            self._no_var.set(rows[0]["inwno"])
            self._fill_from_rows(rows)

    def _print_proforma(self) -> None:
        path = pr.print_proforma(self._get_print_data(),
                                  db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved:\n{path}", parent=self)

    def _print_quot(self) -> None:
        path = pr.print_quotation(self._get_print_data(),
                                   db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved:\n{path}", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  2. ITEM INWARD
#  Loads from Quotation. Adds "Your D.Slip. No." field.
# ─────────────────────────────────────────────────────────────────────────────

class ItemInwardForm(ChainForm):
    TITLE      = "Adhwaitha Sri Plating- Item Inward"
    TABLE      = "ItemInward"
    AUTO_FIELD = "ItemInw"
    NO_LBL     = "Inward No."
    DATE_LBL   = "Date"

    def _build_extra_header(self, ef: tk.Frame) -> None:
        self._dslip   = tk.StringVar()
        self._quot_ref = tk.StringVar()
        lbl(ef, "Your D.Slip. No.", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=0, column=0, sticky="e", padx=3, pady=2)
        ent(ef, self._dslip, width=40).grid(
            row=0, column=1, sticky="w", padx=3)

    def _reset_extra(self) -> None:
        self._dslip.set("")
        self._quot_ref.set("")

    def _extra_header_fields(self) -> dict:
        return {
            "dslip":    self._dslip.get().strip(),
            "quot_ref": self._quot_ref.get().strip(),
        }

    def _fill_extra_from_rows(self, rows: list[sqlite3.Row]) -> None:
        try:
            self._dslip.set(rows[0]["dslip"] or "")
            self._quot_ref.set(rows[0]["quot_ref"] or "")
        except (KeyError, IndexError):
            pass

    def _build_buttons(self, parent: tk.Frame) -> None:
        bb = tk.Frame(parent, bg=FORM_BG)
        bb.pack(side="bottom", fill="x", pady=4)
        for txt, cmd, bg in [
            ("New /Cancel", self._new_record,  BTN_WH),
            ("Load Quotation", self._load_quot, BTN_WH),
            ("Load Inward",  self._load_inward, BTN_WH),
            ("Save",         self._save,        BTN_GR),
            ("Update",       self._update,      BTN_CYAN2),
            ("Delete",       self._delete,      BTN_WH),
            ("Close",        self.destroy,      BTN_WH),
        ]:
            tk.Button(bb, text=txt, command=cmd, bg=bg, fg="#000000",
                      font=FONT_BTN, relief="raised", bd=2, padx=6,
                      cursor="hand2").pack(side="left", padx=2)

    def _load_quot(self) -> None:
        """Load Quotation → populate Inward with Quotation data."""
        rows = self._load_by_no("Quotation", "Enter the Quotation No.")
        if not rows:
            return
        quot_no = rows[0]["inwno"]
        self._quot_ref.set(quot_no)
        # Keep Inward's own number, populate everything else
        self._fill_from_rows(rows)
        # Inward gets its own new number
        nxt = db.next_no(self.app.db, self.AUTO_FIELD)
        self._no_var.set(str(nxt))
        self._date_var.set(today_str())

    def _load_inward(self) -> None:
        rows = self._load_by_no("ItemInward", "Enter the Inward No.")
        if rows:
            self._no_var.set(rows[0]["inwno"])
            self._fill_from_rows(rows)


# ─────────────────────────────────────────────────────────────────────────────
#  3. DELIVERY CHALLAN
#  Loads from ItemInward. Amounts optional (DC is not a billing document).
#  Adds "Your D.Slip. No." field.
# ─────────────────────────────────────────────────────────────────────────────

class DCForm(ChainForm):
    TITLE      = "Adhwaitha Sri Plating- D.C"
    TABLE      = "DC"
    AUTO_FIELD = "DC"
    NO_LBL     = "DC No."
    DATE_LBL   = "DC Date"

    def _build_extra_header(self, ef: tk.Frame) -> None:
        self._dslip  = tk.StringVar()
        self._inw_ref = tk.StringVar()
        lbl(ef, "Your D.Slip. No.", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=0, column=0, sticky="e", padx=3, pady=2)
        ent(ef, self._dslip, width=40).grid(
            row=0, column=1, sticky="w", padx=3)

    def _reset_extra(self) -> None:
        self._dslip.set("")
        self._inw_ref.set("")

    def _extra_header_fields(self) -> dict:
        return {
            "dslip":   self._dslip.get().strip(),
            "inw_ref": self._inw_ref.get().strip(),
        }

    def _fill_extra_from_rows(self, rows: list[sqlite3.Row]) -> None:
        try:
            self._dslip.set(rows[0]["dslip"] or "")
            self._inw_ref.set(rows[0]["inw_ref"] or "")
        except (KeyError, IndexError):
            pass

    def _build_buttons(self, parent: tk.Frame) -> None:
        bb = tk.Frame(parent, bg=FORM_BG)
        bb.pack(side="bottom", fill="x", pady=4)
        for txt, cmd, bg in [
            ("New",        self._new_record,  BTN_WH),
            ("Load Inward",self._load_inward, BTN_WH),
            ("Load DC",    self._load_dc,     BTN_WH),
            ("Save",       self._save,        BTN_GR),
            ("Update",     self._update,      BTN_CYAN2),
            ("Print DC",   self._print_dc,    BTN_WH),
            ("Delete",     self._delete,      BTN_WH),
            ("Email",      self._email,       BTN_WH),
            ("Close",      self.destroy,      BTN_WH),
        ]:
            tk.Button(bb, text=txt, command=cmd, bg=bg, fg="#000000",
                      font=FONT_BTN, relief="raised", bd=2, padx=6,
                      cursor="hand2").pack(side="left", padx=2)

    def _load_inward(self) -> None:
        """Load Inward → populate DC. Amounts are carried over but can be cleared."""
        rows = self._load_by_no("ItemInward", "Enter the Item InWard No.")
        if not rows:
            return
        inw_no = rows[0]["inwno"]
        self._inw_ref.set(inw_no)
        self._fill_from_rows(rows, clear_amounts=False)
        nxt = db.next_no(self.app.db, self.AUTO_FIELD)
        self._no_var.set(str(nxt))
        self._date_var.set(today_str())

    def _load_dc(self) -> None:
        rows = self._load_by_no("DC", "Enter the DC No.")
        if rows:
            self._no_var.set(rows[0]["inwno"])
            self._fill_from_rows(rows)

    def _print_dc(self) -> None:
        path = pr.print_dc(self._get_print_data(),
                            db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved:\n{path}", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  4. JOB WORK BILL
#  Loads from DC. Adds ASP Pro. Inv No + ASP DC Details row.
# ─────────────────────────────────────────────────────────────────────────────

class BillForm(ChainForm):
    TITLE      = "Adhwaitha Sri Plating - Job Work Bill"
    TABLE      = "BILL"
    AUTO_FIELD = "BILL"
    NO_LBL     = "Bill No."
    DATE_LBL   = "Bill Date"

    def _build_extra_header(self, ef: tk.Frame) -> None:
        self._pro_inv = tk.StringVar()
        self._dc_ref  = tk.StringVar()
        self._dc_date = tk.StringVar()

        # Row: Ref + ASP Pro. Inv No  (matches Image 9)
        lbl(ef, "ASP Pro. Inv No", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=0, column=2, sticky="e", padx=3, pady=2)
        ent(ef, self._pro_inv, width=20).grid(
            row=0, column=3, sticky="w", padx=3)

        # Row: ASP DC Details  (matches Image 9)
        lbl(ef, "ASP DC Details", fg=FG_YEL, font=FONT_LBL_B
            ).grid(row=1, column=0, sticky="e", padx=3, pady=2)
        self._dc_details_var = tk.StringVar()
        ent(ef, self._dc_details_var, width=60).grid(
            row=1, column=1, columnspan=5, sticky="ew", padx=3)

    def _reset_extra(self) -> None:
        self._pro_inv.set("")
        self._dc_ref.set("")
        self._dc_date.set("")
        self._dc_details_var.set("")

    def _extra_header_fields(self) -> dict:
        return {
            "pro_inv": self._pro_inv.get().strip(),
            "dc_ref":  self._dc_ref.get().strip(),
            "dc_date": self._dc_date.get().strip(),
            "SDPDC":   self._dc_details_var.get().strip(),
        }

    def _fill_extra_from_rows(self, rows: list[sqlite3.Row]) -> None:
        try:
            self._pro_inv.set(rows[0]["pro_inv"] or "")
            self._dc_ref.set(rows[0]["dc_ref"] or "")
            self._dc_date.set(rows[0]["dc_date"] or "")
            self._dc_details_var.set(rows[0]["SDPDC"] or "")
        except (KeyError, IndexError):
            pass

    def _build_buttons(self, parent: tk.Frame) -> None:
        bb = tk.Frame(parent, bg=FORM_BG)
        bb.pack(side="bottom", fill="x", pady=4)
        for txt, cmd, bg in [
            ("New",                 self._new_record,   BTN_WH),
            ("Load DC",             self._load_dc,      BTN_WH),
            ("Load Proforma Invoice",self._load_proforma,BTN_WH),
            ("Save",                self._save,         BTN_GR),
            ("Print Bill",          self._print_bill,   BTN_WH),
            ("Load Bill",           self._load_bill,    BTN_WH),
            ("Update",              self._update,       BTN_CYAN2),
            ("Delete",              self._delete,       BTN_WH),
            ("Email",               self._email,        BTN_WH),
            ("Close",               self.destroy,       BTN_WH),
        ]:
            tk.Button(bb, text=txt, command=cmd, bg=bg, fg="#000000",
                      font=FONT_BTN, relief="raised", bd=2, padx=5,
                      cursor="hand2").pack(side="left", padx=2)

    def _load_dc(self) -> None:
        """Core chain: Load DC → populate Bill with all DC data + ASP DC Details."""
        rows = self._load_by_no("DC", "Enter the DC No.")
        if not rows:
            return
        dc_no   = rows[0]["inwno"]
        dc_date = rows[0]["inwdate"]
        self._dc_ref.set(dc_no)
        self._dc_date.set(dc_date)
        # Build ASP DC Details string exactly as original shows
        self._dc_details_var.set(
            f"ASP D.C. No. {dc_no}, Dated {dc_date}")
        self._fill_from_rows(rows)
        nxt = db.next_no(self.app.db, self.AUTO_FIELD)
        self._no_var.set(str(nxt))
        self._date_var.set(today_str())

    def _load_proforma(self) -> None:
        rows = self._load_by_no("Quotation", "Enter the Proforma Invoice No.")
        if not rows:
            return
        self._pro_inv.set(rows[0]["inwno"])
        self._fill_from_rows(rows)
        nxt = db.next_no(self.app.db, self.AUTO_FIELD)
        self._no_var.set(str(nxt))
        self._date_var.set(today_str())

    def _load_bill(self) -> None:
        rows = self._load_by_no("BILL", "Enter the Bill No.")
        if rows:
            self._no_var.set(rows[0]["inwno"])
            self._fill_from_rows(rows)

    def _print_bill(self) -> None:
        data = self._get_print_data()
        data["sdpdc"] = self._dc_details_var.get()
        path = pr.print_job_work_bill(data, db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved:\n{path}", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Statement / Report forms (compact, same dark-blue style)
# ─────────────────────────────────────────────────────────────────────────────

class StatementForm(tk.Toplevel):
    TITLE: str = "Statement"
    TABLE: str = "BILL"

    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title(self.TITLE)
        self.geometry("860x520+60+50")
        self._build()
        self._load()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=FORM_BG)
        hdr.pack(fill="x", padx=6, pady=4)
        lbl(hdr, self.TITLE, fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(side="left")

        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=6, pady=2)
        lbl(fr, "From", fg=FG_WH).pack(side="left")
        self._frm = tk.StringVar(value=fy_start(self.app.syear))
        ent(fr, self._frm, width=12).pack(side="left", padx=4)
        lbl(fr, "To", fg=FG_WH).pack(side="left")
        self._to_v = tk.StringVar(value=today_str())
        ent(fr, self._to_v, width=12).pack(side="left", padx=4)
        lbl(fr, "Party", fg=FG_WH).pack(side="left", padx=4)
        self._party = tk.StringVar()
        ent(fr, self._party, width=22).pack(side="left")
        mkbtn(fr, "Load", self._load, width=6).pack(side="left", padx=4)

        cols = ("No.", "Date", "Party", "Taxable",
                "CGST", "SGST", "IGST", "Net Amt")
        self.tv = ttk.Treeview(self, columns=cols,
                               show="headings", height=18)
        for c, w in zip(cols, [55, 80, 230, 80, 65, 65, 65, 85]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w, anchor="center")
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)

        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=6)
        self._summary = tk.StringVar()
        lbl(sf, "", textvariable=self._summary,
            fg=FG_YEL, font=FONT_LBL_B).pack(side="left")
        mkbtn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        try:
            pf = self._party.get().strip()
            rows = db.list_docs(self.app.db, self.TABLE, pf)
        except Exception:
            return
        tot = 0.0
        for r in rows:
            try:
                full = db.load_doc(self.app.db, self.TABLE, r["inwno"])
                if not full:
                    continue
                r0 = full[0]
                net = to_float(r0["NETAMT"])
                tot += net
                self.tv.insert("", "end", values=(
                    r0["inwno"], r0["inwdate"], r0["pname"],
                    fmt_amt(to_float(r0["TAMT"])),
                    fmt_amt(to_float(r0["CGST"])),
                    fmt_amt(to_float(r0["SGST"])),
                    fmt_amt(to_float(r0["IGST"])),
                    fmt_amt(net),
                ))
            except Exception:
                continue
        self._summary.set(
            f"Total: ₹{fmt_amt(tot)}  |  Records: {len(self.tv.get_children())}")


class InwardStatement(StatementForm):
    TITLE = "Inward Statement"
    TABLE = "ItemInward"


class BillStatement(StatementForm):
    TITLE = "Datewise Bill Statement"
    TABLE = "BILL"


class GSTStatement(StatementForm):
    TITLE = "Sales GST Statement"
    TABLE = "BILL"


# ─────────────────────────────────────────────────────────────────────────────
#  Ledger Creation
# ─────────────────────────────────────────────────────────────────────────────

class LedgerCreationForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Ledger Creation")
        self.geometry("680x520+100+70")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=FORM_BG)
        hdr.pack(fill="x", padx=6, pady=4)
        lbl(hdr, "Ledger Creation", fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(side="left")

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)
        self._name = tk.StringVar()
        self._add  = tk.StringVar()
        self._gst  = tk.StringVar()
        for i, (t, v, w) in enumerate([
            ("A/c Name", self._name, 38),
            ("Address",  self._add,  38),
            ("GST No.",  self._gst,  22),
        ]):
            lbl(ef, t, fg=FG_YEL).grid(row=i, column=0, sticky="e", padx=5, pady=3)
            ent(ef, v, width=w).grid(row=i, column=1, sticky="w", padx=4)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=3, column=0, columnspan=2, pady=8)
        for t, c, bg in [("Save", self._save, BTN_GR),
                          ("Delete", self._delete, BTN_WH),
                          ("Clear", self._clear, BTN_WH),
                          ("Close", self.destroy, BTN_WH)]:
            mkbtn(bf, t, c, bg=bg, width=8).pack(side="left", padx=4)

        self.tv = ttk.Treeview(self, columns=("Party","Address","GST"),
                               show="headings", height=14)
        for c, w in [("Party", 220), ("Address", 260), ("GST", 130)]:
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True,
                     padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        for r in db.get_all_parties(self.app.db):
            self.tv.insert("", "end",
                           values=(r["Party"], r["sub"] or "", r["GSTNO"] or ""))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if sel:
            v = self.tv.item(sel[0])["values"]
            self._name.set(v[0])
            self._add.set(v[1])
            self._gst.set(v[2])

    def _save(self) -> None:
        n = self._name.get().strip()
        if not n:
            return
        db.upsert_party(self.app.db, n,
                        self._add.get().strip(), self._gst.get().strip())
        self._refresh()

    def _delete(self) -> None:
        n = self._name.get().strip()
        if n and messagebox.askyesno("Delete", f"Delete '{n}'?", parent=self):
            self.app.db.execute("DELETE FROM HD WHERE Party=?", (n,))
            self.app.db.commit()
            self._clear()
            self._refresh()

    def _clear(self) -> None:
        self._name.set("")
        self._add.set("")
        self._gst.set("")


# ─────────────────────────────────────────────────────────────────────────────
#  Others / Settings
# ─────────────────────────────────────────────────────────────────────────────

class OthersForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Others / Settings")
        self.geometry("440x280+180+140")
        self._build()
        self._load()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=FORM_BG)
        hdr.pack(fill="x", padx=6, pady=4)
        lbl(hdr, "Others / Settings", fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(side="left")

        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="both", expand=True, padx=20, pady=10)

        self._email_v  = tk.StringVar()
        self._pwd_v    = tk.StringVar()
        self._gst_v    = tk.StringVar(value="18")
        self._newpwd_v = tk.StringVar()

        for i, (t, v, w, kw) in enumerate([
            ("Gmail Address",       self._email_v,  30, {}),
            ("Gmail Password",      self._pwd_v,    20, {"show":"*"}),
            ("Default GST %",       self._gst_v,    6,  {}),
            ("Change App Password", self._newpwd_v, 16, {"show":"*"}),
        ]):
            lbl(fr, t, fg=FG_YEL).grid(row=i, column=0, sticky="e", padx=6, pady=4)
            ent(fr, v, width=w, **kw).grid(row=i, column=1, sticky="w", padx=4)

        bf = tk.Frame(fr, bg=FORM_BG)
        bf.grid(row=4, column=0, columnspan=2, pady=12)
        mkbtn(bf, "Save", self._save, bg=BTN_GR, width=8).pack(
            side="left", padx=6)
        mkbtn(bf, "Close", self.destroy, width=8).pack(side="left", padx=6)

    def _load(self) -> None:
        row = self.app.db.execute(
            "SELECT EMAIL,PWD FROM EMAIL WHERE id=1").fetchone()
        if row:
            self._email_v.set(row[0] or "")
            self._pwd_v.set(row[1] or "")
        st = self.app.db.execute(
            "SELECT STax FROM ServTax WHERE id=1").fetchone()
        if st:
            self._gst_v.set(str(st[0]))

    def _save(self) -> None:
        self.app.db.execute(
            "UPDATE EMAIL SET EMAIL=?,PWD=?,SEMAIL=? WHERE id=1",
            (self._email_v.get(), self._pwd_v.get(), self._email_v.get()))
        self.app.db.execute(
            "UPDATE ServTax SET STax=? WHERE id=1",
            (to_float(self._gst_v.get()) or 18.0,))
        self.app.db.commit()
        np = self._newpwd_v.get().strip()
        if np:
            SplashScreen._password = np
        messagebox.showinfo("Saved", "Settings saved.", parent=self)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  Delete helper
# ─────────────────────────────────────────────────────────────────────────────

class DeleteForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Delete Record")
        self.geometry("400x220+200+180")
        self._build()

    def _build(self) -> None:
        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="both", expand=True, padx=20, pady=15)
        self._table = tk.StringVar(value="Quotation")
        self._inwno = tk.StringVar()
        lbl(fr, "Document Type", fg=FG_YEL).grid(
            row=0, column=0, sticky="e", padx=6, pady=4)
        ttk.Combobox(fr, textvariable=self._table,
                     values=["Quotation", "ItemInward", "DC",
                             "BILL", "purchase", "PO"],
                     state="readonly", width=16).grid(
            row=0, column=1, sticky="w", padx=4)
        lbl(fr, "Document No.", fg=FG_YEL).grid(
            row=1, column=0, sticky="e", padx=6, pady=4)
        ent(fr, self._inwno, width=14).grid(
            row=1, column=1, sticky="w", padx=4)
        bf = tk.Frame(fr, bg=FORM_BG)
        bf.grid(row=2, column=0, columnspan=2, pady=12)
        mkbtn(bf, "Delete", self._delete, bg=BTN_WH, width=10).pack(
            side="left", padx=6)
        mkbtn(bf, "Close", self.destroy, width=10).pack(side="left", padx=6)

    def _delete(self) -> None:
        table = self._table.get()
        inwno = self._inwno.get().strip()
        if not inwno:
            messagebox.showwarning("Required",
                                   "Enter document number.", parent=self)
            return
        if messagebox.askyesno("Confirm",
                                f"Delete {table} No. {inwno}?", parent=self):
            try:
                n = db.delete_doc(self.app.db, table, inwno)
                messagebox.showinfo("Deleted",
                                    f"{n} rows deleted.", parent=self)
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Voucher / Daybook / Ledger / Trial Balance — compact list forms
# ─────────────────────────────────────────────────────────────────────────────

class VoucherForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App",
                 edit: bool = False) -> None:
        super().__init__(master)
        self.app  = app
        self.edit = edit
        self.configure(bg=FORM_BG)
        self.title("Edit Voucher" if edit else "Voucher Entry")
        self.geometry("720x500+100+70")
        self._sel_id: Optional[int] = None
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=FORM_BG)
        hdr.pack(fill="x", padx=6, pady=4)
        lbl(hdr, self.title(), fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(side="left")

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)
        self._vdate  = tk.StringVar(value=today_str())
        self._lf     = tk.StringVar()
        self._part   = tk.StringVar()
        self._part1  = tk.StringVar()
        self._debit  = tk.StringVar(value="0.00")
        self._credit = tk.StringVar(value="0.00")
        for i, (t, v, w) in enumerate([
            ("Date",         self._vdate,  12),
            ("Ledger Folio", self._lf,     6),
            ("Particulars",  self._part,   36),
            ("Narration",    self._part1,  36),
            ("Debit (Dr)",   self._debit,  14),
            ("Credit (Cr)",  self._credit, 14),
        ]):
            lbl(ef, t, fg=FG_YEL).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ent(ef, v, width=w).grid(row=i, column=1, sticky="w", padx=4)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=6, column=0, columnspan=2, pady=8)
        mkbtn(bf, "Save", self._save, bg=BTN_GR, width=8).pack(
            side="left", padx=4)
        if self.edit:
            mkbtn(bf, "Delete", self._delete, width=8).pack(
                side="left", padx=4)
        mkbtn(bf, "Clear", self._clear, width=8).pack(side="left", padx=4)
        mkbtn(bf, "Close", self.destroy, width=8).pack(side="left", padx=4)

        cols = ("Date","Particulars","Narration","Debit","Credit")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c, w in zip(cols, [80, 220, 160, 90, 90]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8,0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        if self.edit:
            self.tv.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        for r in self.app.db.execute(
            "SELECT id,VDate,Part,Part1,Debit,Credit FROM Data "
            "ORDER BY id DESC LIMIT 500"
        ).fetchall():
            self.tv.insert("", "end", iid=str(r["id"]), values=(
                r["VDate"], r["Part"], r["Part1"] or "",
                fmt_amt(to_float(r["Debit"])),
                fmt_amt(to_float(r["Credit"]))))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if not sel:
            return
        self._sel_id = int(sel[0])
        row = self.app.db.execute(
            "SELECT * FROM Data WHERE id=?", (self._sel_id,)).fetchone()
        if row:
            self._vdate.set(row["VDate"])
            self._lf.set(str(row["LF"] or ""))
            self._part.set(row["Part"] or "")
            self._part1.set(row["Part1"] or "")
            self._debit.set(fmt_amt(to_float(row["Debit"])))
            self._credit.set(fmt_amt(to_float(row["Credit"])))

    def _save(self) -> None:
        if not self._part.get().strip():
            messagebox.showwarning("Required", "Particulars required.", parent=self)
            return
        self.app.db.execute(
            "INSERT INTO Data(VDate,LF,Part,Part1,Debit,Credit) "
            "VALUES (?,?,?,?,?,?)",
            (parse_date(self._vdate.get()),
             int(to_float(self._lf.get())),
             self._part.get().strip(), self._part1.get().strip(),
             to_float(self._debit.get()), to_float(self._credit.get())))
        self.app.db.commit()
        self._clear()
        self._refresh()

    def _delete(self) -> None:
        if self._sel_id and messagebox.askyesno(
                "Delete", "Delete this voucher?", parent=self):
            self.app.db.execute("DELETE FROM Data WHERE id=?", (self._sel_id,))
            self.app.db.commit()
            self._sel_id = None
            self._clear()
            self._refresh()

    def _clear(self) -> None:
        self._sel_id = None
        self._vdate.set(today_str())
        self._lf.set("")
        self._part.set("")
        self._part1.set("")
        self._debit.set("0.00")
        self._credit.set("0.00")


class DayBookForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Day book")
        self.geometry("780x520+80+55")
        self._build()
        self._load()

    def _build(self) -> None:
        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=8, pady=4)
        lbl(fr, "Day Book", fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(side="left", padx=8)
        self._frm = tk.StringVar(value=fy_start(self.app.syear))
        self._to_v = tk.StringVar(value=today_str())
        for t, v in [("From", self._frm), ("To", self._to_v)]:
            lbl(fr, t, fg=FG_WH).pack(side="left")
            ent(fr, v, width=12).pack(side="left", padx=4)
        mkbtn(fr, "Load", self._load, width=6).pack(side="left", padx=4)

        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=8)
        self._tot_dr = tk.StringVar()
        self._tot_cr = tk.StringVar()
        lbl(sf, "", textvariable=self._tot_dr,
            fg=FG_YEL, font=FONT_LBL_B).pack(side="left", padx=8)
        lbl(sf, "", textvariable=self._tot_cr,
            fg=FG_YEL, font=FONT_LBL_B).pack(side="left")

        cols = ("Date","Particulars","Narration","Debit","Credit")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c, w in zip(cols, [80, 270, 160, 100, 100]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8,0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        mkbtn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        tdr = tcr = 0.0
        for r in self.app.db.execute(
            "SELECT VDate,Part,Part1,Debit,Credit FROM Data "
            "ORDER BY VDate,id LIMIT 2000"
        ).fetchall():
            dr = to_float(r["Debit"])
            cr = to_float(r["Credit"])
            tdr += dr
            tcr += cr
            self.tv.insert("", "end", values=(
                r["VDate"], r["Part"], r["Part1"] or "",
                fmt_amt(dr) if dr else "",
                fmt_amt(cr) if cr else ""))
        self._tot_dr.set(f"Total Debit: {fmt_amt(tdr)}")
        self._tot_cr.set(f"Total Credit: {fmt_amt(tcr)}")


class LedgerForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("LEDGER")
        self.geometry("800x540+80+50")
        self._build()

    def _build(self) -> None:
        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=8, pady=4)
        lbl(fr, "LEDGER", fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(side="left")
        lbl(fr, "Account:", fg=FG_WH).pack(side="left", padx=8)
        self._acct = tk.StringVar()
        names = db.get_all_party_names(self.app.db)
        acb = ttk.Combobox(fr, textvariable=self._acct,
                           values=names, width=30)
        acb.pack(side="left", padx=4)
        mkbtn(fr, "Load", self._load, width=6).pack(side="left", padx=4)

        self._bal = tk.StringVar()
        lbl(self, "", textvariable=self._bal,
            fg=FG_YEL, font=FONT_LBL_B).pack(anchor="w", padx=8)

        cols = ("Date","Particulars","Debit","Credit","Balance")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c, w in zip(cols, [80, 310, 100, 100, 110]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8,0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        mkbtn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        acct = self._acct.get().strip()
        bal = 0.0
        for r in self.app.db.execute(
            "SELECT VDate,Part,Debit,Credit FROM Data "
            "WHERE Part LIKE ? ORDER BY VDate,id LIMIT 1000",
            (f"%{acct}%",)
        ).fetchall():
            dr = to_float(r["Debit"])
            cr = to_float(r["Credit"])
            bal = round(bal + dr - cr, 2)
            self.tv.insert("", "end", values=(
                r["VDate"], r["Part"],
                fmt_amt(dr) if dr else "",
                fmt_amt(cr) if cr else "",
                fmt_amt(bal)))
        self._bal.set(f"Closing Balance: {fmt_amt(bal)}")


class TrialBalanceForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("TRIAL BALANCE")
        self.geometry("700x520+90+55")
        self._build()
        self._load()

    def _build(self) -> None:
        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=8, pady=4)
        lbl(fr, "TRIAL BALANCE", fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(side="left")
        mkbtn(fr, "Refresh", self._load, width=8).pack(side="right", padx=4)

        cols = ("Account","Total Debit","Total Credit","Balance")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=20)
        for c, w in zip(cols, [270, 120, 120, 120]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8,0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=8)
        self._tot_dr = tk.StringVar()
        self._tot_cr = tk.StringVar()
        lbl(sf, "", textvariable=self._tot_dr,
            fg=FG_YEL, font=FONT_LBL_B).pack(side="left", padx=8)
        lbl(sf, "", textvariable=self._tot_cr,
            fg=FG_YEL, font=FONT_LBL_B).pack(side="left")
        mkbtn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        tdr = tcr = 0.0
        for r in self.app.db.execute(
            "SELECT Part,SUM(Debit) as dr,SUM(Credit) as cr "
            "FROM Data GROUP BY Part ORDER BY Part"
        ).fetchall():
            dr = to_float(r["dr"])
            cr = to_float(r["cr"])
            tdr += dr
            tcr += cr
            self.tv.insert("", "end", values=(
                r["Part"], fmt_amt(dr), fmt_amt(cr),
                fmt_amt(round(dr - cr, 2))))
        self._tot_dr.set(f"Total Dr: {fmt_amt(tdr)}")
        self._tot_cr.set(f"Total Cr: {fmt_amt(tcr)}")


# Simple stub windows for Purchase / Stock / PO / ChequePayment
class _SimpleListForm(tk.Toplevel):
    TITLE = "Form"
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title(self.TITLE)
        self.geometry("700x450+110+70")
        lbl(self, self.TITLE, fg=FG_YEL,
            font=("Arial", 11, "bold")).pack(padx=8, pady=8)
        mkbtn(self, "Close", self.destroy, width=10).pack(pady=4)


class PurchaseForm(_SimpleListForm):
    TITLE = "Purchase Entry"


class UsageForm(_SimpleListForm):
    TITLE = "Usage Entry"


class StockForm(_SimpleListForm):
    TITLE = "Stock"


class ProductMasterForm(_SimpleListForm):
    TITLE = "Product Master"


class POForm(_SimpleListForm):
    TITLE = "Purchase Order"


class ChequePayForm(_SimpleListForm):
    TITLE = "Cheque Payment Details"


# ─────────────────────────────────────────────────────────────────────────────
#  Application Controller
# ─────────────────────────────────────────────────────────────────────────────

class App:
    def __init__(self) -> None:
        self.root    = tk.Tk()
        self.root.withdraw()
        self.db:    sqlite3.Connection
        self.syear: int = 0
        self.eyear: int = 0
        self.cpycon = db.get_cpydb()
        SplashScreen(self.root, self._show_company_select)

    def _show_company_select(self) -> None:
        CompanySelector(self.root, self.cpycon, self._on_company_selected)

    def _on_company_selected(self, folder: str,
                              syear: int, eyear: int) -> None:
        self.syear = syear
        self.eyear = eyear
        self.db    = db.get_year_db(folder)
        MainMenu(self.root, self)

    def _g(self) -> bool:
        return hasattr(self, "db") and self.db is not None

    def open_quotation(self)       -> None:
        if self._g(): QuotationForm(self.root, self)

    def open_inward(self)          -> None:
        if self._g(): ItemInwardForm(self.root, self)

    def open_dc(self)              -> None:
        if self._g(): DCForm(self.root, self)

    def open_bill(self)            -> None:
        if self._g(): BillForm(self.root, self)

    def open_purchase(self)        -> None:
        if self._g(): PurchaseForm(self.root, self)

    def open_usage(self)           -> None:
        if self._g(): UsageForm(self.root, self)

    def open_stock(self)           -> None:
        if self._g(): StockForm(self.root, self)

    def open_product_master(self)  -> None:
        if self._g(): ProductMasterForm(self.root, self)

    def open_ledger_creation(self) -> None:
        if self._g(): LedgerCreationForm(self.root, self)

    def open_po(self)              -> None:
        if self._g(): POForm(self.root, self)

    def open_cheque_pay(self)      -> None:
        if self._g(): ChequePayForm(self.root, self)

    def open_voucher(self)         -> None:
        if self._g(): VoucherForm(self.root, self, edit=False)

    def open_edit_voucher(self)    -> None:
        if self._g(): VoucherForm(self.root, self, edit=True)

    def open_daybook(self)         -> None:
        if self._g(): DayBookForm(self.root, self)

    def open_ledger(self)          -> None:
        if self._g(): LedgerForm(self.root, self)

    def open_trial_balance(self)   -> None:
        if self._g(): TrialBalanceForm(self.root, self)

    def open_inward_stmt(self)     -> None:
        if self._g(): InwardStatement(self.root, self)

    def open_bill_stmt(self)       -> None:
        if self._g(): BillStatement(self.root, self)

    def open_gst_stmt(self)        -> None:
        if self._g(): GSTStatement(self.root, self)

    def open_delete(self)          -> None:
        if self._g(): DeleteForm(self.root, self)

    def open_others(self)          -> None:
        if self._g(): OthersForm(self.root, self)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    App().run()