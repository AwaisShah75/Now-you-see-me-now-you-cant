@echo off
setlocal
cd /d "%~dp0"
set "TEMP=%~dp0.runtime\tmp"
set "TMP=%~dp0.runtime\tmp"
set "PIP_CACHE_DIR=%~dp0.runtime\pip-cache"
set "PYTHONPYCACHEPREFIX=%~dp0.runtime\pycache"
set "MPLCONFIGDIR=%~dp0.runtime\matplotlib"
if not exist "%TEMP%" mkdir "%TEMP%"
if exist .venv\Scripts\python.exe goto dependencies
py -3.12 -m venv .venv
if errorlevel 1 py -3.11 -m venv .venv
if errorlevel 1 (
  echo Install Python 3.12 from python.org with the Python launcher enabled, then rerun.
  pause
  exit /b 1
)
:dependencies
if exist .venv\ready.txt goto run
.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection.
  pause
  exit /b 1
)
echo ready>.venv\ready.txt
:run
.venv\Scripts\python.exe app.py --record %*
if errorlevel 1 pause
