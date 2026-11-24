@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto :error

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Gcalcal.spec del /q Gcalcal.spec

".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --name Gcalcal --icon "assets\gcalcal.ico" --add-data "assets;assets" main.py
if errorlevel 1 goto :error

echo.
echo Build completed: dist\Gcalcal\Gcalcal.exe
echo The new Gcalcal calendar icon is embedded in the EXE.
pause
exit /b 0

:error
echo.
echo Build failed. Check the error messages above.
pause
exit /b 1
