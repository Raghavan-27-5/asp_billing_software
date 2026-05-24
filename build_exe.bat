@echo off
REM ============================================================
REM  build_exe.bat
REM  Packages Adhwaitha Sri Plating into a single Windows .exe
REM
REM  Run this on YOUR Windows machine (Raghavan's machine),
REM  NOT on the client's machine.
REM
REM  Prerequisites:
REM    1. Python 3.10+ installed  (python.org)
REM    2. Run this script once — it installs everything else
REM
REM  Before running:
REM    - Make sure Data/ folder has the migrated SQLite files
REM    - Make sure cpydb.sqlite exists
REM    - Make sure ganesha.png exists
REM
REM  Output: dist\AdhwaithaSriPlating.exe  (send THIS to client)
REM ============================================================

echo.
echo  Adhwaitha Sri Plating -- EXE Builder
echo  ======================================
echo.

REM Install dependencies
echo [1/3] Installing Python packages...
pip install pyinstaller reportlab Pillow --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)

REM Ensure Data and Reports folders exist
if not exist "Data" mkdir Data
if not exist "Reports" mkdir Reports

echo [2/3] Building EXE...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "AdhwaithaSriPlating" ^
    --add-data "Data;Data" ^
    --add-data "Reports;Reports" ^
    --add-data "cpydb.sqlite;." ^
    --add-data "ganesha.png;." ^
    --hidden-import "PIL._tkinter_finder" ^
    asp_main.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo [3/3] Done.
echo.
echo  EXE location: dist\AdhwaithaSriPlating.exe
echo.
echo  -------------------------------------------------------
echo  WHAT TO SEND TO THE CLIENT:
echo    1. dist\AdhwaithaSriPlating.exe
echo    2. The entire Data\ folder  (their database)
echo    3. cpydb.sqlite
echo    4. ganesha.png
echo.
echo  Tell them: put all files in the SAME folder, then
echo  double-click AdhwaithaSriPlating.exe
echo  -------------------------------------------------------
echo.
pause
