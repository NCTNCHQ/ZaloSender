@echo off
cd /d "%~dp0"
title Cai dat - Gui tin nhan Zalo tu dong
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY goto nopython
%PY% cai_dat.py
echo.
pause
exit /b

:nopython
echo ============================================================
echo  CHUA CO PYTHON (can Python 3.9 tro len)
echo ============================================================
echo  Dang mo trang tai Python: https://www.python.org/downloads/
echo.
echo  KHI CAI DAT PYTHON, NHO TICH VAO O:
echo     [x] Add Python to PATH   (o cuoi cua so cai dat)
echo.
echo  Cai Python xong, hay chay lai file CAI_DAT.bat nay.
echo ============================================================
start "" "https://www.python.org/downloads/"
pause
