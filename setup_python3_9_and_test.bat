@echo off
REM Batch script to set up Python 3.9 venv, install dependencies, and run tests

REM Step 1: Check for Python 3.9
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python 3.9 not found. Please install Python 3.9 from https://www.python.org/downloads/release/python-390/
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
if not "%PYTHON_VERSION:~0,3%"=="3.9" (
    echo Python 3.9 is required, but found version %PYTHON_VERSION%
    echo Please install Python 3.9 from https://www.python.org/downloads/release/python-390/
    exit /b 1
)

REM Step 2: Create virtual environment
python -m venv venv39

REM Step 3: Activate virtual environment
call venv39\Scripts\activate.bat

REM Step 4: Upgrade pip
python -m pip install --upgrade pip

REM Step 5: Install dependencies
pip install -r requirements.txt

REM Step 6: Run tests
python -m pytest tests/test_crypto_signal.py -v --cov=crypto_signal

REM Step 7: Deactivate venv
call venv39\Scripts\deactivate.bat

echo All done! 