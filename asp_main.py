"""
Adhwaitha Sri Plating — Management System
Rebuilt from original VB6 application.
Stack: Python 3 + Tkinter + SQLite + ReportLab
"""

from __future__ import annotations

import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk, simpledialog
from typing import Any, Callable, Optional

import asp_db as db
import asp_print as pr
from asp_utils import (
    calc_gst, fmt_amt, normalize_gstno, parse_date, today_str, to_float, fy_start,
)

# ── Colour palette (exact VB6 blue theme) ─────────────────────────────────────
BG       = "#0055CC"
BTN_BG   = "#ADD8E6"
BTN_FG   = "#000000"
HDR_BG   = "#003399"
WH       = "#FFFFFF"
FORM_BG  = "#0044BB"
LABEL_FG = "#FFFFFF"
GRID_HDR = "#003080"

FONT_MAIN  = ("Times New Roman", 13)
FONT_BOLD  = ("Times New Roman", 13, "bold")
FONT_TITLE = ("Times New Roman", 24, "bold")
FONT_SMALL = ("Times New Roman", 11)
FONT_BTN   = ("Times New Roman", 11, "bold")
FONT_LBL   = ("Times New Roman", 12)


# ─────────────────────────────────────────────────────────────────────────────
#  Widget helpers
# ─────────────────────────────────────────────────────────────────────────────

def lbl(parent: tk.Widget, text: str, **kw: Any) -> tk.Label:
    return tk.Label(
        parent, text=text,
        bg=kw.pop("bg", FORM_BG),
        fg=kw.pop("fg", LABEL_FG),
        font=kw.pop("font", FONT_LBL),
        **kw,
    )


def ent(parent: tk.Widget, var: Optional[tk.Variable] = None,
        width: int = 20, **kw: Any) -> tk.Entry:
    return tk.Entry(
        parent, textvariable=var, width=width,
        bg=WH, fg="#000000", font=FONT_MAIN,
        relief="flat", bd=0,
        highlightbackground="#999999", highlightthickness=1,
        **kw,
    )


def btn(parent: tk.Widget, text: str, cmd: Callable,
        width: int = 14, bg: str = BTN_BG, **kw: Any) -> tk.Button:
    return tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=BTN_FG, font=FONT_BTN,
        relief="raised", bd=2, width=width,
        activebackground="#87CEEB", cursor="hand2",
        **kw,
    )


def maximize_window(win: tk.Tk | tk.Toplevel) -> None:
    """Maximise window cross-platform, with a geometry fallback."""
    try:
        win.state("zoomed")
        return
    except tk.TclError:
        pass
    try:
        win.attributes("-zoomed", True)
        return
    except tk.TclError:
        pass
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{sw}x{sh}+0+0")


# ─────────────────────────────────────────────────────────────────────────────
#  Splash / Password screen
# ─────────────────────────────────────────────────────────────────────────────

class SplashScreen(tk.Toplevel):
    _password: str = "1234"

    def __init__(self, master: tk.Tk, on_success: Callable) -> None:
        super().__init__(master)
        self.on_success = on_success
        self.title("Adhwaitha Sri Plating")
        self.configure(bg=BG)
        self.geometry("700x480+250+100")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        # ── Left panel ────────────────────────────────────────────────────────
        left = tk.Frame(self, bg=HDR_BG, width=220)
        left.place(x=0, y=0, width=220, height=480)

        # Developer branding — Raghavan
        tk.Label(left, text="ASP", bg=HDR_BG,
                 fg="#FFFF00",
                 font=("Times New Roman", 36, "bold")).place(x=55, y=130)
        tk.Label(left, text="Billing\nSystem", bg=HDR_BG,
                 fg="#AADDFF",
                 font=("Times New Roman", 14, "bold")).place(x=35, y=210)

        # Icon
        tk.Label(left, text="💼", bg=HDR_BG, fg=WH,
                 font=("Arial", 28)).place(x=80, y=285)

        # Developer credits
        tk.Label(left, text="Developed By",
                 bg=HDR_BG, fg=WH,
                 font=("Times New Roman", 9, "bold"),
                 justify="left").place(x=10, y=370)
        tk.Label(left, text="Raghavan",
                 bg=HDR_BG, fg="#FFFF88",
                 font=("Times New Roman", 12, "bold"),
                 justify="left").place(x=10, y=388)
        tk.Label(left, text="Freelance Developer",
                 bg=HDR_BG, fg="#AACCFF",
                 font=("Times New Roman", 8),
                 justify="left").place(x=10, y=410)
        tk.Label(left, text="Version 1.0  |  2025",
                 bg=HDR_BG, fg="#7799BB",
                 font=("Times New Roman", 7),
                 justify="left").place(x=10, y=430)

        # ── Right panel ───────────────────────────────────────────────────────
        right = tk.Frame(self, bg=BG)
        right.place(x=220, y=0, width=480, height=480)

        # Deity text
        tk.Label(right, text="Thiruvattai Iyanar Thunai",
                 bg=BG, fg=WH,
                 font=("Times New Roman", 11, "bold")).place(x=70, y=12)

        # Ganesha / deity image
        self._deity_img = None
        try:
            from PIL import Image as PILImage, ImageTk
            import os
            img_path = str(db.BASE_DIR / "ganesha.png")
            if os.path.exists(img_path):
                pil_img = PILImage.open(img_path).resize((110, 128),
                                                          PILImage.LANCZOS)
                self._deity_img = ImageTk.PhotoImage(pil_img)
                tk.Label(right, image=self._deity_img,
                         bg=BG, bd=2, relief="solid").place(x=185, y=38)
            else:
                raise FileNotFoundError
        except Exception:
            tk.Label(right, text="🙏", bg=BG, fg="#FFDD88",
                     font=("Arial", 52)).place(x=190, y=38)

        # Company name
        tk.Label(right, text="Adhwaitha Sri Plating",
                 bg=BG, fg="#FFFF00",
                 font=("Times New Roman", 22, "bold")).place(x=30, y=185)

        # Password box
        pf = tk.Frame(right, bg="#003399", bd=2, relief="groove")
        pf.place(x=100, y=265, width=275, height=115)
        tk.Label(pf, text="Password", bg="#003399", fg=WH,
                 font=("Times New Roman", 10, "bold")).grid(
            row=0, column=0, columnspan=2, pady=6)
        self._pwd = tk.StringVar()
        tk.Entry(pf, textvariable=self._pwd, show="*",
                 width=20, bg="#FFFFCC", font=FONT_MAIN).grid(
            row=1, column=0, columnspan=2, padx=12)
        tk.Button(pf, text="Ok", command=self._check,
                  bg=BTN_BG, font=FONT_BTN, width=8,
                  relief="raised", bd=2).grid(row=2, column=0, pady=8, padx=6)
        tk.Button(pf, text="Cancel", command=self.destroy,
                  bg=BTN_BG, font=FONT_BTN, width=8,
                  relief="raised", bd=2).grid(row=2, column=1, pady=8, padx=6)

        # Warning text — green, as in original
        tk.Label(right,
                 text="Warning : This Computer Program is Protected by copyright law. Unauthorized\n"
                      "reproduction or distribution of this program, or any portion of it,  may  result  in\n"
                      "severe civil and criminal penalties, and will be prosecuted to the maximum extend\n"
                      "possible under law.",
                 bg=BG, fg="#00CC00",
                 font=("Times New Roman", 8),
                 wraplength=460, justify="left").place(x=8, y=395)

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
#  Company selector
# ─────────────────────────────────────────────────────────────────────────────

class CompanySelector(tk.Toplevel):
    def __init__(self, master: tk.Tk,
                 cpycon: sqlite3.Connection,
                 on_select: Callable) -> None:
        super().__init__(master)
        self.cpycon    = cpycon
        self.on_select = on_select
        self.title("Select Company / Year")
        self.configure(bg=BG)
        self.geometry("500x340+300+150")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG, height=70)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏭", bg=HDR_BG, fg=WH,
                 font=("Arial", 28)).place(x=10, y=10)
        tk.Label(hdr, text="Adhwaitha Sri Plating",
                 bg=HDR_BG, fg=WH,
                 font=("Times New Roman", 14, "bold")).place(x=70, y=8)
        tk.Label(hdr,
                 text="Chrome Plating, Zinc Plating, Electroless Nickel Plating",
                 bg=HDR_BG, fg="#AACCFF",
                 font=("Times New Roman", 8)).place(x=70, y=35)

        fr = tk.Frame(self, bg=BG)
        fr.pack(fill="both", expand=True, padx=20, pady=10)
        lbl(fr, "Select Financial Year:", font=FONT_BOLD).pack(anchor="w")

        self.lb = tk.Listbox(fr, font=FONT_MAIN, height=8,
                             selectbackground=HDR_BG,
                             selectforeground=WH)
        self.lb.pack(fill="both", expand=True, pady=4)
        self.lb.bind("<Double-Button-1>", lambda _: self._select())

        rows = self.cpycon.execute(
            "SELECT cpyf, cpyname, syear, eyear FROM cpydb ORDER BY syear DESC"
        ).fetchall()
        self._data = list(rows)
        for r in rows:
            self.lb.insert("end",
                           f"  {r['cpyname']}  —  FY {r['syear']}-{r['eyear']}")
        if rows:
            self.lb.selection_set(0)

        btn_fr = tk.Frame(fr, bg=BG)
        btn_fr.pack(pady=4)
        btn(btn_fr, "Select", self._select, width=10).pack(side="left", padx=6)
        btn(btn_fr, "New Year", self._new_year, width=10).pack(side="left", padx=6)

    def _select(self) -> None:
        idx = self.lb.curselection()
        if not idx:
            return
        r = self._data[idx[0]]
        self.destroy()
        self.on_select(r["cpyf"], r["syear"], r["eyear"])

    def _new_year(self) -> None:
        NewYearDialog(self, self.cpycon, self._refresh)

    def _refresh(self) -> None:
        self.lb.delete(0, "end")
        rows = self.cpycon.execute(
            "SELECT cpyf, cpyname, syear, eyear FROM cpydb ORDER BY syear DESC"
        ).fetchall()
        self._data = list(rows)
        for r in rows:
            self.lb.insert("end",
                           f"  {r['cpyname']}  —  FY {r['syear']}-{r['eyear']}")


class NewYearDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget,
                 cpycon: sqlite3.Connection,
                 on_done: Callable) -> None:
        super().__init__(master)
        self.cpycon  = cpycon
        self.on_done = on_done
        self.title("Add Financial Year")
        self.configure(bg=FORM_BG)
        self.geometry("340x180+350+250")
        self.grab_set()
        self._build()

    def _build(self) -> None:
        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="both", expand=True, padx=20, pady=15)
        lbl(fr, "Start Year (e.g. 2025)").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self._sy = tk.StringVar()
        ent(fr, self._sy, width=8).grid(row=0, column=1, sticky="w", padx=4)
        lbl(fr, "End Year (e.g. 2026)").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self._ey = tk.StringVar()
        ent(fr, self._ey, width=8).grid(row=1, column=1, sticky="w", padx=4)
        bf = tk.Frame(fr, bg=FORM_BG)
        bf.grid(row=2, column=0, columnspan=2, pady=10)
        btn(bf, "Create", self._create, width=8).pack(side="left", padx=6)
        btn(bf, "Cancel", self.destroy, width=8).pack(side="left", padx=6)

    def _create(self) -> None:
        try:
            sy = int(self._sy.get())
            ey = int(self._ey.get())
        except ValueError:
            messagebox.showerror("Error", "Enter valid years.", parent=self)
            return
        folder = f"ASP{str(sy)[-2:]}{str(ey)[-2:]}"
        try:
            self.cpycon.execute(
                "INSERT INTO cpydb(cpyname,cpyf,syear,eyear) VALUES (?,?,?,?)",
                ("Adhwaitha Sri Plating", folder, sy, ey)
            )
            self.cpycon.commit()
            # Initialise DB schema
            con = db.get_year_db(folder)
            con.close()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Exists",
                                   "This financial year already exists.", parent=self)
            return
        self.destroy()
        self.on_done()


# ─────────────────────────────────────────────────────────────────────────────
#  Main Menu
# ─────────────────────────────────────────────────────────────────────────────

class MainMenu(tk.Toplevel):
    def __init__(self, master: tk.Tk, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.title(f"Adhwaitha Sri Plating — FY {app.syear}-{app.eyear}")
        self.configure(bg=BG)
        self.geometry("900x620+80+40")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._exit)
        self._build()
        maximize_window(self)

    def _build(self) -> None:
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=WH, height=120)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Left Ganesha image
        self._ganesha_left = None
        self._ganesha_right = None
        try:
            from PIL import Image as PILImage, ImageTk
            import os
            img_path = str(db.BASE_DIR / "ganesha.png")
            if os.path.exists(img_path):
                pil_img = PILImage.open(img_path).resize((80, 95), PILImage.LANCZOS)
                self._ganesha_left  = ImageTk.PhotoImage(pil_img)
                self._ganesha_right = ImageTk.PhotoImage(pil_img)
                tk.Label(hdr, image=self._ganesha_left,
                         bg=WH, bd=0).place(x=8, y=10)
                tk.Label(hdr, image=self._ganesha_right,
                         bg=WH, bd=0).place(x=812, y=10)
            else:
                raise FileNotFoundError
        except Exception:
            tk.Label(hdr, text="🕉", bg=WH, fg="#CC6600",
                     font=("Arial", 42)).place(x=12, y=5)
            tk.Label(hdr, text="🕉", bg=WH, fg="#CC6600",
                     font=("Arial", 42)).place(x=815, y=5)

        # Company name — dark blue bold, large
        tk.Label(hdr, text="Adhwaitha Sri Plating",
                 bg=WH, fg="#000080",
                 font=("Times New Roman", 26, "bold")).place(x=100, y=5)

        # Full address — all 4 lines fully visible
        tk.Label(hdr,
                 text="Fac.: SF.No.233, Plot No.: C 26, Electro Plating Industrial Park, Adhanur,",
                 bg=WH, fg="#000000",
                 font=("Times New Roman", 8)).place(x=100, y=50)
        tk.Label(hdr,
                 text="D.Karisalkulam, Manamadurai Taluk, Sivagangai District. Tamilnadu - 630411.",
                 bg=WH, fg="#000000",
                 font=("Times New Roman", 8)).place(x=100, y=63)
        tk.Label(hdr,
                 text="Mobile No. 63693 73649, 99944 43530",
                 bg=WH, fg="#000000",
                 font=("Times New Roman", 8)).place(x=100, y=76)
        tk.Label(hdr,
                 text="GST No. : 33ADZPA3791Q2ZP",
                 bg=WH, fg="#000000",
                 font=("Times New Roman", 8, "bold")).place(x=100, y=89)

        # FY + date top-right
        tk.Label(hdr, text=f"FY: {self.app.syear}-{self.app.eyear}",
                 bg=WH, fg=HDR_BG,
                 font=("Times New Roman", 9, "bold")).place(x=660, y=5)
        tk.Label(hdr, text=today_str(), bg=WH, fg=HDR_BG,
                 font=("Times New Roman", 9)).place(x=672, y=20)

        tk.Frame(self, bg=HDR_BG, height=4).pack(fill="x")

        sub = tk.Frame(self, bg=BG, height=36)
        sub.pack(fill="x")
        sub.pack_propagate(False)
        tk.Label(sub, text="Adhwaitha Sri Plating",
                 bg=BG, fg=WH,
                 font=("Times New Roman", 14, "bold")).place(relx=0.5, rely=0.5,
                                                              anchor="center")

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        # LEFT
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="y", padx=(0, 8))
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
            btn(left, text, cmd, width=24).pack(pady=2, fill="x")

        # CENTER
        center = tk.Frame(body, bg=BG)
        center.pack(side="left", fill="both", expand=True, padx=8)

        df = tk.Frame(center, bg=BG)
        df.pack(pady=6)
        lbl(df, "FROM", font=FONT_BOLD).pack(side="left", padx=3)
        self._frm = tk.StringVar(value=fy_start(self.app.syear))
        ent(df, self._frm, width=12).pack(side="left")
        lbl(df, "TO", font=FONT_BOLD).pack(side="left", padx=3)
        self._to = tk.StringVar(value=today_str())
        ent(df, self._to, width=12).pack(side="left")

        tk.Label(center, text="👤", bg=BG, fg=WH,
                 font=("Arial", 48)).pack(pady=6)

        btn(center, "Change Date", self._change_date, width=14).pack(pady=3)
        btn(center, "EXIT", self._exit, width=14, bg="#FF9999").pack(pady=3)

        # RIGHT
        right = tk.Frame(body, bg=BG)
        right.pack(side="right", fill="y", padx=(8, 0))
        for text, cmd in [
            ("Voucher Entry",           self.app.open_voucher),
            ("Edit Voucher Entry",      self.app.open_edit_voucher),
            ("Day Book",                self.app.open_daybook),
            ("LEDGER",                  self.app.open_ledger),
            ("TRIAL BALANCE",           self.app.open_trial_balance),
            ("Inward Statement",        self.app.open_inward_stmt),
            ("Datewise Bill Statement", self.app.open_bill_stmt),
            ("Sales GST Statement",     self.app.open_gst_stmt),
            ("Delete",                  self.app.open_delete),
            ("Others",                  self.app.open_others),
        ]:
            btn(right, text, cmd, width=24).pack(pady=2, fill="x")

    def _change_date(self) -> None:
        d = simpledialog.askstring("InvSDP", "Enter FROM date (DD/MM/YYYY):", parent=self)
        if d:
            self._frm.set(parse_date(d.strip()))
        d2 = simpledialog.askstring("InvSDP", "Enter TO date (DD/MM/YYYY):", parent=self)
        if d2:
            self._to.set(parse_date(d2.strip()))

    def _exit(self) -> None:
        if messagebox.askyesno("Exit", "Exit Adhwaitha Sri Plating?", parent=self):
            self.app.root.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  Generic Load Dialog
# ─────────────────────────────────────────────────────────────────────────────

class LoadDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App",
                 table: str, on_select: Callable) -> None:
        super().__init__(master)
        self.app       = app
        self.table     = table
        self.on_select = on_select
        self.title(f"Load — {table}")
        self.configure(bg=FORM_BG)
        self.geometry("720x420+130+130")
        self.grab_set()
        self._build()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Select — {self.table}",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=8, pady=4)
        lbl(sf, "Search party:").pack(side="left")
        self._q = tk.StringVar()
        ent(sf, self._q, width=28).pack(side="left", padx=4)
        btn(sf, "Search", self._search, width=8).pack(side="left")

        cols = ("No.", "Date", "Party", "Net Amt")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c, w in zip(cols, [70, 90, 360, 100]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)

        self.tv.bind("<Double-Button-1>", lambda _: self._select())
        btn(self, "Select", self._select, width=10).pack(pady=4)
        self._search()

    def _search(self) -> None:
        self.tv.delete(*self.tv.get_children())
        try:
            rows = db.list_docs(self.app.db, self.table, self._q.get().strip())
            for r in rows:
                net = fmt_amt(float(r["NETAMT"])) if r["NETAMT"] else ""
                self.tv.insert("", "end",
                               values=(r["inwno"], r["inwdate"], r["pname"], net))
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)

    def _select(self) -> None:
        sel = self.tv.selection()
        if not sel:
            return
        inwno = str(self.tv.item(sel[0])["values"][0])
        try:
            rows = db.load_doc(self.app.db, self.table, inwno)
            self.destroy()
            self.on_select(rows)
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Entry Form Base (Quotation / DC / Bill / Inward)
# ─────────────────────────────────────────────────────────────────────────────

class EntryFormBase(tk.Toplevel):
    TITLE:       str = "Entry Form"
    TABLE:       str = "Quotation"
    AUTO_FIELD:  str = "Quo"
    NO_LBL:      str = "No."
    N_ROWS:      int = 8
    SEPARATE_DATE_ROW: bool = False

    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title(self.TITLE)
        self.geometry("920x600+50+30")
        self.resizable(True, True)
        self.minsize(1024, 680)
        self._grid_vars: list[dict[str, tk.StringVar]] = []
        self._build()
        self._new_record()
        maximize_window(self)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main = tk.Frame(self, bg=FORM_BG)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # Title bar
        hdr = tk.Frame(main, bg=HDR_BG)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        self._fy_no = tk.StringVar()
        tk.Label(hdr, text="FY No.:", bg=HDR_BG, fg=WH,
                 font=FONT_SMALL).grid(row=0, column=0, padx=(8, 2), pady=4)
        ent(hdr, self._fy_no, width=16,
            state="readonly").grid(row=0, column=0, padx=(70, 0), pady=4)
        tk.Label(hdr, text=self.TITLE, bg=HDR_BG, fg=WH,
                 font=FONT_TITLE).grid(row=0, column=1, pady=6)
        # right spacer to balance centering
        tk.Label(hdr, text="", bg=HDR_BG, width=12).grid(row=0, column=2)

        # Header fields
        hf = tk.Frame(main, bg=FORM_BG)
        hf.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        for c in range(10):
            hf.grid_columnconfigure(c, weight=0)
        for c in range(1, 9):
            hf.grid_columnconfigure(c, weight=1)

        self._no_var   = tk.StringVar()
        self._date_var = tk.StringVar(value=today_str())
        if self.SEPARATE_DATE_ROW:
            # DC-style: No. on row 0, Date on row 1, well separated
            lbl(hf, self.NO_LBL, font=FONT_BOLD).grid(row=0, column=0, sticky="e", padx=6, pady=4)
            ent(hf, self._no_var, width=14).grid(row=0, column=1, columnspan=2, sticky="w", padx=6, pady=4)
            lbl(hf, "Date", font=FONT_BOLD).grid(row=1, column=0, sticky="e", padx=6, pady=4)
            ent(hf, self._date_var, width=14).grid(row=1, column=1, columnspan=2, sticky="w", padx=6, pady=4)
            self._hdr_row_offset = 2  # subsequent rows shift down
        else:
            lbl(hf, self.NO_LBL).grid(row=0, column=0, sticky="e", padx=3, pady=2)
            ent(hf, self._no_var, width=10).grid(row=0, column=1, sticky="w", padx=3, pady=2)
            lbl(hf, "Date").grid(row=0, column=8, sticky="e", padx=3)
            ent(hf, self._date_var, width=13).grid(row=0, column=9, sticky="w", padx=3)
            self._hdr_row_offset = 1

        ro = self._hdr_row_offset  # row offset
        self._pname = tk.StringVar()
        self._padd  = tk.StringVar()
        lbl(hf, "To").grid(row=ro, column=0, sticky="ne", padx=3, pady=2)
        pe = ent(hf, self._pname, width=58)
        pe.grid(row=ro, column=1, columnspan=8, sticky="ew", padx=3, pady=2)
        self._party_entry = pe
        pe.bind("<FocusOut>", self._on_party_focusout)
        pe.bind("<KeyRelease>", self._autocomplete)
        pe.bind("<Return>", self._on_entry_return)
        pe.bind("<Escape>", lambda e: self._close_autocomplete_popup())

        self._gstno = tk.StringVar()
        ent(hf, self._padd, width=46).grid(row=ro+1, column=1, columnspan=5,
                                            sticky="ew", padx=3, pady=2)
        lbl(hf, "GST No.").grid(row=ro+1, column=6, sticky="e", padx=3)
        gst_entry = ent(hf, self._gstno, width=18)
        gst_entry.grid(row=ro+1, column=7, columnspan=2, sticky="w", padx=3)
        gst_entry.bind("<KeyRelease>", self._on_gst_keyrelease)
        gst_entry.bind("<FocusOut>",   self._on_gst_focusout)
        btn(hf, "Save Customer", self._save_customer, width=12).grid(
            row=ro+1, column=9, sticky="w", padx=3
        )

        self._sub = tk.StringVar(
            value="Hard Chrome Plating and Diamond Polishing")
        lbl(hf, "Sub").grid(row=ro+2, column=0, sticky="e", padx=3, pady=2)
        ent(hf, self._sub, width=58).grid(row=ro+2, column=1, columnspan=8,
                                           sticky="ew", padx=3, pady=2)

        self._ref = tk.StringVar()
        lbl(hf, "Ref").grid(row=ro+3, column=0, sticky="e", padx=3, pady=2)
        ent(hf, self._ref, width=58).grid(row=ro+3, column=1, columnspan=8,
                                           sticky="ew", padx=3, pady=2)

        self._build_extra_header(hf)

        # Grid
        gf = tk.Frame(main, bg=FORM_BG)
        gf.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)
        gf.grid_columnconfigure(0, weight=1)
        self._build_grid(gf)

        # Totals
        tf = tk.Frame(main, bg=FORM_BG)
        tf.grid(row=3, column=0, sticky="ew", padx=10, pady=4)
        self._build_totals(tf)

        # Buttons
        bf = tk.Frame(main, bg=HDR_BG)
        bf.grid(row=4, column=0, sticky="ew", pady=(6, 4))
        for text, cmd, color in self._buttons():
            tk.Button(bf, text=text, command=cmd,
                      bg=color, fg=BTN_FG, font=FONT_BTN,
                      relief="raised", bd=2, padx=5,
                      activebackground="#87CEEB", cursor="hand2"
                      ).pack(side="left", padx=3, pady=4)

    def _build_extra_header(self, parent: tk.Frame) -> None:
        """Subclasses add extra header rows (PDC, SDPDC)."""

    def _build_grid(self, parent: tk.Frame) -> None:
        cols = [("Sl.", 4), ("Particulars", 42),
                ("CAV OD", 9), ("Micron", 8),
                ("Rate", 11), ("Qty", 7), ("Amount", 13)]
        # Use a sub-frame so we can draw vertical separator lines
        # Columns: 0=Sl, sep, 1=Part, sep, 2=OD, sep, 3=Mic, sep, 4=Rate, sep, 5=Qty, sep, 6=Amt
        # Grid col indices: data at 0,2,4,6,8,10,12  separators at 1,3,5,7,9,11
        n_data_cols = len(cols)
        col_weights = [1, 9, 2, 2, 2, 2, 3]
        for c in range(n_data_cols):
            gc = c * 2  # actual grid column (data)
            parent.grid_columnconfigure(gc, weight=col_weights[c])
        # Separator columns get zero weight, fixed width
        for c in range(n_data_cols - 1):
            gc = c * 2 + 1
            parent.grid_columnconfigure(gc, weight=0, minsize=1)

        # Header row
        for c, (txt, w) in enumerate(cols):
            gc = c * 2
            tk.Label(parent, text=txt, bg=GRID_HDR, fg=WH,
                     font=("Times New Roman", 12, "bold"),
                     width=w, relief="flat", bd=0
                     ).grid(row=0, column=gc, sticky="nsew", padx=0, pady=0)
        # Header separator line (bottom of header)
        sep_hdr = tk.Frame(parent, bg="#333333", height=2)
        sep_hdr.grid(row=1, column=0, columnspan=n_data_cols * 2 - 1, sticky="ew")

        # Vertical separators spanning all rows
        total_rows = self.N_ROWS + 3  # header + data rows + 2 extra text rows
        for c in range(n_data_cols - 1):
            gc = c * 2 + 1
            vsep = tk.Frame(parent, bg="#888888", width=1)
            vsep.grid(row=0, column=gc, rowspan=total_rows + 1, sticky="ns")

        for r in range(self.N_ROWS):
            parent.grid_rowconfigure(r + 2, weight=1)
            rv: dict[str, tk.StringVar] = {
                k: tk.StringVar() for k in
                ("slno", "part", "od", "mic", "rate", "qty", "amt")
            }
            rv["slno"].set(str(r + 1))
            rv["qty"].set("1")
            self._grid_vars.append(rv)

            tk.Label(parent, textvariable=rv["slno"],
                     bg=WH, fg="#000", width=4,
                     relief="flat", bd=0,
                     font=FONT_MAIN).grid(row=r+2, column=0, padx=0, pady=0, sticky="nsew")
            ent(parent, rv["part"], width=36).grid(row=r+2, column=2, padx=0, pady=0, sticky="nsew")
            ent(parent, rv["od"],   width=7).grid(row=r+2, column=4, padx=0, pady=0, sticky="nsew")
            ent(parent, rv["mic"],  width=6).grid(row=r+2, column=6, padx=0, pady=0, sticky="nsew")

            re_ = ent(parent, rv["rate"], width=9)
            re_.grid(row=r+2, column=8, padx=0, pady=0, sticky="nsew")
            re_.bind("<FocusOut>", lambda _, v=rv: self._calc_row(v))

            qe = ent(parent, rv["qty"], width=5)
            qe.grid(row=r+2, column=10, padx=0, pady=0, sticky="nsew")
            qe.bind("<FocusOut>", lambda _, v=rv: self._calc_row(v))

            ent(parent, rv["amt"], width=11,
                state="readonly").grid(row=r+2, column=12, padx=0, pady=0, sticky="nsew")

        self._extra1 = tk.StringVar()
        self._extra2 = tk.StringVar()
        for i, v in enumerate((self._extra1, self._extra2)):
            ent(parent, v, width=90).grid(
                row=self.N_ROWS + 2 + i, column=0, columnspan=n_data_cols * 2 - 1,
                padx=1, pady=1, sticky="ew")

    def _build_totals(self, parent: tk.Frame) -> None:
        lf = tk.Frame(parent, bg=FORM_BG)
        lf.pack(side="left", fill="y")

        self._gst_pct  = tk.StringVar(value="18")
        self._cgst_pct = tk.StringVar(value="9")
        self._sgst_pct = tk.StringVar(value="9")
        self._igst_pct = tk.StringVar(value="18")

        lbl(lf, f"HSN Code : 75089010").grid(row=0, column=0, sticky="w", padx=4)
        gr = tk.Frame(lf, bg=FORM_BG)
        gr.grid(row=1, column=0, sticky="w", padx=4)
        lbl(gr, "GST").pack(side="left")
        ent(gr, self._gst_pct, width=3).pack(side="left", padx=2)
        lbl(gr, "%   CGST").pack(side="left")
        ent(gr, self._cgst_pct, width=3).pack(side="left", padx=2)
        lbl(gr, "%  SGST").pack(side="left")
        ent(gr, self._sgst_pct, width=3).pack(side="left", padx=2)
        lbl(gr, "%").pack(side="left")
        ir = tk.Frame(lf, bg=FORM_BG)
        ir.grid(row=2, column=0, sticky="w", padx=4)
        lbl(ir, "IGST").pack(side="left")
        ent(ir, self._igst_pct, width=3).pack(side="left", padx=2)
        lbl(ir, "%").pack(side="left")
        lbl(lf, "Labour Charges").grid(row=3, column=0, sticky="w", padx=4, pady=2)

        rf = tk.Frame(parent, bg=FORM_BG)
        rf.pack(side="right", fill="y", padx=8)

        self._tamt   = tk.StringVar(value="0.00")
        self._cgst_v = tk.StringVar(value="0.00")
        self._sgst_v = tk.StringVar(value="0.00")
        self._igst_v = tk.StringVar(value="0.00")
        self._total  = tk.StringVar(value="0.00")

        self._totals_widgets = {}
        for i, (key, lbl_t, var) in enumerate([
            ("tamt", "Taxable Amount", self._tamt),
            ("cgst", "CGST @ 9 %",     self._cgst_v),
            ("sgst", "SGST @ 9 %",     self._sgst_v),
            ("igst", "IGST @ 18 %",    self._igst_v),
            ("total", "Grand Total",    self._total),
        ]):
            l = lbl(rf, f"{lbl_t} :")
            l.grid(row=i, column=0, sticky="e", padx=4, pady=1)
            e = ent(rf, var, width=12, state="readonly")
            e.grid(row=i, column=1, padx=4, pady=1)
            self._totals_widgets[key] = (l, e, i)

        self._update_totals_grid()

    def _buttons(self) -> list[tuple[str, Callable, str]]:
        return [
            ("&New",    self._new_record, BTN_BG),
            ("&Save",   self._save,       "#90EE90"),
            ("&Load",   self._load,       BTN_BG),
            ("&Update", self._update,     BTN_BG),
            ("&Delete", self._delete,     "#FFB6C1"),
            ("&Print",  self._print,      BTN_BG),
            ("Email",   self._email,      BTN_BG),
            ("&Close",  self.destroy,     BTN_BG),
        ]

    # ── Business logic ────────────────────────────────────────────────────────

    def _update_totals_grid(self) -> None:
        if not hasattr(self, "_totals_widgets"):
            return
        gstno = normalize_gstno(self._gstno.get())
        state_code = gstno[:2]
        intrastate = (state_code == "33") or (not gstno)
        
        self._totals_widgets["tamt"][0].grid(row=0, column=0, sticky="e")
        self._totals_widgets["tamt"][1].grid(row=0, column=1)
        
        if intrastate:
            self._totals_widgets["igst"][0].grid_forget()
            self._totals_widgets["igst"][1].grid_forget()
            
            self._totals_widgets["cgst"][0].grid(row=1, column=0, sticky="e", padx=4, pady=1)
            self._totals_widgets["cgst"][1].grid(row=1, column=1, padx=4, pady=1)
            self._totals_widgets["sgst"][0].grid(row=2, column=0, sticky="e", padx=4, pady=1)
            self._totals_widgets["sgst"][1].grid(row=2, column=1, padx=4, pady=1)
            
            self._totals_widgets["total"][0].grid(row=3, column=0, sticky="e", padx=4, pady=1)
            self._totals_widgets["total"][1].grid(row=3, column=1, padx=4, pady=1)
        else:
            self._totals_widgets["cgst"][0].grid_forget()
            self._totals_widgets["cgst"][1].grid_forget()
            self._totals_widgets["sgst"][0].grid_forget()
            self._totals_widgets["sgst"][1].grid_forget()
            
            self._totals_widgets["igst"][0].grid(row=1, column=0, sticky="e", padx=4, pady=1)
            self._totals_widgets["igst"][1].grid(row=1, column=1, padx=4, pady=1)
            
            self._totals_widgets["total"][0].grid(row=2, column=0, sticky="e", padx=4, pady=1)
            self._totals_widgets["total"][1].grid(row=2, column=1, padx=4, pady=1)

    def _on_entry_return(self, event: Any) -> None:
        if hasattr(self, "_autocomplete_popup") and self._autocomplete_popup.winfo_exists():
            if self._autocomplete_list.size() > 0:
                self._autocomplete_list.selection_set(0)
                self._on_popup_select()

    def _on_popup_select(self, event: Any = None) -> None:
        if not hasattr(self, "_autocomplete_list"):
            return
        sel = self._autocomplete_list.curselection()
        if sel:
            idx = sel[0]
            row = self._autocomplete_data[idx]
            self._pname.set(row["Party"])
            self._padd.set(row["sub"] or "")
            self._gstno.set(normalize_gstno(row["GSTNO"] or ""))
            self._calc_totals()
            self._close_autocomplete_popup()
            self._party_entry.focus_set()

    def _close_autocomplete_popup(self) -> None:
        if hasattr(self, "_autocomplete_popup") and self._autocomplete_popup.winfo_exists():
            self._autocomplete_popup.destroy()

    def _on_popup_focusout(self, event: Any) -> None:
        self.after(100, self._check_focus_and_close)

    def _check_focus_and_close(self) -> None:
        if not hasattr(self, "_autocomplete_popup") or not self._autocomplete_popup.winfo_exists():
            return
        focus = self.focus_get()
        if focus not in (self._party_entry, self._autocomplete_list):
            self._close_autocomplete_popup()

    def _autocomplete(self, event: Any) -> None:
        if event.keysym in ("Down", "Up", "Return", "Escape", "Tab"):
            if event.keysym == "Down" and hasattr(self, "_autocomplete_popup") and self._autocomplete_popup.winfo_exists():
                self._autocomplete_list.focus_set()
                if self._autocomplete_list.size() > 0:
                    self._autocomplete_list.selection_clear(0, "end")
                    self._autocomplete_list.selection_set(0)
                    self._autocomplete_list.activate(0)
            return

        txt = self._pname.get().strip()
        if not txt:
            self._close_autocomplete_popup()
            return

        rows = db.lookup_party(self.app.db, txt)
        if not rows:
            self._close_autocomplete_popup()
            return

        if not hasattr(self, "_autocomplete_popup") or not self._autocomplete_popup.winfo_exists():
            self._autocomplete_popup = tk.Toplevel(self)
            self._autocomplete_popup.wm_overrideredirect(True)
            self._autocomplete_list = tk.Listbox(
                self._autocomplete_popup, font=FONT_MAIN,
                bg=WH, fg="#000000", bd=1, relief="solid",
                selectbackground="#90EE90", selectforeground="black"
            )
            self._autocomplete_list.pack(fill="both", expand=True)
            self._autocomplete_list.bind("<Double-Button-1>", self._on_popup_select)
            self._autocomplete_list.bind("<Return>", self._on_popup_select)
            self._autocomplete_list.bind("<Escape>", lambda e: self._close_autocomplete_popup())
            self._autocomplete_list.bind("<FocusOut>", self._on_popup_focusout)

        self._autocomplete_list.delete(0, "end")
        self._autocomplete_data = rows
        for row in rows:
            self._autocomplete_list.insert("end", row["Party"])

        self.update_idletasks()
        x = self._party_entry.winfo_rootx()
        y = self._party_entry.winfo_rooty() + self._party_entry.winfo_height()
        w = self._party_entry.winfo_width()
        h = min(250, 28 * len(rows) + 5)
        self._autocomplete_popup.wm_geometry(f"{w}x{h}+{x}+{y}")
        self._autocomplete_popup.lift()

    def _on_party_focusout(self, _event: Any) -> None:
        self.after(100, self._check_focus_and_close)

    def _on_gst_keyrelease(self, _event: Any) -> None:
        """Trigger reverse GST lookup once 15 chars entered (full GST length)."""
        gstno = normalize_gstno(self._gstno.get())
        if self._gstno.get().strip() != gstno:
            self._gstno.set(gstno)
        if len(gstno) >= 15:
            self._reverse_gst_lookup(gstno)
        # Recompute tax mode immediately while typing GST.
        self._calc_totals()

    def _on_gst_focusout(self, _event: Any) -> None:
        """
        On leaving GST field:
        1. Attempt reverse lookup → fill name + address if found.
        2. Recalculate tax to reflect intra/inter-state mode.
        Customer persistence happens ONLY on Save/Update button click.
        """
        gstno = normalize_gstno(self._gstno.get())
        self._gstno.set(gstno)
        if len(gstno) >= 6:
            self._reverse_gst_lookup(gstno)
        # Ensure tax is recalculated even if lookup didn't find a party.
        self._calc_totals()

    def _reverse_gst_lookup(self, gstno: str) -> None:
        """
        Look up party by GST number and auto-fill name + address.
        Only fills if party name field is currently empty (don't overwrite
        a name the operator has already typed in manually).
        """
        gstno = normalize_gstno(gstno)
        if not gstno:
            return
        row = db.lookup_party_by_gst(self.app.db, gstno)
        if row:
            # Only auto-fill if name field is empty or matches existing
            current_name = self._pname.get().strip()
            if not current_name or current_name == (row["Party"] or ""):
                self._pname.set(row["Party"] or "")
                self._padd.set(row["sub"] or "")
            self._gstno.set(normalize_gstno(row["GSTNO"] or gstno))
            self._calc_totals()
            return

        # External fallback hook (if provider is configured in future).
        ext = db.lookup_party_by_gst_external(gstno)
        if ext:
            party = (ext.get("party") or "").strip()
            addr = (ext.get("address") or "").strip()
            gst_ext = normalize_gstno(ext.get("gstno") or gstno)
            if party:
                self._pname.set(party)
            if addr:
                self._padd.set(addr)
            self._gstno.set(gst_ext)
            self._calc_totals()

    def _save_customer(self) -> None:
        """Explicitly save current customer details into local ledger master."""
        pname = self._pname.get().strip()
        if len(pname) < 2:
            messagebox.showwarning("Required", "Enter customer name.", parent=self)
            return
        gstno = normalize_gstno(self._gstno.get())
        if gstno and len(gstno) != 15:
            messagebox.showwarning(
                "Invalid GST",
                "GST number must be 15 characters (or leave blank).",
                parent=self,
            )
            return
        padd = self._padd.get().strip()
        db.upsert_party(self.app.db, pname, padd, gstno)
        self._gstno.set(gstno)
        messagebox.showinfo(
            "Saved",
            f"Customer '{pname}' saved to ledger master.",
            parent=self,
        )

    def _calc_row(self, rv: dict[str, tk.StringVar]) -> None:
        r = to_float(rv["rate"].get())
        q = to_float(rv["qty"].get()) or 1
        amt = round(r * q, 2)
        rv["amt"].set(fmt_amt(amt) if amt else "")
        self._calc_totals()

    def _calc_totals(self) -> None:
        taxable = sum(to_float(rv["amt"].get()) for rv in self._grid_vars)
        gst_pct = to_float(self._gst_pct.get()) or 18.0
        result  = calc_gst(taxable, gst_pct, self._gstno.get())
        self._tamt.set(fmt_amt(result["taxable"]))
        self._cgst_v.set(fmt_amt(result["cgst"]))
        self._sgst_v.set(fmt_amt(result["sgst"]))
        self._igst_v.set(fmt_amt(result["igst"]))
        self._total.set(fmt_amt(result["total"]))
        self._update_totals_grid()

    def _collect_rows(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i, rv in enumerate(self._grid_vars):
            part = rv["part"].get().strip()
            if not part:
                continue
            out.append({
                "slno":  i + 1,
                "part":  part,
                "od":    int(to_float(rv["od"].get())),
                "guage": int(to_float(rv["mic"].get())),
                "qty":   max(1, int(to_float(rv["qty"].get()))),
                "rate":  to_float(rv["rate"].get()),
                "AMT":   to_float(rv["amt"].get()),
            })
        return out

    def _build_header_dict(self) -> dict[str, Any]:
        return {
            "inwno":   self._no_var.get().strip(),
            "inwdate": parse_date(self._date_var.get()),
            "pname":   self._pname.get().strip(),
            "padd":    self._padd.get().strip(),
            "PGSTNO":  normalize_gstno(self._gstno.get()),
            "ref":     self._ref.get().strip(),
            "SUB":     self._sub.get().strip(),
            "TAMT":    to_float(self._tamt.get()),
            "CGST":    to_float(self._cgst_v.get()),
            "SGST":    to_float(self._sgst_v.get()),
            "IGST":    to_float(self._igst_v.get()),
            "NETAMT":  to_float(self._total.get()),
        }

    def _new_record(self) -> None:
        nxt = db.next_no(self.app.db, self.AUTO_FIELD)
        self._no_var.set(str(nxt))
        self._date_var.set(today_str())
        self._pname.set("")
        self._padd.set("")
        self._gstno.set("")
        self._sub.set("Hard Chrome Plating and Diamond Polishing")
        self._ref.set("")
        self._extra1.set("")
        self._extra2.set("")
        for rv in self._grid_vars:
            rv["part"].set("")
            rv["od"].set("")
            rv["mic"].set("")
            rv["rate"].set("")
            rv["qty"].set("1")
            rv["amt"].set("")
        for var in (self._tamt, self._cgst_v, self._sgst_v,
                    self._igst_v, self._total):
            var.set("0.00")
        self._reset_extra_fields()

    def _reset_extra_fields(self) -> None:
        """Subclasses reset their extra fields here."""

    def _save(self) -> None:
        rows = self._collect_rows()
        if not rows:
            messagebox.showwarning("Empty",
                                   "Enter at least one line item.", parent=self)
            return
        inwno = self._no_var.get().strip()
        if not inwno:
            messagebox.showwarning("No number",
                                   "Document number is missing.", parent=self)
            return

        # Check duplicate
        existing = db.load_doc(self.app.db, self.TABLE, inwno)
        if existing:
            if not messagebox.askyesno(
                    "Duplicate", f"No. {inwno} already exists. Overwrite?",
                    parent=self):
                return
            db.delete_doc(self.app.db, self.TABLE, inwno)

        header = self._build_header_dict()
        header.update(self._extra_header_fields())
        db.save_rows(self.app.db, self.TABLE, header, rows)
        db.upsert_party(self.app.db, header["pname"],
                        header["padd"], header["PGSTNO"])
        db.advance_no(self.app.db, self.AUTO_FIELD, int(inwno))
        self._fy_no.set(f"FY No. {inwno}")
        messagebox.showinfo("Saved",
                            f"Record {inwno} saved successfully.", parent=self)

    def _extra_header_fields(self) -> dict[str, Any]:
        return {}

    def _update(self) -> None:
        rows = self._collect_rows()
        if not rows:
            messagebox.showwarning("Empty", "Nothing to update.", parent=self)
            return
        inwno = self._no_var.get().strip()
        db.delete_doc(self.app.db, self.TABLE, inwno)
        header = self._build_header_dict()
        header.update(self._extra_header_fields())
        db.save_rows(self.app.db, self.TABLE, header, rows)
        db.upsert_party(self.app.db, header["pname"],
                        header["padd"], header["PGSTNO"])
        messagebox.showinfo("Updated",
                            f"Record {inwno} updated.", parent=self)

    def _load(self) -> None:
        num = simpledialog.askstring("InvSDP", f"Enter the {self.NO_LBL}", parent=self)
        if not num:
            return
        num = num.strip()
        rows = db.load_doc(self.app.db, self.TABLE, num)
        if not rows:
            messagebox.showwarning("Not Found", f"{self.TABLE} No. {num} not found or not saved.", parent=self)
            return
        self._fill_from_rows(rows)

    def _fill_from_rows(self, rows: list[sqlite3.Row]) -> None:
        if not rows:
            return
        r0 = rows[0]
        self._no_var.set(str(r0["inwno"]))
        self._fy_no.set(f"FY No. {r0['inwno']}")
        self._date_var.set(r0["inwdate"])
        self._pname.set(r0["pname"] or "")
        self._padd.set(r0["padd"] or "")
        self._gstno.set(normalize_gstno(r0["PGSTNO"] or ""))
        self._sub.set(r0["SUB"] or "")
        self._ref.set(r0["ref"] or "")
        self._tamt.set(fmt_amt(to_float(r0["TAMT"])))
        self._cgst_v.set(fmt_amt(to_float(r0["CGST"])))
        self._sgst_v.set(fmt_amt(to_float(r0["SGST"])))
        self._igst_v.set(fmt_amt(to_float(r0["IGST"])))
        self._total.set(fmt_amt(to_float(r0["NETAMT"])))
        for rv in self._grid_vars:
            for k in ("part", "od", "mic", "rate", "qty", "amt"):
                rv[k].set("")
            rv["qty"].set("1")
        for i, row in enumerate(rows[:self.N_ROWS]):
            rv = self._grid_vars[i]
            rv["part"].set(str(row["part"]))
            rv["od"].set(str(row["od"]) if row["od"] else "")
            rv["mic"].set(str(row["guage"]) if row["guage"] else "")
            rv["rate"].set(fmt_amt(to_float(row["rate"])))
            rv["qty"].set(str(row["qty"]))
            rv["amt"].set(fmt_amt(to_float(row["AMT"])))
        self._fill_extra_fields(r0)
        self._calc_totals()

    def _fill_extra_fields(self, row: sqlite3.Row) -> None:
        """Subclasses fill their extra fields from loaded row."""

    def _delete(self) -> None:
        inwno = self._no_var.get().strip()
        if not inwno:
            return
        if messagebox.askyesno("Delete",
                                f"Delete record {inwno}?", parent=self):
            n = db.delete_doc(self.app.db, self.TABLE, inwno)
            messagebox.showinfo("Deleted",
                                f"{n} rows deleted.", parent=self)
            self._new_record()

    def _get_print_data(self) -> dict[str, Any]:
        return {
            "no":    self._no_var.get(),
            "date":  self._date_var.get(),
            "pname": self._pname.get(),
            "padd":  self._padd.get(),
            "gstno": self._gstno.get(),
            "sub":   self._sub.get(),
            "ref":   self._ref.get(),
            "rows":  self._collect_rows(),
            "tamt":  to_float(self._tamt.get()),
            "cgst":  to_float(self._cgst_v.get()),
            "sgst":  to_float(self._sgst_v.get()),
            "igst":  to_float(self._igst_v.get()),
            "total": to_float(self._total.get()),
        }

    def _print(self) -> None:
        messagebox.showinfo("Print", "Use the specific print button.", parent=self)

    def _email(self) -> None:
        messagebox.showinfo("Email",
                            "Configure email in Others > Settings.", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Concrete entry forms
# ─────────────────────────────────────────────────────────────────────────────

class QuotationForm(EntryFormBase):
    TITLE      = "Adhwaitha Sri Plating — Quotation"
    TABLE      = "Quotation"
    AUTO_FIELD = "Quo"
    NO_LBL     = "Quotation No."

    def _buttons(self):
        return [
            ("&New",               self._new_record,    BTN_BG),
            ("&Save",              self._save,          "#90EE90"),
            ("Print Quotation",    self._print_quot,    BTN_BG),
            ("Print Proforma Invoice", self._print_proforma, BTN_BG),
            ("Load Quotation",     self._load,          BTN_BG),
            ("&Update",            self._update,        BTN_BG),
            ("&Delete",            self._delete,        "#FFB6C1"),
            ("Email",              self._email,         BTN_BG),
            ("&Close",             self.destroy,        BTN_BG),
        ]

    def _print_proforma(self) -> None:
        path = pr.print_proforma(self._get_print_data(),
                                  db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved: {path}", parent=self)

    def _print_quot(self) -> None:
        path = pr.print_quotation(self._get_print_data(),
                                   db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved: {path}", parent=self)

    def _print(self) -> None:
        self._print_proforma()


class DCForm(EntryFormBase):
    TITLE      = "Adhwaitha Sri Plating — Delivery Challan"
    TABLE      = "DC"
    AUTO_FIELD = "DC"
    NO_LBL     = "DC No."
    SEPARATE_DATE_ROW = True

    def _build_extra_header(self, parent: tk.Frame) -> None:
        self._goods_value = tk.StringVar()
        self._inward_ref_num = ""
        self._inward_ref_date = ""
        ro = self._hdr_row_offset + 4
        lbl(parent, "Your D.Slip. No.").grid(row=ro, column=0, sticky="e", padx=3, pady=2)
        ent(parent, self._goods_value, width=40).grid(row=ro, column=1, columnspan=5,
                                                       sticky="w", padx=3)

    def _extra_header_fields(self) -> dict[str, Any]:
        return {
            "GOODS_VALUE": self._goods_value.get().strip(),
            "sdidcno":     getattr(self, "_inward_ref_num", ""),
            "sdidt":       getattr(self, "_inward_ref_date", ""),
        }

    def _reset_extra_fields(self) -> None:
        self._goods_value.set("")
        self._inward_ref_num = ""
        self._inward_ref_date = ""

    def _fill_extra_fields(self, row: sqlite3.Row) -> None:
        try:
            self._goods_value.set(row["GOODS_VALUE"] or "")
        except (IndexError, KeyError):
            pass
        try:
            self._inward_ref_num = row["sdidcno"] or ""
            self._inward_ref_date = row["sdidt"] or ""
        except (IndexError, KeyError):
            self._inward_ref_num = ""
            self._inward_ref_date = ""

    def _buttons(self):
        return [
            ("&New",               self._new_record,    BTN_BG),
            ("Load Inward",        self._load_inward,   BTN_BG),
            ("Load DC",            self._load,          BTN_BG),
            ("&Save",              self._save,          "#90EE90"),
            ("Print DC",           self._print_dc,      BTN_BG),
            ("&Delete",            self._delete,        "#FFB6C1"),
            ("Email",              self._email,         BTN_BG),
            ("&Close",             self.destroy,        BTN_BG),
        ]

    def _load_inward(self) -> None:
        num = simpledialog.askstring("InvSDP", "Enter the Item Inward No.", parent=self)
        if not num:
            return
        num = num.strip()
        rows = db.load_doc(self.app.db, "ItemInward", num)
        if not rows:
            messagebox.showwarning("Not Found", f"Inward No. {num} not found.", parent=self)
            return

        self._pname.set(rows[0]["pname"] or "")
        self._padd.set(rows[0]["padd"] or "")
        self._gstno.set(normalize_gstno(rows[0]["PGSTNO"] or ""))
        self._sub.set(rows[0]["SUB"] or "")
        self._ref.set(f"Inw Ref: {num}")
        self._inward_ref_num = num
        self._inward_ref_date = rows[0]["inwdate"] or ""

        for rv in self._grid_vars:
            for k in ("part", "od", "mic", "rate", "qty", "amt"):
                rv[k].set("")
            rv["qty"].set("1")

        for i, row in enumerate(rows[:self.N_ROWS]):
            rv = self._grid_vars[i]
            rv["part"].set(str(row["part"]))
            rv["od"].set(str(row["od"]) if row["od"] else "")
            rv["mic"].set(str(row["guage"]) if row["guage"] else "")
            rv["rate"].set("")
            rv["qty"].set(str(row["qty"]))
            rv["amt"].set("")

        self._calc_totals()
        messagebox.showinfo("Loaded", f"Inward {num} loaded (non-financial).", parent=self)

    def _print_dc(self) -> None:
        d = self._get_print_data()
        d["goods_value"] = self._goods_value.get().strip()
        path = pr.print_dc(d, db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved: {path}", parent=self)

    def _print(self) -> None:
        self._print_dc()


class BillForm(EntryFormBase):
    TITLE      = "Adhwaitha Sri Plating — Cash / Credit Bill"
    TABLE      = "BILL"
    AUTO_FIELD = "BILL"
    NO_LBL     = "Bill No."

    def _build_extra_header(self, parent: tk.Frame) -> None:
        self._pdc   = tk.StringVar()
        self._sdpdc = tk.StringVar()
        self._inward_ref_num = ""
        self._inward_ref_date = ""
        lbl(parent, "PDC").grid(row=self._hdr_row_offset + 4, column=0, sticky="e", padx=3, pady=2)
        ent(parent, self._pdc, width=30).grid(row=self._hdr_row_offset + 4, column=1, columnspan=4,
                                               sticky="w", padx=3)
        lbl(parent, "ASP D.C.No.").grid(row=self._hdr_row_offset + 4, column=5, sticky="e", padx=3)
        ent(parent, self._sdpdc, width=24).grid(row=self._hdr_row_offset + 4, column=6, columnspan=3,
                                                 sticky="w", padx=3)

    def _extra_header_fields(self) -> dict[str, Any]:
        return {
            "PDC":     self._pdc.get().strip(),
            "SDPDC":   self._sdpdc.get().strip(),
            "sdidcno": getattr(self, "_inward_ref_num", ""),
            "sdidt":   getattr(self, "_inward_ref_date", ""),
        }

    def _reset_extra_fields(self) -> None:
        self._pdc.set("")
        self._sdpdc.set("")
        self._inward_ref_num = ""
        self._inward_ref_date = ""

    def _fill_extra_fields(self, row: sqlite3.Row) -> None:
        try:
            self._pdc.set(row["PDC"] or "")
            self._sdpdc.set(row["SDPDC"] or "")
        except (IndexError, KeyError):
            pass
        try:
            self._inward_ref_num = row["sdidcno"] or ""
            self._inward_ref_date = row["sdidt"] or ""
        except (IndexError, KeyError):
            self._inward_ref_num = ""
            self._inward_ref_date = ""

    def _buttons(self):
        return [
            ("&New",               self._new_record,    BTN_BG),
            ("Load DC",            self._load_dc,       BTN_BG),
            ("Load Proforma Invoice", self._load_proforma_invoice, BTN_BG),
            ("&Save",              self._save,          "#90EE90"),
            ("Print Bill",         self._print_bill,    BTN_BG),
            ("Load Bill",          self._load,          BTN_BG),
            ("&Update",            self._update,        BTN_BG),
            ("&Delete",            self._delete,        "#FFB6C1"),
            ("Email",              self._email,         BTN_BG),
            ("&Close",             self.destroy,        BTN_BG),
        ]

    def _load_dc(self) -> None:
        num = simpledialog.askstring("InvSDP", "Enter the D.C No.", parent=self)
        if not num:
            return
        num = num.strip()
        dc_rows = db.load_doc(self.app.db, "DC", num)
        if not dc_rows:
            messagebox.showwarning("Not Found", f"DC No. {num} not found.", parent=self)
            return

        r0 = dc_rows[0]
        self._pname.set(r0["pname"] or "")
        self._padd.set(r0["padd"] or "")
        self._gstno.set(normalize_gstno(r0["PGSTNO"] or ""))
        self._sub.set(r0["SUB"] or "")
        self._ref.set(f"DC Ref: {num}")

        if hasattr(self, "_sdpdc"):
            self._sdpdc.set(num)

        inward_no = r0.get("sdidcno", "")
        self._inward_ref_num = inward_no
        self._inward_ref_date = r0.get("sdidt", "")
        inw_rates = {}
        if inward_no:
            inw_rows = db.load_doc(self.app.db, "ItemInward", inward_no)
            for row in inw_rows:
                part = row["part"].strip()
                inw_rates[part] = {
                    "rate": to_float(row["rate"]),
                    "mic": str(row["guage"]) if row["guage"] else "",
                    "od": str(row["od"]) if row["od"] else "",
                }

        for rv in self._grid_vars:
            for k in ("part", "od", "mic", "rate", "qty", "amt"):
                rv[k].set("")
            rv["qty"].set("1")

        for i, row in enumerate(dc_rows[:self.N_ROWS]):
            rv = self._grid_vars[i]
            part = str(row["part"])
            rv["part"].set(part)
            rv["qty"].set(str(row["qty"]))

            part_key = part.strip()
            if part_key in inw_rates:
                rv["rate"].set(fmt_amt(inw_rates[part_key]["rate"]))
                rv["mic"].set(inw_rates[part_key]["mic"])
                rv["od"].set(inw_rates[part_key]["od"])
            else:
                rv["rate"].set(fmt_amt(to_float(row.get("rate", 0))) if to_float(row.get("rate", 0)) else "")
                rv["mic"].set(str(row.get("guage", "")) if row.get("guage") else "")
                rv["od"].set(str(row.get("od", "")) if row.get("od") else "")

            r = to_float(rv["rate"].get())
            q = to_float(rv["qty"].get()) or 1
            amt = round(r * q, 2)
            rv["amt"].set(fmt_amt(amt) if amt else "")

        self._calc_totals()
        messagebox.showinfo("Loaded", f"DC {num} loaded successfully.", parent=self)

    def _load_proforma_invoice(self) -> None:
        num = simpledialog.askstring("InvSDP", "Enter the Quotation No.", parent=self)
        if not num:
            return
        num = num.strip()
        rows = db.load_doc(self.app.db, "Quotation", num)
        if not rows:
            messagebox.showwarning("Not Found", f"Proforma / Quotation No. {num} not found.", parent=self)
            return

        r0 = rows[0]
        self._pname.set(r0["pname"] or "")
        self._padd.set(r0["padd"] or "")
        self._gstno.set(normalize_gstno(r0["PGSTNO"] or ""))
        self._sub.set(r0["SUB"] or "")
        self._ref.set(f"PF Ref: {num}")
        self._inward_ref_num = num
        self._inward_ref_date = r0["inwdate"] or ""

        for rv in self._grid_vars:
            for k in ("part", "od", "mic", "rate", "qty", "amt"):
                rv[k].set("")
            rv["qty"].set("1")

        for i, row in enumerate(rows[:self.N_ROWS]):
            rv = self._grid_vars[i]
            rv["part"].set(str(row["part"]))
            rv["od"].set(str(row["od"]) if row["od"] else "")
            rv["mic"].set(str(row["guage"]) if row["guage"] else "")
            rv["rate"].set(fmt_amt(to_float(row["rate"])))
            rv["qty"].set(str(row["qty"]))
            rv["amt"].set(fmt_amt(to_float(row["AMT"])))

        self._calc_totals()
        messagebox.showinfo("Loaded", f"Proforma Invoice {num} loaded successfully.", parent=self)

    def _print_bill(self) -> None:
        d = self._get_print_data()
        d["sdpdc"] = self._sdpdc.get()
        path = pr.print_job_work_bill(d, db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved: {path}", parent=self)

    def _print_pf(self) -> None:
        path = pr.print_proforma(self._get_print_data(),
                                  db.REPORTS_DIR, open_pdf=True)
        messagebox.showinfo("PDF", f"Saved: {path}", parent=self)

    def _print(self) -> None:
        self._print_bill()


class ItemInwardForm(EntryFormBase):
    TITLE      = "Adhwaitha Sri Plating — Goods Inward Receipt"
    TABLE      = "ItemInward"
    AUTO_FIELD = "ItemInw"
    NO_LBL     = "Inward No."

    def _build_extra_header(self, parent: tk.Frame) -> None:
        self._pdc = tk.StringVar()
        lbl(parent, "Your D.Slip. No.").grid(row=self._hdr_row_offset + 4, column=0, sticky="e", padx=3, pady=2)
        ent(parent, self._pdc, width=40).grid(row=self._hdr_row_offset + 4, column=1, columnspan=5,
                                               sticky="w", padx=3)

    def _extra_header_fields(self) -> dict[str, Any]:
        return {
            "PDC":     self._pdc.get().strip(),
            "sdidcno": getattr(self, "_quot_ref_num", ""),
            "sdidt":   getattr(self, "_quot_ref_date", ""),
        }

    def _reset_extra_fields(self) -> None:
        self._pdc.set("")
        self._quot_ref_num = ""
        self._quot_ref_date = ""

    def _fill_extra_fields(self, row: sqlite3.Row) -> None:
        try:
            self._pdc.set(row["PDC"] or "")
        except (IndexError, KeyError):
            pass
        try:
            self._quot_ref_num = row["sdidcno"] or ""
            self._quot_ref_date = row["sdidt"] or ""
        except (IndexError, KeyError):
            self._quot_ref_num = ""
            self._quot_ref_date = ""

    def _buttons(self):
        return [
            ("New/Cancel",         self._new_record,    BTN_BG),
            ("Load Quotation",     self._load_quotation, BTN_BG),
            ("Load Inward",        self._load,          BTN_BG),
            ("&Save",              self._save,          "#90EE90"),
            ("&Update",            self._update,        BTN_BG),
            ("&Delete",            self._delete,        "#FFB6C1"),
            ("&Close",             self.destroy,        BTN_BG),
        ]

    def _load_quotation(self) -> None:
        num = simpledialog.askstring("InvSDP", "Enter the Quotation No.", parent=self)
        if not num:
            return
        num = num.strip()
        rows = db.load_doc(self.app.db, "Quotation", num)
        if not rows:
            messagebox.showwarning("Not Found", f"Quotation No. {num} not found.", parent=self)
            return

        self._pname.set(rows[0]["pname"] or "")
        self._padd.set(rows[0]["padd"] or "")
        self._gstno.set(normalize_gstno(rows[0]["PGSTNO"] or ""))
        self._sub.set(rows[0]["SUB"] or "")
        self._ref.set(f"Quot Ref: {num}")
        self._quot_ref_num = num
        self._quot_ref_date = rows[0]["inwdate"] or ""

        for rv in self._grid_vars:
            for k in ("part", "od", "mic", "rate", "qty", "amt"):
                rv[k].set("")
            rv["qty"].set("1")

        for i, row in enumerate(rows[:self.N_ROWS]):
            rv = self._grid_vars[i]
            rv["part"].set(str(row["part"]))
            rv["od"].set(str(row["od"]) if row["od"] else "")
            rv["mic"].set(str(row["guage"]) if row["guage"] else "")
            rv["rate"].set(fmt_amt(to_float(row["rate"])))
            rv["qty"].set(str(row["qty"]))
            rv["amt"].set(fmt_amt(to_float(row["AMT"])))

        self._calc_totals()
        messagebox.showinfo("Loaded", f"Quotation {num} loaded successfully.", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Ledger Creation (Party Master)
# ─────────────────────────────────────────────────────────────────────────────

class LedgerCreationForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Ledger Creation")
        self.geometry("660x520+110+70")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Ledger Creation — Party Master",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=8)
        lbl(ef, "A/c Name").grid(row=0, column=0, sticky="e", padx=5)
        self._name = tk.StringVar()
        ent(ef, self._name, width=38).grid(row=0, column=1, padx=4, pady=3)
        lbl(ef, "Address").grid(row=1, column=0, sticky="e", padx=5)
        self._add = tk.StringVar()
        ent(ef, self._add, width=38).grid(row=1, column=1, padx=4, pady=3)
        lbl(ef, "GST No.").grid(row=2, column=0, sticky="e", padx=5)
        self._gst = tk.StringVar()
        ent(ef, self._gst, width=22).grid(row=2, column=1, padx=4, pady=3, sticky="w")

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=3, column=0, columnspan=2, pady=8)
        btn(bf, "Save",   self._save,   width=8).pack(side="left", padx=5)
        btn(bf, "Delete", self._delete, width=8).pack(side="left", padx=5)
        btn(bf, "Clear",  self._clear,  width=8).pack(side="left", padx=5)
        btn(bf, "Close",  self.destroy, width=8).pack(side="left", padx=5)

        cols = ("Party", "Address", "GST No.")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c, w in zip(cols, [220, 250, 130]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
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
        name = self._name.get().strip()
        if not name:
            messagebox.showwarning("Required", "A/c Name is required.", parent=self)
            return
        db.upsert_party(self.app.db, name,
                        self._add.get().strip(), self._gst.get().strip())
        self._refresh()

    def _delete(self) -> None:
        name = self._name.get().strip()
        if not name:
            return
        if messagebox.askyesno("Delete", f"Delete '{name}'?", parent=self):
            self.app.db.execute("DELETE FROM HD WHERE Party=?", (name,))
            self.app.db.commit()
            self._clear()
            self._refresh()

    def _clear(self) -> None:
        self._name.set("")
        self._add.set("")
        self._gst.set("")


# ─────────────────────────────────────────────────────────────────────────────
#  Purchase Entry
# ─────────────────────────────────────────────────────────────────────────────

class PurchaseForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Purchase Entry")
        self.geometry("680x500+110+70")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Purchase Entry",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)

        self._vars: dict[str, tk.StringVar] = {
            "_dt":    tk.StringVar(value=today_str()),
            "_pfrom": tk.StringVar(),
            "_padd":  tk.StringVar(),
            "_pname": tk.StringVar(),
            "_qty":   tk.StringVar(value="1"),
            "_amt":   tk.StringVar(),
        }
        labels = [
            ("Date",          "_dt",    12),
            ("Purchased From","_pfrom", 32),
            ("Address",       "_padd",  32),
            ("Item Name",     "_pname", 32),
            ("Qty",           "_qty",   8),
            ("Amount",        "_amt",   12),
        ]
        for i, (lbl_t, attr, w) in enumerate(labels):
            lbl(ef, lbl_t).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ent(ef, self._vars[attr], width=w).grid(row=i, column=1,
                                                     sticky="w", padx=4, pady=2)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=len(labels), column=0, columnspan=2, pady=8)
        btn(bf, "Save",   self._save,   width=8).pack(side="left", padx=5)
        btn(bf, "Delete", self._delete, width=8).pack(side="left", padx=5)
        btn(bf, "Clear",  self._clear,  width=8).pack(side="left", padx=5)
        btn(bf, "Close",  self.destroy, width=8).pack(side="left", padx=5)

        cols = ("Date", "From", "Item", "Qty", "Amount")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=10)
        for c, w in zip(cols, [90, 160, 180, 50, 90]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)
        self._sel_id: Optional[int] = None

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        rows = self.app.db.execute(
            "SELECT id,pdt,pfrom,pname,qty,amt FROM purchase "
            "ORDER BY id DESC LIMIT 300"
        ).fetchall()
        for r in rows:
            self.tv.insert("", "end", iid=str(r["id"]),
                           values=(r["pdt"], r["pfrom"], r["pname"],
                                   r["qty"], fmt_amt(to_float(r["amt"]))))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if not sel:
            return
        self._sel_id = int(sel[0])
        row = self.app.db.execute(
            "SELECT * FROM purchase WHERE id=?", (self._sel_id,)
        ).fetchone()
        if row:
            self._vars["_dt"].set(row["pdt"])
            self._vars["_pfrom"].set(row["pfrom"] or "")
            self._vars["_padd"].set(row["padd"] or "")
            self._vars["_pname"].set(row["pname"] or "")
            self._vars["_qty"].set(str(row["qty"]))
            self._vars["_amt"].set(fmt_amt(to_float(row["amt"])))

    def _save(self) -> None:
        pname = self._vars["_pname"].get().strip()
        if not pname:
            messagebox.showwarning("Required", "Item Name is required.", parent=self)
            return
        self.app.db.execute(
            "INSERT INTO purchase(pdt,pfrom,padd,pname,qty,amt) VALUES (?,?,?,?,?,?)",
            (parse_date(self._vars["_dt"].get()),
             self._vars["_pfrom"].get().strip(),
             self._vars["_padd"].get().strip(),
             pname,
             max(1, int(to_float(self._vars["_qty"].get()))),
             to_float(self._vars["_amt"].get()))
        )
        self.app.db.commit()
        self._clear()
        self._refresh()

    def _delete(self) -> None:
        if self._sel_id is None:
            return
        if messagebox.askyesno("Delete", "Delete this purchase entry?", parent=self):
            self.app.db.execute("DELETE FROM purchase WHERE id=?", (self._sel_id,))
            self.app.db.commit()
            self._sel_id = None
            self._clear()
            self._refresh()

    def _clear(self) -> None:
        self._sel_id = None
        self._vars["_dt"].set(today_str())
        for k in ("_pfrom", "_padd", "_pname", "_amt"):
            self._vars[k].set("")
        self._vars["_qty"].set("1")


# ─────────────────────────────────────────────────────────────────────────────
#  Purchase Order
# ─────────────────────────────────────────────────────────────────────────────

class POForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Adhwaitha Sri Plating — Purchase Order")
        self.geometry("760x520+90+60")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Purchase Order",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)

        self._pono   = tk.StringVar()
        self._podate = tk.StringVar(value=today_str())
        self._pfrom  = tk.StringVar()
        self._padd   = tk.StringVar()
        self._part   = tk.StringVar()
        self._qty    = tk.StringVar(value="1")
        self._rate   = tk.StringVar()
        self._ref    = tk.StringVar()

        fields = [
            ("PO No.",    self._pono,   8),
            ("Date",      self._podate, 12),
            ("Vendor",    self._pfrom,  36),
            ("Address",   self._padd,   36),
            ("Item/Part", self._part,   36),
            ("Qty",       self._qty,    8),
            ("Rate",      self._rate,   12),
            ("Ref",       self._ref,    36),
        ]
        for i, (lbl_t, var, w) in enumerate(fields):
            lbl(ef, lbl_t).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ent(ef, var, width=w).grid(row=i, column=1, sticky="w", padx=4, pady=2)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=len(fields), column=0, columnspan=2, pady=8)
        btn(bf, "New",    self._new_record, width=8).pack(side="left", padx=4)
        btn(bf, "Save",   self._save,       width=8, bg="#90EE90").pack(side="left", padx=4)
        btn(bf, "Print",  self._print_po,   width=8).pack(side="left", padx=4)
        btn(bf, "Delete", self._delete,     width=8, bg="#FFB6C1").pack(side="left", padx=4)
        btn(bf, "Close",  self.destroy,     width=8).pack(side="left", padx=4)

        cols = ("PO No.", "Date", "Vendor", "Item", "Qty", "Rate")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c, w in zip(cols, [60, 80, 180, 180, 50, 80]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)
        self._sel_id: Optional[int] = None

    def _new_record(self) -> None:
        nxt = db.next_no(self.app.db, "PO")
        self._pono.set(str(nxt))
        self._podate.set(today_str())
        for v in (self._pfrom, self._padd, self._part, self._ref, self._rate):
            v.set("")
        self._qty.set("1")
        self._sel_id = None

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        rows = self.app.db.execute(
            "SELECT id,pono,podate,pname,part,qty,rate FROM PO "
            "ORDER BY id DESC LIMIT 300"
        ).fetchall()
        for r in rows:
            self.tv.insert("", "end", iid=str(r["id"]),
                           values=(r["pono"], r["podate"], r["pname"],
                                   r["part"], r["qty"],
                                   fmt_amt(to_float(r["rate"]))))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if not sel:
            return
        self._sel_id = int(sel[0])
        row = self.app.db.execute(
            "SELECT * FROM PO WHERE id=?", (self._sel_id,)
        ).fetchone()
        if row:
            self._pono.set(row["pono"])
            self._podate.set(row["podate"])
            self._pfrom.set(row["pname"] or "")
            self._padd.set(row["padd"] or "")
            self._part.set(row["part"] or "")
            self._qty.set(str(row["qty"]))
            self._rate.set(fmt_amt(to_float(row["rate"])))
            self._ref.set(row["ref"] or "")

    def _save(self) -> None:
        pono = self._pono.get().strip()
        if not pono:
            messagebox.showwarning("Required", "PO No. required.", parent=self)
            return
        qty  = max(1, int(to_float(self._qty.get())))
        rate = to_float(self._rate.get())
        netamt = round(qty * rate, 2)
        self.app.db.execute(
            "INSERT OR REPLACE INTO PO(pono,podate,pname,padd,part,qty,rate,ref,netamt) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (pono, parse_date(self._podate.get()),
             self._pfrom.get().strip(), self._padd.get().strip(),
             self._part.get().strip(), qty, rate,
             self._ref.get().strip(), netamt)
        )
        self.app.db.commit()
        db.advance_no(self.app.db, "PO", int(pono))
        self._refresh()

    def _delete(self) -> None:
        if self._sel_id is None:
            return
        if messagebox.askyesno("Delete", "Delete this PO?", parent=self):
            self.app.db.execute("DELETE FROM PO WHERE id=?", (self._sel_id,))
            self.app.db.commit()
            self._sel_id = None
            self._new_record()
            self._refresh()

    def _print_po(self) -> None:
        qty  = to_float(self._qty.get())
        rate = to_float(self._rate.get())
        data = {
            "no":    self._pono.get(),
            "date":  self._podate.get(),
            "pname": self._pfrom.get(),
            "padd":  self._padd.get(),
            "gstno": "",
            "sub":   self._ref.get(),
            "ref":   "",
            "rows":  [{"part": self._part.get(), "od": 0,
                        "rate": rate, "qty": qty, "AMT": qty * rate}],
            "tamt":  qty * rate,
            "cgst":  0.0, "sgst": 0.0, "igst": 0.0,
            "total": qty * rate,
        }
        path = pr.print_purchase_order(data, db.REPORTS_DIR)
        messagebox.showinfo("PDF", f"Saved: {path}", parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Cheque Payment Details
# ─────────────────────────────────────────────────────────────────────────────

class ChequePayForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Cheque Payment Details")
        self.geometry("740x530+90+60")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Cheque Payment Details",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)

        self._pname  = tk.StringVar()
        self._bank   = tk.StringVar()
        self._cno    = tk.StringVar()
        self._cdate  = tk.StringVar(value=today_str())
        self._camt   = tk.StringVar()
        self._billno = tk.StringVar()
        self._bdate  = tk.StringVar(value=today_str())
        self._bamt   = tk.StringVar()
        self._paid   = tk.StringVar()

        fields = [
            ("Party Name",    self._pname,  36),
            ("Bank Name",     self._bank,   28),
            ("Cheque No.",    self._cno,    16),
            ("Cheque Date",   self._cdate,  12),
            ("Cheque Amount", self._camt,   12),
            ("Bill No.",      self._billno, 10),
            ("Bill Date",     self._bdate,  12),
            ("Bill Amount",   self._bamt,   12),
            ("Amt Paid",      self._paid,   12),
        ]
        for i, (lbl_t, var, w) in enumerate(fields):
            r, c = divmod(i, 2)
            lbl(ef, lbl_t).grid(row=r, column=c*2, sticky="e", padx=5, pady=2)
            ent(ef, var, width=w).grid(row=r, column=c*2+1, sticky="w", padx=4, pady=2)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=(len(fields)//2)+1, column=0, columnspan=4, pady=8)
        btn(bf, "Save",   self._save,   width=8, bg="#90EE90").pack(side="left", padx=4)
        btn(bf, "Delete", self._delete, width=8, bg="#FFB6C1").pack(side="left", padx=4)
        btn(bf, "Clear",  self._clear,  width=8).pack(side="left", padx=4)
        btn(bf, "Close",  self.destroy, width=8).pack(side="left", padx=4)

        cols = ("Party", "Bank", "Chq No.", "Chq Date", "Amount", "Bill No.")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=9)
        for c, w in zip(cols, [160, 120, 80, 80, 80, 70]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)
        self._sel_id: Optional[int] = None

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        rows = self.app.db.execute(
            "SELECT id,pname,bankname,cno,cdate,camt,billno FROM CqPay "
            "ORDER BY id DESC LIMIT 300"
        ).fetchall()
        for r in rows:
            self.tv.insert("", "end", iid=str(r["id"]),
                           values=(r["pname"], r["bankname"], r["cno"],
                                   r["cdate"], fmt_amt(to_float(r["camt"])),
                                   r["billno"]))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if not sel:
            return
        self._sel_id = int(sel[0])
        row = self.app.db.execute(
            "SELECT * FROM CqPay WHERE id=?", (self._sel_id,)
        ).fetchone()
        if row:
            self._pname.set(row["pname"] or "")
            self._bank.set(row["bankname"] or "")
            self._cno.set(row["cno"] or "")
            self._cdate.set(row["cdate"] or "")
            self._camt.set(fmt_amt(to_float(row["camt"])))
            self._billno.set(row["billno"] or "")
            self._bdate.set(row["billdate"] or "")
            self._bamt.set(fmt_amt(to_float(row["billamt"])))
            self._paid.set(fmt_amt(to_float(row["amtpaid"])))

    def _save(self) -> None:
        pname = self._pname.get().strip()
        if not pname:
            messagebox.showwarning("Required", "Party Name required.", parent=self)
            return
        self.app.db.execute(
            "INSERT INTO CqPay(pname,bankname,cno,cdate,camt,"
            "billno,billdate,billamt,amtpaid) VALUES (?,?,?,?,?,?,?,?,?)",
            (pname, self._bank.get(), self._cno.get(),
             parse_date(self._cdate.get()), to_float(self._camt.get()),
             self._billno.get(), parse_date(self._bdate.get()),
             to_float(self._bamt.get()), to_float(self._paid.get()))
        )
        self.app.db.commit()
        self._clear()
        self._refresh()

    def _delete(self) -> None:
        if self._sel_id is None:
            return
        if messagebox.askyesno("Delete", "Delete this entry?", parent=self):
            self.app.db.execute("DELETE FROM CqPay WHERE id=?", (self._sel_id,))
            self.app.db.commit()
            self._sel_id = None
            self._clear()
            self._refresh()

    def _clear(self) -> None:
        self._sel_id = None
        for v in (self._pname, self._bank, self._cno, self._camt,
                  self._billno, self._bamt, self._paid):
            v.set("")
        self._cdate.set(today_str())
        self._bdate.set(today_str())


# ─────────────────────────────────────────────────────────────────────────────
#  Voucher Entry
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
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self.title(),
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)

        self._vdate  = tk.StringVar(value=today_str())
        self._lf     = tk.StringVar()
        self._part   = tk.StringVar()
        self._part1  = tk.StringVar()
        self._debit  = tk.StringVar(value="0.00")
        self._credit = tk.StringVar(value="0.00")

        fields = [
            ("Date",         self._vdate,  12),
            ("Ledger Folio", self._lf,     8),
            ("Particulars",  self._part,   36),
            ("Narration",    self._part1,  36),
            ("Debit (Dr)",   self._debit,  14),
            ("Credit (Cr)",  self._credit, 14),
        ]
        for i, (lbl_t, var, w) in enumerate(fields):
            lbl(ef, lbl_t).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ent(ef, var, width=w).grid(row=i, column=1, sticky="w", padx=4, pady=2)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=len(fields), column=0, columnspan=2, pady=8)
        btn(bf, "Save",   self._save,   width=8, bg="#90EE90").pack(side="left", padx=4)
        if self.edit:
            btn(bf, "Delete", self._delete, width=8, bg="#FFB6C1").pack(side="left", padx=4)
        btn(bf, "Clear",  self._clear,  width=8).pack(side="left", padx=4)
        btn(bf, "Close",  self.destroy, width=8).pack(side="left", padx=4)

        cols = ("Date", "Particulars", "Narration", "Debit", "Credit")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c, w in zip(cols, [80, 220, 160, 90, 90]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        if self.edit:
            self.tv.bind("<<TreeviewSelect>>", self._on_select)
        self._sel_id: Optional[int] = None

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        rows = self.app.db.execute(
            "SELECT id,VDate,Part,Part1,Debit,Credit FROM Data "
            "ORDER BY id DESC LIMIT 500"
        ).fetchall()
        for r in rows:
            self.tv.insert("", "end", iid=str(r["id"]),
                           values=(r["VDate"], r["Part"], r["Part1"] or "",
                                   fmt_amt(to_float(r["Debit"])),
                                   fmt_amt(to_float(r["Credit"]))))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if not sel:
            return
        self._sel_id = int(sel[0])
        row = self.app.db.execute(
            "SELECT * FROM Data WHERE id=?", (self._sel_id,)
        ).fetchone()
        if row:
            self._vdate.set(row["VDate"])
            self._lf.set(str(row["LF"] or ""))
            self._part.set(row["Part"] or "")
            self._part1.set(row["Part1"] or "")
            self._debit.set(fmt_amt(to_float(row["Debit"])))
            self._credit.set(fmt_amt(to_float(row["Credit"])))

    def _save(self) -> None:
        part = self._part.get().strip()
        if not part:
            messagebox.showwarning("Required", "Particulars required.", parent=self)
            return
        nxt = db.next_no(self.app.db, "Vch")
        self.app.db.execute(
            "INSERT INTO Data(VDate,LF,Part,Part1,Debit,Credit) "
            "VALUES (?,?,?,?,?,?)",
            (parse_date(self._vdate.get()),
             int(to_float(self._lf.get())),
             part, self._part1.get().strip(),
             to_float(self._debit.get()),
             to_float(self._credit.get()))
        )
        self.app.db.commit()
        db.advance_no(self.app.db, "Vch", nxt)
        self._clear()
        self._refresh()

    def _delete(self) -> None:
        if self._sel_id is None:
            return
        if messagebox.askyesno("Delete", "Delete this voucher?", parent=self):
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


# ─────────────────────────────────────────────────────────────────────────────
#  Day Book
# ─────────────────────────────────────────────────────────────────────────────

class DayBookForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Day Book")
        self.geometry("780x520+90+60")
        self._build()
        self._load()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Day Book",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=8, pady=4)
        lbl(fr, "From").pack(side="left")
        self._frm = tk.StringVar(value=fy_start(self.app.syear))
        ent(fr, self._frm, width=12).pack(side="left", padx=4)
        lbl(fr, "To").pack(side="left")
        self._to = tk.StringVar(value=today_str())
        ent(fr, self._to, width=12).pack(side="left", padx=4)
        btn(fr, "Load", self._load, width=6).pack(side="left", padx=4)

        # Summary labels
        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=8)
        self._tot_dr = tk.StringVar(value="Dr: 0.00")
        self._tot_cr = tk.StringVar(value="Cr: 0.00")
        lbl(sf, "", textvariable=self._tot_dr, font=FONT_BOLD).pack(side="left", padx=12)
        lbl(sf, "", textvariable=self._tot_cr, font=FONT_BOLD).pack(side="left")

        cols = ("Date", "Particulars", "Narration", "Debit", "Credit")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c, w in zip(cols, [80, 260, 160, 100, 100]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        btn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        rows = self.app.db.execute(
            "SELECT VDate,Part,Part1,Debit,Credit FROM Data "
            "ORDER BY VDate, id LIMIT 2000"
        ).fetchall()
        total_dr = total_cr = 0.0
        for r in rows:
            dr = to_float(r["Debit"])
            cr = to_float(r["Credit"])
            total_dr += dr
            total_cr += cr
            self.tv.insert("", "end", values=(
                r["VDate"], r["Part"], r["Part1"] or "",
                fmt_amt(dr) if dr else "",
                fmt_amt(cr) if cr else "",
            ))
        self._tot_dr.set(f"Total Debit: {fmt_amt(total_dr)}")
        self._tot_cr.set(f"Total Credit: {fmt_amt(total_cr)}")


# ─────────────────────────────────────────────────────────────────────────────
#  Ledger
# ─────────────────────────────────────────────────────────────────────────────

class LedgerForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Ledger")
        self.geometry("800x540+90+55")
        self._build()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Ledger",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=8, pady=4)
        lbl(fr, "Account:").pack(side="left")
        self._acct = tk.StringVar()
        acct_cb = ttk.Combobox(fr, textvariable=self._acct, width=32)
        all_p = [r["Party"] for r in db.get_all_parties(self.app.db)]
        acct_cb["values"] = all_p
        acct_cb.pack(side="left", padx=4)
        lbl(fr, "From").pack(side="left", padx=4)
        self._frm = tk.StringVar(value=fy_start(self.app.syear))
        ent(fr, self._frm, width=12).pack(side="left")
        lbl(fr, "To").pack(side="left", padx=4)
        self._to = tk.StringVar(value=today_str())
        ent(fr, self._to, width=12).pack(side="left")
        btn(fr, "Load", self._load, width=6).pack(side="left", padx=4)

        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=8)
        self._bal = tk.StringVar(value="Balance: 0.00")
        lbl(sf, "", textvariable=self._bal, font=FONT_BOLD).pack(side="left")

        cols = ("Date", "Particulars", "Debit", "Credit", "Balance")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c, w in zip(cols, [80, 300, 100, 100, 110]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        btn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        acct = self._acct.get().strip()
        rows = self.app.db.execute(
            "SELECT VDate,Part,Debit,Credit FROM Data "
            "WHERE Part LIKE ? ORDER BY VDate, id LIMIT 1000",
            (f"%{acct}%",)
        ).fetchall()
        balance = 0.0
        for r in rows:
            dr = to_float(r["Debit"])
            cr = to_float(r["Credit"])
            balance = round(balance + dr - cr, 2)
            self.tv.insert("", "end", values=(
                r["VDate"], r["Part"],
                fmt_amt(dr) if dr else "",
                fmt_amt(cr) if cr else "",
                fmt_amt(balance),
            ))
        self._bal.set(f"Closing Balance: {fmt_amt(balance)}")


# ─────────────────────────────────────────────────────────────────────────────
#  Trial Balance
# ─────────────────────────────────────────────────────────────────────────────

class TrialBalanceForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Trial Balance")
        self.geometry("700x520+90+55")
        self._build()
        self._load()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Trial Balance",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)
        btn(self._make_btn_row(), "Refresh", self._load, width=8).pack(side="left", padx=4)

        cols = ("Account", "Total Debit", "Total Credit", "Balance")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=20)
        for c, w in zip(cols, [260, 120, 120, 120]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)

        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=8)
        self._tot_dr = tk.StringVar()
        self._tot_cr = tk.StringVar()
        lbl(sf, "", textvariable=self._tot_dr, font=FONT_BOLD).pack(side="left", padx=8)
        lbl(sf, "", textvariable=self._tot_cr, font=FONT_BOLD).pack(side="left")
        btn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _make_btn_row(self) -> tk.Frame:
        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=8, pady=4)
        return fr

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        rows = self.app.db.execute(
            "SELECT Part, SUM(Debit) as dr, SUM(Credit) as cr "
            "FROM Data GROUP BY Part ORDER BY Part"
        ).fetchall()
        tot_dr = tot_cr = 0.0
        for r in rows:
            dr = to_float(r["dr"])
            cr = to_float(r["cr"])
            bal = round(dr - cr, 2)
            tot_dr += dr
            tot_cr += cr
            self.tv.insert("", "end", values=(
                r["Part"], fmt_amt(dr), fmt_amt(cr), fmt_amt(bal)
            ))
        self._tot_dr.set(f"Total Dr: {fmt_amt(tot_dr)}")
        self._tot_cr.set(f"Total Cr: {fmt_amt(tot_cr)}")


# ─────────────────────────────────────────────────────────────────────────────
#  Statement views (Inward / Bill / GST)
# ─────────────────────────────────────────────────────────────────────────────

class StatementForm(tk.Toplevel):
    TITLE: str = "Statement"
    TABLE: str = "BILL"

    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title(self.TITLE)
        self.geometry("860x520+70+50")
        self._build()
        self._load()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text=self.TITLE,
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="x", padx=8, pady=4)
        lbl(fr, "From").pack(side="left")
        self._frm = tk.StringVar(value=fy_start(self.app.syear))
        ent(fr, self._frm, width=12).pack(side="left", padx=4)
        lbl(fr, "To").pack(side="left")
        self._to = tk.StringVar(value=today_str())
        ent(fr, self._to, width=12).pack(side="left", padx=4)
        lbl(fr, "Party").pack(side="left")
        self._party = tk.StringVar()
        ent(fr, self._party, width=20).pack(side="left", padx=4)
        btn(fr, "Load", self._load, width=6).pack(side="left", padx=4)

        cols = ("No.", "Date", "Party", "Taxable", "CGST", "SGST", "IGST", "Net Amt")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c, w in zip(cols, [55, 80, 220, 80, 65, 65, 65, 85]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)

        sf = tk.Frame(self, bg=FORM_BG)
        sf.pack(fill="x", padx=8)
        self._summary = tk.StringVar()
        lbl(sf, "", textvariable=self._summary, font=FONT_BOLD).pack(side="left")
        btn(self, "Close", self.destroy, width=10).pack(pady=4)

    def _load(self) -> None:
        self.tv.delete(*self.tv.get_children())
        party_filter = self._party.get().strip()
        try:
            if party_filter:
                rows = self.app.db.execute(
                    f"SELECT DISTINCT inwno,inwdate,pname,TAMT,CGST,SGST,IGST,NETAMT "
                    f"FROM {self.TABLE} WHERE pname LIKE ? "
                    f"ORDER BY CAST(inwno AS INTEGER)",
                    (f"%{party_filter}%",)
                ).fetchall()
            else:
                rows = self.app.db.execute(
                    f"SELECT DISTINCT inwno,inwdate,pname,TAMT,CGST,SGST,IGST,NETAMT "
                    f"FROM {self.TABLE} ORDER BY CAST(inwno AS INTEGER)"
                ).fetchall()
        except Exception:
            return

        tot = 0.0
        for r in rows:
            net = to_float(r["NETAMT"])
            tot += net
            self.tv.insert("", "end", values=(
                r["inwno"], r["inwdate"], r["pname"],
                fmt_amt(to_float(r["TAMT"])),
                fmt_amt(to_float(r["CGST"])),
                fmt_amt(to_float(r["SGST"])),
                fmt_amt(to_float(r["IGST"])),
                fmt_amt(net),
            ))
        self._summary.set(f"Total: {fmt_amt(tot)}  |  Records: {len(rows)}")


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
#  Stock
# ─────────────────────────────────────────────────────────────────────────────

class StockForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Stock")
        self.geometry("620x480+110+70")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Stock",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)
        self._pname = tk.StringVar()
        self._stock = tk.StringVar(value="0")
        self._units = tk.StringVar()
        fields = [("Item Name", self._pname, 32),
                  ("Stock Qty", self._stock, 10),
                  ("Units",     self._units, 10)]
        for i, (lbl_t, var, w) in enumerate(fields):
            lbl(ef, lbl_t).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ent(ef, var, width=w).grid(row=i, column=1, sticky="w", padx=4, pady=2)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=len(fields), column=0, columnspan=2, pady=8)
        btn(bf, "Save",   self._save,   width=8, bg="#90EE90").pack(side="left", padx=4)
        btn(bf, "Delete", self._delete, width=8, bg="#FFB6C1").pack(side="left", padx=4)
        btn(bf, "Clear",  self._clear,  width=8).pack(side="left", padx=4)
        btn(bf, "Close",  self.destroy, width=8).pack(side="left", padx=4)

        cols = ("Item", "Stock", "Units")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=16)
        for c, w in zip(cols, [320, 100, 80]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        for r in self.app.db.execute(
            "SELECT pname,stock,units FROM Stock ORDER BY pname"
        ).fetchall():
            self.tv.insert("", "end", values=(r["pname"], r["stock"], r["units"] or ""))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if sel:
            v = self.tv.item(sel[0])["values"]
            self._pname.set(v[0])
            self._stock.set(str(v[1]))
            self._units.set(v[2])

    def _save(self) -> None:
        pname = self._pname.get().strip()
        if not pname:
            messagebox.showwarning("Required", "Item Name required.", parent=self)
            return
        self.app.db.execute(
            "INSERT INTO Stock(pname,stock,units) VALUES (?,?,?) "
            "ON CONFLICT(pname) DO UPDATE SET stock=excluded.stock, units=excluded.units",
            (pname, int(to_float(self._stock.get())), self._units.get().strip())
        )
        self.app.db.commit()
        self._refresh()

    def _delete(self) -> None:
        pname = self._pname.get().strip()
        if not pname:
            return
        if messagebox.askyesno("Delete", f"Delete '{pname}'?", parent=self):
            self.app.db.execute("DELETE FROM Stock WHERE pname=?", (pname,))
            self.app.db.commit()
            self._clear()
            self._refresh()

    def _clear(self) -> None:
        self._pname.set("")
        self._stock.set("0")
        self._units.set("")


# ─────────────────────────────────────────────────────────────────────────────
#  Product Master
# ─────────────────────────────────────────────────────────────────────────────

class ProductMasterForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Product Master")
        self.geometry("640x500+110+70")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Product Master",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)
        self._pname  = tk.StringVar()
        self._hsn    = tk.StringVar()
        self._rate   = tk.StringVar()
        self._units  = tk.StringVar()
        fields = [("Product Name", self._pname, 36),
                  ("HSN/SAC Code", self._hsn,   16),
                  ("Default Rate", self._rate,  12),
                  ("Units",        self._units, 12)]
        for i, (lbl_t, var, w) in enumerate(fields):
            lbl(ef, lbl_t).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ent(ef, var, width=w).grid(row=i, column=1, sticky="w", padx=4, pady=2)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=len(fields), column=0, columnspan=2, pady=8)
        btn(bf, "Save",   self._save,   width=8, bg="#90EE90").pack(side="left", padx=4)
        btn(bf, "Delete", self._delete, width=8, bg="#FFB6C1").pack(side="left", padx=4)
        btn(bf, "Clear",  self._clear,  width=8).pack(side="left", padx=4)
        btn(bf, "Close",  self.destroy, width=8).pack(side="left", padx=4)

        cols = ("Product", "HSN", "Rate", "Units")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c, w in zip(cols, [260, 100, 80, 80]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        for r in self.app.db.execute(
            "SELECT pname,hsncode,rate,units FROM ProductMaster ORDER BY pname"
        ).fetchall():
            self.tv.insert("", "end",
                           values=(r["pname"], r["hsncode"] or "",
                                   fmt_amt(to_float(r["rate"])), r["units"] or ""))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if sel:
            v = self.tv.item(sel[0])["values"]
            self._pname.set(v[0])
            self._hsn.set(v[1])
            self._rate.set(str(v[2]))
            self._units.set(v[3])

    def _save(self) -> None:
        pname = self._pname.get().strip()
        if not pname:
            messagebox.showwarning("Required", "Product Name required.", parent=self)
            return
        self.app.db.execute(
            "INSERT INTO ProductMaster(pname,hsncode,rate,units) VALUES (?,?,?,?) "
            "ON CONFLICT(pname) DO UPDATE SET hsncode=excluded.hsncode, "
            "rate=excluded.rate, units=excluded.units",
            (pname, self._hsn.get().strip(),
             to_float(self._rate.get()), self._units.get().strip())
        )
        self.app.db.commit()
        self._refresh()

    def _delete(self) -> None:
        pname = self._pname.get().strip()
        if not pname:
            return
        if messagebox.askyesno("Delete", f"Delete '{pname}'?", parent=self):
            self.app.db.execute("DELETE FROM ProductMaster WHERE pname=?", (pname,))
            self.app.db.commit()
            self._clear()
            self._refresh()

    def _clear(self) -> None:
        self._pname.set("")
        self._hsn.set("")
        self._rate.set("")
        self._units.set("")


# ─────────────────────────────────────────────────────────────────────────────
#  Usage Entry
# ─────────────────────────────────────────────────────────────────────────────

class UsageForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Usage Entry")
        self.geometry("660x500+110+70")
        self._build()
        self._refresh()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Usage Entry",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        ef = tk.Frame(self, bg=FORM_BG)
        ef.pack(fill="x", padx=12, pady=6)

        self._date  = tk.StringVar(value=today_str())
        self._item  = tk.StringVar()
        self._qty   = tk.StringVar(value="1")
        self._units = tk.StringVar()
        self._note  = tk.StringVar()

        # Populate items from Stock
        all_items = [r["pname"] for r in self.app.db.execute(
            "SELECT pname FROM Stock ORDER BY pname"
        ).fetchall()]

        fields_w: list[tuple[str, tk.Variable, int]] = [
            ("Date",    self._date,  12),
            ("Qty",     self._qty,   8),
            ("Units",   self._units, 10),
            ("Note",    self._note,  36),
        ]
        lbl(ef, "Date").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        ent(ef, self._date, width=12).grid(row=0, column=1, sticky="w", padx=4)
        lbl(ef, "Item").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        item_cb = ttk.Combobox(ef, textvariable=self._item,
                               values=all_items, width=34)
        item_cb.grid(row=1, column=1, sticky="w", padx=4, pady=2)
        for i, (lbl_t, var, w) in enumerate(fields_w[1:], start=2):
            lbl(ef, lbl_t).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            ent(ef, var, width=w).grid(row=i, column=1, sticky="w", padx=4, pady=2)

        bf = tk.Frame(ef, bg=FORM_BG)
        bf.grid(row=len(fields_w)+2, column=0, columnspan=2, pady=8)
        btn(bf, "Save",   self._save,   width=8, bg="#90EE90").pack(side="left", padx=4)
        btn(bf, "Delete", self._delete, width=8, bg="#FFB6C1").pack(side="left", padx=4)
        btn(bf, "Close",  self.destroy, width=8).pack(side="left", padx=4)

        cols = ("Date", "Item", "Qty", "Units", "Note")
        self.tv = ttk.Treeview(self, columns=cols, show="headings", height=10)
        for c, w in zip(cols, [80, 220, 60, 60, 180]):
            self.tv.heading(c, text=c)
            self.tv.column(c, width=w)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        sb.pack(side="left", fill="y", pady=4)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)
        self._sel_id: Optional[int] = None

    def _refresh(self) -> None:
        self.tv.delete(*self.tv.get_children())
        for r in self.app.db.execute(
            "SELECT id,pdt,pname,qty FROM Sales ORDER BY id DESC LIMIT 300"
        ).fetchall():
            self.tv.insert("", "end", iid=str(r["id"]),
                           values=(r["pdt"], r["pname"], r["qty"], "", ""))

    def _on_select(self, _: Any) -> None:
        sel = self.tv.selection()
        if sel:
            self._sel_id = int(sel[0])
            v = self.tv.item(sel[0])["values"]
            self._date.set(v[0])
            self._item.set(v[1])
            self._qty.set(str(v[2]))

    def _save(self) -> None:
        item = self._item.get().strip()
        if not item:
            messagebox.showwarning("Required", "Item required.", parent=self)
            return
        qty = max(1, int(to_float(self._qty.get())))
        self.app.db.execute(
            "INSERT INTO Sales(pdt,pname,qty) VALUES (?,?,?)",
            (parse_date(self._date.get()), item, qty)
        )
        # Decrement stock
        self.app.db.execute(
            "UPDATE Stock SET stock=MAX(0,stock-?) WHERE pname=?",
            (qty, item)
        )
        self.app.db.commit()
        self._refresh()

    def _delete(self) -> None:
        if self._sel_id is None:
            return
        if messagebox.askyesno("Delete", "Delete this usage entry?", parent=self):
            self.app.db.execute("DELETE FROM Sales WHERE id=?", (self._sel_id,))
            self.app.db.commit()
            self._sel_id = None
            self._refresh()


# ─────────────────────────────────────────────────────────────────────────────
#  Delete Dialog
# ─────────────────────────────────────────────────────────────────────────────

class DeleteForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Delete Record")
        self.geometry("460x260+200+180")
        self._build()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Delete Record",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="both", expand=True, padx=20, pady=15)

        self._table = tk.StringVar(value="Quotation")
        self._inwno = tk.StringVar()

        lbl(fr, "Document Type").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        tables = ["Quotation", "DC", "BILL", "ItemInward",
                  "inward", "purchase", "PO"]
        ttk.Combobox(fr, textvariable=self._table,
                     values=tables, width=16, state="readonly"
                     ).grid(row=0, column=1, sticky="w", padx=4)

        lbl(fr, "Document No.").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        ent(fr, self._inwno, width=14).grid(row=1, column=1, sticky="w", padx=4)

        bf = tk.Frame(fr, bg=FORM_BG)
        bf.grid(row=2, column=0, columnspan=2, pady=12)
        btn(bf, "Delete", self._delete, width=10, bg="#FFB6C1").pack(side="left", padx=6)
        btn(bf, "Close",  self.destroy, width=10).pack(side="left", padx=6)

    def _delete(self) -> None:
        table = self._table.get()
        inwno = self._inwno.get().strip()
        if not inwno:
            messagebox.showwarning("Required", "Enter document number.", parent=self)
            return
        if messagebox.askyesno("Confirm",
                                f"Delete {table} No. {inwno}?", parent=self):
            try:
                n = db.delete_doc(self.app.db, table, inwno)
                messagebox.showinfo("Deleted",
                                    f"{n} rows deleted from {table}.", parent=self)
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
#  Others (Settings)
# ─────────────────────────────────────────────────────────────────────────────

class OthersForm(tk.Toplevel):
    def __init__(self, master: tk.Widget, app: "App") -> None:
        super().__init__(master)
        self.app = app
        self.configure(bg=FORM_BG)
        self.title("Others / Settings")
        self.geometry("440x360+180+140")
        self._build()
        self._load()

    def _build(self) -> None:
        hdr = tk.Frame(self, bg=HDR_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Others / Settings",
                 bg=HDR_BG, fg=WH, font=FONT_TITLE).pack(fill="x", pady=6)

        fr = tk.Frame(self, bg=FORM_BG)
        fr.pack(fill="both", expand=True, padx=20, pady=15)

        self._email   = tk.StringVar()
        self._pwd     = tk.StringVar()
        self._gst_pct = tk.StringVar(value="18")
        self._newpwd  = tk.StringVar()

        fields = [
            ("Gmail Address",       self._email,   30, {}),
            ("Gmail Password",      self._pwd,     20, {"show": "*"}),
            ("Default GST %",       self._gst_pct, 6,  {}),
            ("Change App Password", self._newpwd,  16, {"show": "*"}),
        ]
        for i, (lbl_t, var, w, kw) in enumerate(fields):
            lbl(fr, lbl_t).grid(row=i, column=0, sticky="e", padx=6, pady=4)
            ent(fr, var, width=w, **kw).grid(row=i, column=1, sticky="w", padx=4)

        bf = tk.Frame(fr, bg=FORM_BG)
        bf.grid(row=len(fields), column=0, columnspan=2, pady=12)
        btn(bf, "Save",  self._save,   width=8, bg="#90EE90").pack(side="left", padx=6)
        btn(bf, "Close", self.destroy, width=8).pack(side="left", padx=6)

    def _load(self) -> None:
        row = self.app.db.execute(
            "SELECT EMAIL,PWD FROM EMAIL WHERE id=1"
        ).fetchone()
        if row:
            self._email.set(row["EMAIL"] or "")
            self._pwd.set(row["PWD"] or "")
        stax = self.app.db.execute(
            "SELECT STax FROM ServTax WHERE id=1"
        ).fetchone()
        if stax:
            self._gst_pct.set(str(stax["STax"]))

    def _save(self) -> None:
        email  = self._email.get().strip()
        pwd    = self._pwd.get().strip()
        gst    = to_float(self._gst_pct.get()) or 18.0
        newpwd = self._newpwd.get().strip()

        self.app.db.execute(
            "UPDATE EMAIL SET EMAIL=?,PWD=?,SEMAIL=? WHERE id=1",
            (email, pwd, email)
        )
        self.app.db.execute(
            "UPDATE ServTax SET STax=? WHERE id=1", (gst,)
        )
        self.app.db.commit()

        if newpwd:
            SplashScreen._password = newpwd

        messagebox.showinfo("Saved", "Settings saved.", parent=self)
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  Application Controller
# ─────────────────────────────────────────────────────────────────────────────

class App:
    def __init__(self) -> None:
        self.root    = tk.Tk()
        self.root.withdraw()
        self.db:     sqlite3.Connection
        self.syear:  int = 0
        self.eyear:  int = 0
        self.cpycon: sqlite3.Connection = db.get_cpydb()
        SplashScreen(self.root, self._show_company_select)

    def _show_company_select(self) -> None:
        CompanySelector(self.root, self.cpycon, self._on_company_selected)

    def _on_company_selected(self, folder: str,
                              syear: int, eyear: int) -> None:
        self.syear = syear
        self.eyear = eyear
        self.db    = db.get_year_db(folder)
        MainMenu(self.root, self)

    def _guard(self) -> bool:
        return hasattr(self, "db") and self.db is not None

    # ── Openers ───────────────────────────────────────────────────────────────
    def open_quotation(self)      -> None:
        if self._guard(): QuotationForm(self.root, self)

    def open_inward(self)         -> None:
        if self._guard(): ItemInwardForm(self.root, self)

    def open_dc(self)             -> None:
        if self._guard(): DCForm(self.root, self)

    def open_bill(self)           -> None:
        if self._guard(): BillForm(self.root, self)

    def open_purchase(self)       -> None:
        if self._guard(): PurchaseForm(self.root, self)

    def open_usage(self)          -> None:
        if self._guard(): UsageForm(self.root, self)

    def open_stock(self)          -> None:
        if self._guard(): StockForm(self.root, self)

    def open_product_master(self) -> None:
        if self._guard(): ProductMasterForm(self.root, self)

    def open_ledger_creation(self)-> None:
        if self._guard(): LedgerCreationForm(self.root, self)

    def open_po(self)             -> None:
        if self._guard(): POForm(self.root, self)

    def open_cheque_pay(self)     -> None:
        if self._guard(): ChequePayForm(self.root, self)

    def open_voucher(self)        -> None:
        if self._guard(): VoucherForm(self.root, self, edit=False)

    def open_edit_voucher(self)   -> None:
        if self._guard(): VoucherForm(self.root, self, edit=True)

    def open_daybook(self)        -> None:
        if self._guard(): DayBookForm(self.root, self)

    def open_ledger(self)         -> None:
        if self._guard(): LedgerForm(self.root, self)

    def open_trial_balance(self)  -> None:
        if self._guard(): TrialBalanceForm(self.root, self)

    def open_inward_stmt(self)    -> None:
        if self._guard(): InwardStatement(self.root, self)

    def open_bill_stmt(self)      -> None:
        if self._guard(): BillStatement(self.root, self)

    def open_gst_stmt(self)       -> None:
        if self._guard(): GSTStatement(self.root, self)

    def open_delete(self)         -> None:
        if self._guard(): DeleteForm(self.root, self)

    def open_others(self)         -> None:
        if self._guard(): OthersForm(self.root, self)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
