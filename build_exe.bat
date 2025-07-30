@echo off
echo ====================================
echo    Podcast Player EXE Builder
echo ====================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if in virtual environment (optional but recommended)
echo Checking Python environment...
python -c "import sys; print('Virtual environment detected' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'Using system Python')"
echo.

REM Install build dependencies if needed
echo Installing build dependencies...
pip install pyinstaller python-vlc pygame feedparser requests mutagen
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
    REM --onefile ^
if exist *.spec del /q *.spec 2>nul

REM Build the executable
echo Building executable...
pyinstaller ^
    --windowed ^
    --name=PodcastPlayer ^
    --add-data="config;config" ^
    --add-data="data;data" ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=pygame ^
    --hidden-import=feedparser ^
    --hidden-import=requests ^
    --hidden-import=vlc ^
    --hidden-import=json ^
    --hidden-import=threading ^
    --hidden-import=urllib.parse ^
    --hidden-import=urllib.request ^
    --hidden-import=xml.etree.ElementTree ^
    --hidden-import=mutagen ^
    --paths=src ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=scipy ^
    --exclude-module=pandas ^
    --exclude-module=PIL ^
    --exclude-module=cv2 ^
    src/run.py

if errorlevel 1 (
    echo.
    echo Error: Build failed!
    echo Make sure VLC Media Player is installed on your system.
    echo Download from: https://www.videolan.org/vlc/
    pause
    exit /b 1
)
echo The executable is located at: dist\PodcastPlayer\PodcastPlayer.exe
echo.
echo ====================================
echo 2. The config and data directories are in the same folder as the PodcastPlayer.exe (inside dist\PodcastPlayer)
echo ====================================
echo.
echo The executable is located at: dist\PodcastPlayer.exe
echo.
echo Before running the executable, make sure:
echo 1. VLC Media Player is installed
echo 2. The config and data directories are in the same folder as the .exe
echo.
pause