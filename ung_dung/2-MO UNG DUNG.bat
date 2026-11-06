@echo off
cd /d "%~dp0he_thong"
title Gui tin nhan Zalo tu dong
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Chua co Python. Hay bam dup vao file 1-CAI DAT truoc.
  pause
  exit /b
)
%PY% app.py
if errorlevel 1 pause
