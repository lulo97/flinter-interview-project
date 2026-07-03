@echo off

REM Change to the directory containing this batch file
cd /d "%~dp0"

REM Activate the virtual environment
call .venv\Scripts\activate.bat

REM Run the Python script
python src\implement\app.py

REM Keep the window open (optional)
pause