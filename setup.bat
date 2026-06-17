@echo off
:: Set clean CLI colors (bright cyan text on black background)
color 0B
title Smart Attendance Tracker - Setup Wizard

echo =======================================================================
echo               Smart Attendance Tracker - Setup Wizard
echo =======================================================================
echo.
echo This script will verify your Python environment and install all
echo required dependencies for the Smart Attendance Tracker.
echo.
echo =======================================================================
echo.

:: Step 1: Check Python installation
echo [*] Checking Python installation...
set PYTHON_CMD=
python --version >temp_ver.txt 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
) else (
    py --version >temp_ver.txt 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    )
)
del temp_ver.txt >nul 2>&1

if "%PYTHON_CMD%"=="" (
    color 0C
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo.
    echo Please download and install Python from: https://www.python.org/downloads/
    echo During installation, make sure to check "Add Python to PATH".
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

for /f "tokens=2" %%I in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VER=%%I
echo [^+] Python %PYTHON_VER% detected (using %PYTHON_CMD% command).
echo.

:: Step 2: Check Pip installation
echo [*] Checking pip installation...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Pip is not available for your Python installation.
    echo.
    echo Trying to install pip...
    %PYTHON_CMD% -m ensurepip --default-pip
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install pip automatically.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)
echo [^+] Pip is available.
echo.

:: Step 3: Install Dependencies
echo [*] Upgrading pip to the latest version...
%PYTHON_CMD% -m pip install --upgrade pip
echo.
echo [*] Installing required python libraries from requirements.txt...
echo This might take a few moments...
echo.

%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR] Failed to install dependencies via requirements.txt.
    echo Attempting direct installation...
    echo.
    %PYTHON_CMD% -m pip install customtkinter opencv-python Pillow qrcode pyttsx3
    if %errorlevel% neq 0 (
        echo [ERROR] Direct installation also failed. Please check your internet connection.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

color 0A
echo.
echo =======================================================================
echo [^+] All dependencies installed successfully!
echo =======================================================================
echo.
echo Setup is complete. You can now run the application.
echo.

set /p choice="Do you want to launch the Smart Attendance Tracker now? (Y/N): "
if /i "%choice%"=="Y" (
    echo.
    echo [*] Launching application...
    start "" %PYTHON_CMD%w Main.pyw
) else (
    echo.
    echo You can run the application anytime using: %PYTHON_CMD% Main.pyw or double-clicking Main.pyw
    echo.
    echo Press any key to exit...
    pause >nul
)
