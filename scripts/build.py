#!/usr/bin/env python3
"""
Build script for Podcast Player application.

This script handles building the application for distribution.
"""

import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def clean_build_dirs():
    """Clean previous build artifacts."""
    build_dirs = ['build', 'dist', '*.egg-info']
    for pattern in build_dirs:
        for path in Path('.').glob(pattern):
            if path.exists():
                print(f"Cleaning {path}")
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()


def build_wheel():
    """Build wheel distribution."""
    run_command("python -m build --wheel", "Building wheel")


def build_exe():
    """Build executable using PyInstaller."""
    # Check if PyInstaller is available
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing...")
        run_command("pip install pyinstaller", "Installing PyInstaller")
    
    # Check if spec file exists
    spec_file = Path("podcast_player.spec")
    if spec_file.exists():
        print("Using existing spec file...")
        run_command("pyinstaller podcast_player.spec", "Building executable with spec file")
    else:
        print("Creating executable with command line options...")
        # Build executable with command line options
        pyinstaller_args = [
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--name=PodcastPlayer",
            "--add-data=config:config",
            "--add-data=data:data", 
            "--hidden-import=tkinter",
            "--hidden-import=pygame",
            "--hidden-import=feedparser",
            "--hidden-import=requests",
            "--hidden-import=vlc",
            "--paths=src",
            "src/podcast_player/main.py"
        ]
        
        run_command(" ".join(pyinstaller_args), "Building executable")


def main():
    """Main build function."""
    if len(sys.argv) < 2:
        print("Usage: python build.py [wheel|exe|all|clean]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "clean":
        clean_build_dirs()
    elif action == "wheel":
        clean_build_dirs()
        build_wheel()
    elif action == "exe":
        clean_build_dirs()
        build_exe()
    elif action == "all":
        clean_build_dirs()
        build_wheel()
        build_exe()
    else:
        print(f"Unknown action: {action}")
        print("Available actions: wheel, exe, all, clean")
        sys.exit(1)
    
    print("Build completed successfully!")


if __name__ == "__main__":
    main()