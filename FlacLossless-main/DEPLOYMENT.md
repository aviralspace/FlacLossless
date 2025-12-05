# Deployment Guide

## The Problem
Your **frontend** is deployed on Vercel, but your **backend** (Flask server) is still running locally. That's why YouTube search doesn't work on Vercel - the frontend can't reach the backend.

## Solution: Deploy Backend Separately

### Quick Option: Deploy to Railway.app (Easiest)
1. Go to [railway.app](https://railway.app)
2. Click "Create Project" → "Deploy from GitHub"
3. Select your FlacLossless repository
4. Railway will auto-detect it's Python
5. It will deploy and give you a URL like `https://flaclessless-production.up.railway.app`

### Connect Frontend to Backend
1. Copy your backend URL from Railway
2. Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**
3. Add new variable:
   - **Name:** `VITE_BACKEND_URL`
   - **Value:** `https://your-railway-url` (replace with actual URL, no trailing slash)
4. Click "Save" and **Redeploy** your Vercel project
5. Wait 1-2 minutes for Vercel to rebuild and deploy

### Test It
1. Go to your Vercel URL
2. Click **STREAM** button
3. Search for any song - it should now work! ✅

## Alternative Backends
- **Render.com** - Free tier available
- **Heroku** - Paid tier
- **AWS/Azure** - For production scale

## Environment Variables Needed

### Vercel (Frontend)
Add these in Vercel Dashboard → Settings → Environment Variables:
```
VITE_BACKEND_URL=https://your-backend-url.com
GEMINI_API_KEY=your_gemini_key (if using AI features)
VITE_SPOTIFY_CLIENT_ID=your_spotify_id (if using Spotify)
```

### Backend (Railway/Render)
Add these in your backend provider's environment variables:
```
PORT=5000
YT_COOKIES_FILE=/path/to/youtube_cookies.txt (optional, for YouTube auth)
```

## YouTube Authentication & Cookies

**Important: YouTube aggressively blocks cloud server IPs (Render, Railway, Vercel, AWS, etc.)** This is a known issue affecting all yt-dlp users on datacenter IPs. Even with valid cookies, success rate is approximately 40-60% on cloud servers.

### Best Practices for Cloud Deployment:

1. **Export FRESH cookies from an INCOGNITO/PRIVATE window**
   - Log into YouTube in a new incognito window
   - Use a browser extension like "Get cookies.txt LOCALLY"
   - Export cookies as Netscape format `.txt` file
   - Incognito cookies work better because they have no tracking history
   
2. **Upload cookies frequently**
   - Use the green COOKIES button in the app
   - Re-export and re-upload when downloads start failing
   - YouTube cookies expire faster on server IPs

3. **Expect some failures**
   - Cloud servers have ~50% success rate with YouTube
   - Some videos may never work on server IPs
   - Try different videos if one fails repeatedly

4. **For better reliability** (if possible):
   - Run the backend locally on your computer for 100% success rate
   - Use residential proxy service if available
   - Some VPS providers have better IP reputation than others

## Troubleshooting

### "Authentication Failed" Error
- Your YouTube cookies may be expired
- Export fresh cookies from a logged-in YouTube session
- Upload via the COOKIES button in the app

### "Format Not Available" Error
- Some videos have restricted formats
- Try a different video or upload fresh cookies

### Backend Not Reachable
- Verify `VITE_BACKEND_URL` is set correctly (no trailing slash)
- Redeploy Vercel after setting the environment variable
