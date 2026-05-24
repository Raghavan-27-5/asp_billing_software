#!/bin/bash
# =============================================================
# setup.sh — Run this ONE TIME on your machine (Linux/Mac)
# to install tools and migrate the old data.
#
# What it does:
#   1. Installs mdbtools (reads old .mdb files)
#   2. Installs Python packages
#   3. Migrates old .mdb data → SQLite
#   4. Verifies migration worked
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# =============================================================

set -e  # stop on any error

echo ""
echo "======================================================"
echo "  Adhwaitha Sri Plating — One-Time Setup"
echo "======================================================"
echo ""

# ── Step 1: mdbtools ──────────────────────────────────────
echo "[1/4] Installing mdbtools..."
if command -v mdb-tables &> /dev/null; then
    echo "      mdbtools already installed, skipping."
else
    if [ "$(uname)" == "Darwin" ]; then
        brew install mdbtools
    else
        sudo apt-get install -y mdbtools
    fi
fi

# ── Step 2: Python packages ───────────────────────────────
echo "[2/4] Installing Python packages..."
pip3 install reportlab Pillow --break-system-packages 2>/dev/null || \
pip3 install reportlab Pillow
echo "      Done."

# ── Step 3: Verify MDB files present ─────────────────────
echo "[3/4] Checking MDB files..."

MISSING=0
if [ ! -f "CpyDB.mdb" ]; then
    echo "      ERROR: CpyDB.mdb not found in current folder."
    MISSING=1
fi

for FOLDER in ASP2122 ASP2324 ASP2425; do
    if [ ! -f "Data/$FOLDER/invsdi.mdb" ]; then
        echo "      WARNING: Data/$FOLDER/invsdi.mdb not found (skipping that year)"
    else
        echo "      Found: Data/$FOLDER/invsdi.mdb"
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "  CpyDB.mdb is required. Place it in the same folder as this script."
    echo "  The Data/ folder structure should be:"
    echo "    Data/ASP2122/invsdi.mdb"
    echo "    Data/ASP2324/invsdi.mdb"
    echo "    Data/ASP2425/invsdi.mdb"
    exit 1
fi

# ── Step 4: Migrate ───────────────────────────────────────
echo "[4/4] Migrating old data to SQLite..."
python3 migrate_mdb.py --mdb-dir .

echo ""
echo "======================================================"
echo "  Setup complete!"
echo ""
echo "  SQLite databases created in: Data/"
echo "  Company registry: cpydb.sqlite"
echo ""
echo "  NEXT STEP (on Windows):"
echo "  Copy this entire folder to your Windows machine"
echo "  and double-click build_exe.bat"
echo "======================================================"
