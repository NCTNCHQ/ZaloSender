@echo off
cd /d "%~dp0he_thong"
title CAI DAT - Gui tin nhan Zalo tu dong
color 1F
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY goto nopython
%PY% cai_dat.py
echo.
pause
exit /b

:nopython
color 4F
echo.
echo  ============================================================
echo     MAY CHUA CO PYTHON  (can Python 3.9 tro len)
echo  ============================================================
echo.
echo   Dang mo trang tai Python: https://www.python.org/downloads/
echo.
echo   KHI CAI PYTHON, NHO TICH VAO O:
echo        [x] Add Python to PATH    (o o cuoi cua so cai dat)
echo.
echo   Cai Python xong, BAM DUP LAI VAO FILE:
echo        "1-CAI DAT (bam dup vao day)"
echo  ============================================================
start "" "https://www.python.org/downloads/"
pause
