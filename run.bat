@echo off
REM Run TransCreeper application

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Activate virtual environment if it exists
if exist "%SCRIPT_DIR%.venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
)

REM Run the application
python "%SCRIPT_DIR%src\main.py" %*
