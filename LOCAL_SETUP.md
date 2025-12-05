# Run FlacLossless Locally

This guide helps you run both the backend (Flask) and frontend (React/Vite) on your computer.

## Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 18+** (for frontend)
- **ffmpeg** (for audio conversion)
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: Download from https://ffmpeg.org/download.html

## Quick Start (Automated)

### macOS / Linux
```bash
cd /path/to/FlacLossless
chmod +x run_local.sh
./run_local.sh
```

### Windows (PowerShell)
```powershell
cd C:\path\to\FlacLossless
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip setuptools wheel
pip install -r FlacLossless-main\backend\requirements.txt
cd FlacLossless-main
npm install
# In one terminal:
python backend\server.py
# In another terminal:
npm run dev
```

After running, open **http://localhost:5173** in your browser.

---

## Manual Setup (Step-by-Step)

### Step 1: Clone & Navigate
```bash
git clone https://github.com/aviralspace/FlacLossless.git
cd FlacLossless
```

### Step 2: Setup Backend (Python)
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r FlacLossless-main/backend/requirements.txt
```

### Step 3: Setup Frontend (Node)
```bash
cd FlacLossless-main
npm install
cd ..
```

### Step 4: Start Backend (Terminal 1)
```bash
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
python3 FlacLossless-main/backend/server.py
```

Backend runs on **http://127.0.0.1:3001** and logs to the console.

### Step 5: Start Frontend (Terminal 2)
```bash
cd FlacLossless-main
npm run dev
```

Frontend dev server runs on **http://localhost:5173** (or **http://127.0.0.1:5173**).

### Step 6: Open in Browser
Visit **http://localhost:5173** and start using the app!

---

## Configuration

### Backend URL
The frontend automatically detects the backend:
- On `localhost`, it looks for `http://localhost:3001`
- You can override by setting `VITE_BACKEND_URL` environment variable when building:
  ```bash
  export VITE_BACKEND_URL=http://192.168.1.100:3001
  npm run dev
  ```

### YouTube Cookies
If downloads fail due to YouTube blocking:
1. Export cookies from your YouTube session using a browser extension (e.g., "Get cookies.txt")
2. Save as `youtube_cookies.txt` in the repo root or upload via the UI "Upload Cookies" button

---

## Troubleshooting

**"vite: command not found"**
- Make sure you ran `npm install` in `FlacLossless-main/`
- Or reinstall: `cd FlacLossless-main && npm install`

**"Port 3001 already in use"**
- Change backend port: `PORT=3002 python3 FlacLossless-main/backend/server.py`
- Then set frontend to use new port: `VITE_BACKEND_URL=http://localhost:3002 npm run dev`

**"ffmpeg not found"**
- Install ffmpeg (see Prerequisites section)

**Backend errors about yt-dlp**
- Ensure you're in the `.venv` virtual environment: `source .venv/bin/activate`
- Reinstall: `pip install -r FlacLossless-main/backend/requirements.txt`

**Frontend won't connect to backend**
- Check backend is running: `curl http://localhost:3001/health`
- Check logs in backend terminal for errors
- Verify both are on same network if using remote machine

---

## Production Build

To test a production build locally:
```bash
cd FlacLossless-main
npm run build
npm run preview
```

Open **http://localhost:4173** to see the optimized build.

---

## Stop Servers

**Linux/macOS:** `pkill -f "python3.*server.py" && pkill -f "vite"`
**Windows PowerShell:** `Get-Process python,node | Stop-Process`

---

## Next Steps

- Check the [main README](FlacLossless-main/README.md) for feature overview
- For deployment, see [DEPLOYMENT.md](FlacLossless-main/DEPLOYMENT.md)
