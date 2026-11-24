@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Checking Python...
where py >nul 2>nul
if errorlevel 1 goto no_python

echo [2/3] Creating virtual environment if needed...
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto failed

echo [3/3] Installing Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto failed

echo.
echo Dependencies installed successfully.
pause
exit /b 0

:no_python
echo Python Launcher was not found. Install Python 3 and enable the py launcher.
pause
exit /b 1

:failed
echo Dependency installation failed. Check the messages above and your internet connection.
pause
exit /b 1
