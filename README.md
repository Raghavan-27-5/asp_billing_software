# Adhwaitha Sri Plating — Billing System
**Developer: Raghavan (Freelance)**  
Version 1.0 | 2025

---

## What this software does
GST-compliant job work billing system for chrome plating businesses.  
Core modules: Proforma Invoice, Delivery Challan, Cash/Credit Bill.  
Full suite: 11 entry forms + 10 report/statement views + PDF printing.

---

## Files in this project

| File | Purpose |
|---|---|
| `asp_main.py` | Main application — all UI and form logic |
| `asp_db.py` | Database layer — schema, queries, migrations |
| `asp_utils.py` | Utilities — GST calc, date parsing, amount-in-words |
| `asp_print.py` | PDF generation — Bill, DC, Proforma, Quotation |
| `migrate_mdb.py` | One-time migration from old .mdb files → SQLite |
| `test_asp.py` | Full test suite (39 tests) |
| `build_exe.bat` | Packages everything into a Windows .exe |
| `ganesha.png` | Deity image for splash screen |
| `requirements.txt` | Python dependencies |
| `Data/` | SQLite databases (one folder per financial year) |
| `cpydb.sqlite` | Company/year selector database |
| `Reports/` | Generated PDF files |

---

## Step-by-step: Developer setup (Raghavan's machine)

### Step 1 — Install Python
Download from https://python.org (Python 3.10 or newer).  
During install, tick "Add Python to PATH".

### Step 2 — Install dependencies
Open Command Prompt in the project folder:
```
pip install reportlab Pillow pyinstaller
```

### Step 3 — Migrate old data (one time only)
You need the original MDB files from the client's machine.  
They sent you: `CpyDB.mdb` and a `Data/` folder with `invsdi.mdb` files.

Put them in a folder, e.g. `C:\OldData\` so the structure is:
```
C:\OldData\CpyDB.mdb
C:\OldData\Data\ASP2425\invsdi.mdb
C:\OldData\Data\ASP2324\invsdi.mdb
C:\OldData\Data\ASP2122\invsdi.mdb
```

Then run (on Linux/Mac — needs mdbtools):
```
apt install mdbtools          # Linux only, one time
python3 migrate_mdb.py --mdb-dir /path/to/OldData
```

On Windows without mdbtools: skip migration for now and start fresh.  
The software works without old data — existing parties are seeded from  
the real MDB export already embedded in asp_db.py.

### Step 4 — Test it runs
```
python asp_main.py
```
Default password: `1234`  
Change it in Others → Settings.

### Step 5 — Run tests
```
python test_asp.py
```
All 39 tests should pass.

### Step 6 — Build the .exe
On Windows, double-click `build_exe.bat`.  
It produces: `dist\AdhwaithaSriPlating.exe`

---

## What to send to the client

**Option A — Simple (recommended for non-technical client):**

Create a folder called `AdhwaithaSriPlating` and put inside:
```
AdhwaithaSriPlating.exe    ← the program
cpydb.sqlite               ← company/year list
ganesha.png                ← deity image
Data\                      ← all their data
  ASP2425\invsdi.sqlite
  ASP2324\invsdi.sqlite
  ASP2122\invsdi.sqlite
Reports\                   ← empty folder (PDFs save here)
```

Zip this folder and send via WhatsApp/Google Drive.  
Tell them: **"Extract the zip, open the folder, double-click AdhwaithaSriPlating.exe"**

**That is all they ever need to do.**

---

## Do they need Python installed? No.
The .exe bundles Python + all libraries inside itself.  
Single double-click. Nothing else to install.

---

## Where is their data stored?
In the `Data/` folder next to the .exe — on their own computer.  
No internet, no cloud, no server. Fully offline.

**Tell them to back up the Data/ folder to a pen drive regularly.**

---

## Financial year rollover (every April)
They click "New Year" in the company selector screen.  
Type start year and end year. Done. No developer needed.

---

## Key features
- **Auto-fill from GST number**: type a customer's GST → name + address fills automatically
- **Auto-fill from party name**: type 2+ letters of name → GST + address fills automatically
- **Auto-save new parties**: once a customer is entered, they're saved forever
- **PDF printing**: Proforma Invoice, Job Work Bill, Delivery Challan, Quotation
- **GST auto-calculation**: CGST+SGST (intrastate) or IGST (interstate) based on party's GST state code
- **Amount in words**: auto-generated on every bill (Indian number system)
- **Multi-year**: all financial years in one software, no new EXE every year

---

## Default password
`1234`  
Change in: Others → Settings → "Change App Password"

---

## Annual Maintenance (for Raghavan)
- New financial year: 5 mins (they can do it themselves)
- Any bug fixes: update the .py files, rebuild .exe, resend
- No server to maintain, no hosting cost, no subscription

