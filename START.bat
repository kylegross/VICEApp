@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto ready
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m venv .venv
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Install Python 3.11 or newer from https://www.python.org/downloads/
    echo Then double-click START again.
    pause
    exit /b 1
  )
  python -m venv .venv
)
if errorlevel 1 goto failed
:ready
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
if not exist config.json (
  copy config.example.json config.json >nul
  echo Enter your token and server ID in the file that opens, save, and close Notepad.
  start /wait notepad.exe config.json
)
".venv\Scripts\python.exe" bot.py
pause
exit /b
:failed
echo Setup failed. Keep this window open to read the error.
pause
