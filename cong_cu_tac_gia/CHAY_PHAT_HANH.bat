@echo off
cd /d "%~dp0"
set "PY="
py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
if not defined PY python -c "import sys" >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Chua co Python.
  pause
  exit /b
)
%PY% -m pip install -q cryptography
%PY% phat_hanh.py
if errorlevel 1 pause
