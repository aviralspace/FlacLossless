# Quick Reference: YouTube Cookies Authentication

## TL;DR - The Error & The Fix

**Problem:**
```
ERROR: [youtube] TeMKcpRYfEA: Sign in to confirm you're not a bot
```

**Solution:** Upload your YouTube cookies file to the app

---

## Quick Start

### 1. Export YouTube Cookies (5 minutes)

**Chrome:**
1. Install [Get cookies.txt extension](https://chrome.google.com/webstore/detail/get-cookiestxt-locally)
2. Go to youtube.com and login
3. Click extension → "Export" → Save `youtube_cookies.txt`

**Firefox:**
1. Install [Get cookies.txt extension](https://addons.mozilla.org/firefox)
2. Go to youtube.com and login
3. Click extension → "Export" → Save `youtube_cookies.txt`

### 2. Upload to FlacLossless

- Click "Upload Cookies" in the app
- Select your `youtube_cookies.txt` file
- Done! ✓

### 3. Download Music

- Search for a YouTube video
- Click download
- It will now work without authentication errors

---

## What Changed in Your App

### Backend (`backend/server.py`)
- ✅ Added cookie upload endpoint: `POST /cookies`
- ✅ Added cookie status endpoint: `GET /cookies`
- ✅ Auto-detects cookies from `./youtube_cookies.txt`
- ✅ Better error messages for auth failures

### Frontend (`services/backendService.ts`)
- ✅ Added `uploadCookies()` method
- ✅ Added `checkCookies()` method

### New Components
- ✅ `CookieUpload.tsx` - Upload UI
- ✅ `DownloadError.tsx` - Error modal with retry
- ✅ `CookiesIntegrationExample.tsx` - Example code

### Documentation
- 📄 `COOKIES_SETUP.md` - Complete guide
- 📄 `IMPLEMENTATION_SUMMARY.md` - Technical details
- 📄 `COOKIES_CHANGELOG.md` - All changes
- 📄 This file - Quick reference

---

## API Endpoints

### Check Cookies Status
```bash
curl http://localhost:5000/cookies
```
Response:
```json
{
  "has_cookies": true,
  "path": "./youtube_cookies.txt",
  "file_size": 2900
}
```

### Upload Cookies File
```bash
curl -F "file=@youtube_cookies.txt" http://localhost:5000/cookies
```
Response:
```json
{
  "success": true,
  "message": "Cookies file uploaded successfully"
}
```

---

## Using in Your Code

### Check if cookies available
```typescript
const status = await backendService.checkCookies();
if (status.has_cookies) {
  console.log('Ready to download!');
}
```

### Upload cookies
```typescript
const file = fileInputElement.files[0];
const result = await backendService.uploadCookies(file);
console.log(result.message);
```

### Show cookie upload UI
```tsx
import CookieUpload from '@/components/CookieUpload';

<CookieUpload 
  onSuccess={() => console.log('Cookies uploaded!')}
  onError={(err) => console.error(err)}
/>
```

### Show error with retry
```tsx
import DownloadError from '@/components/DownloadError';

{error && (
  <DownloadError
    error={error}
    videoTitle="My Video"
    onRetry={handleRetry}
    onDismiss={handleDismiss}
  />
)}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid cookies file" | Export a fresh file from YouTube |
| "Still getting bot error" | Your cookies may have expired, export new ones |
| "File upload button not working" | Make sure you're using Chrome or Firefox |
| "Can't find cookies.txt" | Use extension → Export, don't manually create |

---

## File Locations

```
/workspaces/FlacLossless/
├── youtube_cookies.txt          ← Your cookies (pre-loaded)
├── backend/server.py            ← Backend changes
├── services/backendService.ts   ← Frontend service changes
├── components/
│   ├── CookieUpload.tsx         ← Upload component (NEW)
│   └── DownloadError.tsx        ← Error modal (NEW)
├── COOKIES_SETUP.md             ← Full guide
├── IMPLEMENTATION_SUMMARY.md    ← Technical details
└── COOKIES_CHANGELOG.md         ← All changes
```

---

## Security Tips

⚠️ Treat cookies like passwords
- Don't share your cookies file
- Use a separate YouTube account if possible
- Delete old cookies files after uploading
- Cookies expire in ~6 months (YouTube's policy)

---

## Next Steps

1. ✓ Understand the error (authentication required)
2. ✓ Export YouTube cookies (5 minutes)
3. ✓ Upload to FlacLossless (1 minute)
4. ✓ Start downloading (profit!)

---

## Support

- Full guide: See `COOKIES_SETUP.md`
- Technical details: See `IMPLEMENTATION_SUMMARY.md`
- All changes: See `COOKIES_CHANGELOG.md`

---

**Version:** 1.0
**Date:** December 2, 2025
**Status:** ✅ Ready to use
