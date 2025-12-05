# FlacLossless Windows Installer & Launcher

This folder contains tools to install and run FlacLossless as a proper Windows application.

## Option 1: Simple Python Installer (Recommended)

**Requires:** Python 3.8+, Node.js 18+, and ffmpeg

1. Download the entire folder
2. Double-click `setup.py` **OR** run in PowerShell:
   ```powershell
   python setup.py
   ```
3. The installer will:
   - Create a Python virtual environment
   - Install all Python & Node dependencies
   - Create desktop shortcuts
   - Launch the app automatically

4. Once running, open http://localhost:5173 in your browser

---

## Option 2: NSIS Installer (Advanced)

For a professional .exe installer:

1. Install NSIS from https://nsis.sourceforge.io/
2. Right-click `installer.nsi` → "Compile NSIS Script"
3. Run `FlacLossless-Setup.exe`

---

## Option 3: Manual Setup

See `LOCAL_SETUP.md` for step-by-step terminal commands.

---

## Running the App Later

Once installed, just double-click `FlacLossless.lnk` on your desktop or in Start Menu.

Or run `run_windows.bat` from the installation folder.

---

## Troubleshooting

**"Python not found"**
- Download Python from https://www.python.org/ (make sure to add to PATH during install)

**"Node.js not found"**
- Download Node.js from https://nodejs.org/

**"ffmpeg not found"**
- Download from https://ffmpeg.org/ (optional but recommended for audio conversion)

**App won't start**
- Check that both terminal windows open (backend + frontend)
- If port 3001 or 5173 is in use, change them in `run_windows.bat`

**Can't download YouTube videos**
- Export YouTube cookies using a browser extension
- Upload via the app's "Upload Cookies" button

---

## Support

For issues, check the main `README.md` or `LOCAL_SETUP.md`
