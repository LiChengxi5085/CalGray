@echo off
chcp 65001 >nul
title CalGary v1.0 - Image Data Converter

echo ========================================
echo    CalGary - Image Data Converter
echo ========================================
echo.

REM 设置环境变量
set QT_QPA_PLATFORM_PLUGIN_PATH=%~dp0PyQt5\Qt5\plugins\platforms
set QT_PLUGIN_PATH=%~dp0PyQt5\Qt5\plugins
set PYTHONPATH=%~dp0

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.13 from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 检查依赖
echo Checking dependencies...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PyQt5 not found. Installing...
    pip install pyqt5 numpy scipy matplotlib
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo Please run: pip install pyqt5 numpy scipy matplotlib
        pause
        exit /b 1
    )
)

echo.
echo Starting CalGary...
echo.

REM 启动程序
python "%~dp0main.py"

REM 如果程序异常退出
if errorlevel 1 (
    echo.
    echo [ERROR] Program exited with error code: %errorlevel%
    echo.
    echo Possible issues:
    echo   - Qt plugins not found
    echo   - Missing dependencies
    echo   - Python version incompatibility
    echo.
    echo Try running: python main.py
    echo.
    pause
    exit /b 1
)

pause