# YouTube Cookies Authentication Setup

## Overview

The FlacLossless application now includes automatic YouTube authentication support using cookies. This solves the "Sign in to confirm you're not a bot" error from yt-dlp.

## Implementation

### Backend Changes (`backend/server.py`)

1. **Cookies Management Endpoints:**
   - `POST /cookies` - Upload a new cookies file
   - `GET /cookies` - Check if cookies are available

2. **Enhanced Error Detection:**
   - The backend now detects authentication failures and returns user-friendly error messages
   - Distinguishes between authentication errors and other download failures

3. **Automatic Cookie Detection:**
   - The `get_youtube_cookies()` function checks multiple locations for cookies:
     1. Environment variable `YT_COOKIES_FILE`
     2. Default paths: `./youtube_cookies.txt`, `../youtube_cookies.txt`, `~/youtube_cookies.txt`
   - Returns valid YouTube cookies file path if found

### Frontend Changes

#### New Services (`services/backendService.ts`)

Added two new methods:

```typescript
// Upload cookies file to backend
async uploadCookies(file: File): Promise<{ success: boolean; message: string }>

// Check if cookies are available
async checkCookies(): Promise<{ has_cookies: boolean; path?: string; message?: string }>
```

#### New Components

1. **CookieUpload.tsx** - Standalone cookie upload component
   - File upload interface with drag-and-drop support
   - Validation and error handling
   - Instructions for exporting cookies

2. **DownloadError.tsx** - Error modal with cookie upload fallback
   - Detects authentication errors automatically
   - Provides option to upload cookies and retry
   - User-friendly error messages

## How to Export YouTube Cookies

### Method 1: Using Browser Extension (Recommended)

1. Install one of these extensions:
   - **Chrome:** [Get cookies.txt](https://chrome.google.com/webstore) or [EditThisCookie](https://chrome.google.com/webstore)
   - **Firefox:** [Get cookies.txt](https://addons.mozilla.org/firefox) or [EditThisCookie](https://addons.mozilla.org/firefox)

2. Visit [youtube.com](https://youtube.com) and ensure you're logged in

3. Click the extension icon and select "Export" or "Download as txt"

4. Save the file (e.g., `youtube_cookies.txt`)

5. Upload to FlacLossless app via the cookie upload dialog

### Method 2: Manual via DevTools

1. Open YouTube and login
2. Press `F12` to open DevTools
3. Go to Application → Cookies → youtube.com
4. Create a file with these essential cookies in Netscape format:
   ```
   .youtube.com	TRUE	/	TRUE	<timestamp>	LOGIN_INFO	<value>
   .youtube.com	TRUE	/	TRUE	<timestamp>	VISITOR_INFO1_LIVE	<value>
   ```

## Usage

### For Users

1. **First Time Setup:**
   - When you first try to download a YouTube video, if authentication is needed, you'll see a dialog
   - Click "Upload YouTube Cookies"
   - Select your cookies file and upload

2. **If Download Fails:**
   - An error dialog will appear if authentication is required
   - Follow the "Upload YouTube Cookies" link
   - Retry the download after uploading

### For Developers

#### Environment Variables

```bash
# Optional: Specify custom cookies file location
export YT_COOKIES_FILE=/path/to/youtube_cookies.txt
```

#### Testing Cookie Upload

```bash
curl -X POST -F "file=@youtube_cookies.txt" http://localhost:5000/cookies
```

#### Check Cookie Status

```bash
curl http://localhost:5000/cookies
```

## Features

✅ **Automatic Detection** - Backend automatically finds and uses cookies
✅ **Error Handling** - Clear messages when authentication is needed
✅ **User Upload** - Frontend UI for uploading new cookies
✅ **Retry Logic** - Users can retry downloads after uploading cookies
✅ **File Validation** - Only valid YouTube cookies are accepted
✅ **Multiple Locations** - Checks several default locations for cookies files

## Troubleshooting

### "Invalid YouTube cookies file" error

- Ensure the file is in Netscape format (usually exported by extensions automatically)
- The file must contain `.youtube.com` entries
- Download a fresh cookies file if the old one is expired

### Cookies expiry

- YouTube cookies typically expire after several months
- Export new cookies if downloads start failing with "Sign in to confirm" errors
- The app will prompt you to upload new cookies when needed

### Still getting authentication errors

1. Try logging out and back into YouTube
2. Clear browser cookies and cache
3. Export a fresh cookies file
4. Upload the new cookies to FlacLossless

## Security Note

Cookies files contain authentication tokens. Treat them like passwords:
- Don't share your cookies file
- Store in a secure location
- Re-export if you believe they've been compromised
- Consider using a separate YouTube account for downloading if privacy is a concern

## API Reference

### POST /cookies

Upload YouTube cookies file.

**Request:**
```
Content-Type: multipart/form-data
file: <.txt file>
```

**Response:**
```json
{
  "success": true,
  "message": "Cookies file uploaded successfully",
  "path": "/path/to/youtube_cookies.txt"
}
```

### GET /cookies

Check if cookies are available.

**Response:**
```json
{
  "has_cookies": true,
  "path": "/path/to/youtube_cookies.txt",
  "file_size": 2900
}
```

## Related Files

- Backend: `backend/server.py` - Cookie handling and yt-dlp integration
- Frontend: `services/backendService.ts` - API methods
- Components: `components/CookieUpload.tsx`, `components/DownloadError.tsx`
- Default cookies location: `./youtube_cookies.txt`
