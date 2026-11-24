@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto no_python

if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto failed

echo Checking and installing required packages...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo Starting Gcalcal...
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto failed
exit /b 0

:no_python
echo Python Launcher was not found. Install Python 3 and enable the py launcher.
pause
exit /b 1

:failed
echo An error occurred. See the messages above.
pause
exit /b 1
