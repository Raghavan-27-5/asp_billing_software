@echo off
setlocal

REM ============================================================
REM  build_exe.bat
REM  Builds Adhwaitha Sri Plating and creates a client ZIP.
REM
REM  Run this on the Windows build machine, not on Linux and not
REM  on the client's machine.
REM
REM  Prerequisites:
REM    1. Python 3.10+ installed from python.org
REM    2. Current repo already git-pulled on the Windows machine
REM
REM  Required files/folders in this repo before running:
REM    - Data\                     client SQLite data folder
REM    - cpydb.sqlite              company/year registry
REM    - ganesha.png               app splash/header image
REM    - ref\old_ui\asp_logo.jpg   print form logo
REM
REM  Final output to send:
REM    dist\AdhwaithaSriPlating_Client.zip
REM ============================================================

set "APP_NAME=AdhwaithaSriPlating"
set "PACKAGE_DIR=dist\%APP_NAME%_Client"
set "ZIP_PATH=dist\%APP_NAME%_Client.zip"

echo.
echo  Adhwaitha Sri Plating -- Client ZIP Builder
echo  ===========================================
echo.

echo [1/6] Checking required files...
if not exist "Data" (
    echo ERROR: Data folder is missing.
    pause
    exit /b 1
)
if not exist "cpydb.sqlite" (
    echo ERROR: cpydb.sqlite is missing.
    pause
    exit /b 1
)
if not exist "ganesha.png" (
    echo ERROR: ganesha.png is missing.
    pause
    exit /b 1
)
if not exist "ref\old_ui\asp_logo.jpg" (
    echo ERROR: ref\old_ui\asp_logo.jpg is missing.
    pause
    exit /b 1
)

echo [2/6] Installing Python packages...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is installed and on PATH.
    pause
    exit /b 1
)

if not exist "Reports" mkdir Reports

echo [3/6] Building EXE...
pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    --add-data "ref\old_ui\asp_logo.jpg;ref\old_ui" ^
    --hidden-import "PIL._tkinter_finder" ^
    asp_main.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo [4/6] Assembling client folder...
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%\Reports"
mkdir "%PACKAGE_DIR%\ref\old_ui"

copy /Y "dist\%APP_NAME%.exe" "%PACKAGE_DIR%\" >nul
copy /Y "cpydb.sqlite" "%PACKAGE_DIR%\" >nul
copy /Y "ganesha.png" "%PACKAGE_DIR%\" >nul
copy /Y "ref\old_ui\asp_logo.jpg" "%PACKAGE_DIR%\ref\old_ui\" >nul
xcopy "Data" "%PACKAGE_DIR%\Data" /E /I /Y >nul

if not exist "%PACKAGE_DIR%\%APP_NAME%.exe" (
    echo ERROR: EXE was not copied into the client folder.
    pause
    exit /b 1
)

echo [5/6] Writing client instructions...
(
    echo Adhwaitha Sri Plating
    echo ======================
    echo.
    echo To start the software:
    echo 1. Extract this ZIP file.
    echo 2. Open the extracted folder.
    echo 3. Double-click %APP_NAME%.exe.
    echo.
    echo Do not delete or rename the Data folder or cpydb.sqlite.
    echo Generated PDFs will be saved in the Reports folder.
    echo Back up the Data folder regularly.
) > "%PACKAGE_DIR%\READ_ME_FIRST.txt"

echo [6/6] Creating ZIP...
if exist "%ZIP_PATH%" del /q "%ZIP_PATH%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force"
if %errorlevel% neq 0 (
    echo ERROR: ZIP creation failed.
    pause
    exit /b 1
)

echo.
echo  DONE.
echo.
echo  Client ZIP:
echo    %ZIP_PATH%
echo.
echo  Send that ZIP file to the client. They only need to extract it
echo  and double-click %APP_NAME%.exe.
echo.
pause
endlocal
