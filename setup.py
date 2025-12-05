#!/usr/bin/env python3
"""
FlacLossless Windows Installer & Setup Script
Downloads and installs all dependencies, creates shortcuts, runs the app.

Usage: python setup.py
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from urllib.request import urlopen
import tempfile
import zipfile

class FlacLosslessInstaller:
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.venv_dir = self.app_dir / ".venv"
        self.backend_dir = self.app_dir / "FlacLossless-main" / "backend"
        self.frontend_dir = self.app_dir / "FlacLossless-main"
        
    def log(self, msg):
        print(f"[FlacLossless] {msg}")
    
    def check_python(self):
        """Check if Python 3.8+ is installed"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log("ERROR: Python 3.8+ required")
            return False
        self.log(f"✓ Python {version.major}.{version.minor} found")
        return True
    
    def check_node(self):
        """Check if Node.js is installed"""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            self.log(f"✓ Node.js {result.stdout.strip()} found")
            return True
        except FileNotFoundError:
            self.log("ERROR: Node.js not found. Download from https://nodejs.org/")
            return False
    
    def check_ffmpeg(self):
        """Check if ffmpeg is installed"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            self.log("✓ ffmpeg found")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.log("WARNING: ffmpeg not found (optional but recommended)")
            self.log("Download from: https://ffmpeg.org/download.html")
            return False
    
    def create_venv(self):
        """Create Python virtual environment"""
        if self.venv_dir.exists():
            self.log("✓ Virtual environment already exists")
            return True
        
        self.log("Creating Python virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], check=True)
            self.log("✓ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"ERROR: Failed to create venv: {e}")
            return False
    
    def get_pip_path(self):
        """Get path to pip in venv"""
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "pip.exe"
        return self.venv_dir / "bin" / "pip"
    
    def get_python_path(self):
        """Get path to python in venv"""
        if sys.platform == "win32":
            return self.venv_dir / "Scripts" / "python.exe"
        return self.venv_dir / "bin" / "python"
    
    def install_backend_deps(self):
        """Install backend Python dependencies"""
        self.log("Installing backend dependencies...")
        pip_path = self.get_pip_path()
        requirements = self.backend_dir / "requirements.txt"
        
        if not requirements.exists():
            self.log("ERROR: requirements.txt not found")
            return False
        
        try:
            subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
            subprocess.run([str(pip_path), "install", "-r", str(requirements)], check=True)
            self.log("✓ Backend dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"ERROR: Failed to install backend deps: {e}")
            return False
    
    def install_frontend_deps(self):
        """Install frontend Node dependencies"""
        self.log("Installing frontend dependencies...")
        
        node_modules = self.frontend_dir / "node_modules"
        if node_modules.exists():
            self.log("✓ Frontend dependencies already installed")
            return True
        
        try:
            subprocess.run(["npm", "install", "--silent"], cwd=str(self.frontend_dir), check=True)
            self.log("✓ Frontend dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"ERROR: Failed to install frontend deps: {e}")
            return False
    
    def create_shortcuts(self):
        """Create Windows shortcuts"""
        if sys.platform != "win32":
            return True
        
        try:
            import winshell
            self.log("Creating shortcuts...")
            
            # Create desktop shortcut
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "FlacLossless.lnk"
            
            run_bat = self.app_dir / "run_windows.bat"
            if run_bat.exists():
                shell = winshell.WshShell()
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.TargetPath = str(run_bat)
                shortcut.WorkingDirectory = str(self.app_dir)
                shortcut.save()
                self.log(f"✓ Desktop shortcut created")
        except ImportError:
            self.log("INFO: winshell not available, skipping shortcuts")
        except Exception as e:
            self.log(f"WARNING: Failed to create shortcuts: {e}")
        
        return True
    
    def run_app(self):
        """Start backend and frontend"""
        self.log("Starting application...")
        
        if sys.platform == "win32":
            # On Windows, use batch file
            bat_file = self.app_dir / "run_windows.bat"
            if bat_file.exists():
                subprocess.Popen(str(bat_file))
                self.log("Application launched!")
                return True
        else:
            # On Unix-like systems
            self.log("Starting backend...")
            python_path = self.get_python_path()
            backend_file = self.backend_dir / "server.py"
            subprocess.Popen([str(python_path), str(backend_file)])
            
            self.log("Starting frontend...")
            subprocess.Popen(["npm", "run", "dev"], cwd=str(self.frontend_dir))
            
            self.log("Application started! Open http://localhost:5173")
            return True
        
        return False
    
    def install(self):
        """Run full installation"""
        print("\n" + "="*50)
        print("FlacLossless Installer")
        print("="*50 + "\n")
        
        # Check requirements
        if not self.check_python():
            return False
        
        if not self.check_node():
            return False
        
        self.check_ffmpeg()
        
        print()
        
        # Install
        if not self.create_venv():
            return False
        
        if not self.install_backend_deps():
            return False
        
        if not self.install_frontend_deps():
            return False
        
        print()
        
        # Create shortcuts
        self.create_shortcuts()
        
        print("\n" + "="*50)
        print("Installation Complete!")
        print("="*50 + "\n")
        
        return True

if __name__ == "__main__":
    installer = FlacLosslessInstaller()
    
    if installer.install():
        print("Starting FlacLossless...\n")
        installer.run_app()
    else:
        print("\nInstallation failed. Check errors above.")
        sys.exit(1)
