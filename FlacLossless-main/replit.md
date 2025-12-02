# SonicPulse ULTRA (FlacLossless)

## Overview
SonicPulse ULTRA is an AI-powered music player with studio-grade audio processing, real-time visualizations, and intelligent EQ generation. Built with React, TypeScript, and Vite.

## Recent Changes (December 2025)
- Fixed YouTube download issues by removing cookies from default yt-dlp options
- Changed format selection from 'best' to 'bestaudio/best' for better audio extraction
- Added ffmpeg_location to yt-dlp options for proper audio conversion
- Fixed HLS download handling (mp4 to mp3 conversion)
- Backend now runs on port 3001, frontend on port 5000 (Vite proxy configured)

## Project Structure
```
├── backend/             # Python Flask backend
│   ├── server.py        # yt-dlp download server
│   ├── requirements.txt # Python dependencies
│   └── audio/           # Downloaded audio files (generated)
├── components/          # React components
│   ├── DownloadProgress.tsx  # Download progress UI
│   ├── Equalizer.tsx    # 10-band parametric equalizer
│   ├── PlayerControls.tsx # Playback controls
│   ├── Playlist.tsx     # Track playlist management
│   ├── StreamingSource.tsx # Spotify/YouTube integration
│   ├── Visualizer.tsx   # Audio visualizer
│   └── YouTubePlayer.tsx # YouTube fallback player
├── services/            # Business logic services
│   ├── audioGraph.ts    # Web Audio API processing
│   ├── backendService.ts # Backend API client
│   ├── downloadJobService.ts # Download job management
│   ├── geminiService.ts # AI EQ generation
│   ├── liveService.ts   # Voice control
│   ├── spotifyService.ts # Spotify API integration
│   └── youtubeService.ts # YouTube API integration
├── App.tsx              # Main application component
├── constants.ts         # App constants and presets
├── types.ts             # TypeScript interfaces
├── index.tsx            # React entry point
├── index.html           # HTML template
├── index.css            # Global styles
├── vite.config.ts       # Vite configuration
├── youtube_cookies.txt  # YouTube cookies (template)
└── package.json         # npm dependencies
```

## Running the App
- Frontend: `npm run dev` (runs on port 5000)
- Backend: `cd backend && python server.py` (runs on port 3001)
- Build: `npm run build`
- Preview: `npm run preview`

Note: The Vite dev server proxies API requests from port 5000 to the backend on port 3001.

## Environment Variables
- `GEMINI_API_KEY` - Required for AI-powered EQ generation
- `VITE_SPOTIFY_CLIENT_ID` - Optional, for Spotify integration
- `VITE_YOUTUBE_API_KEY` - Optional, for YouTube integration

## Key Features
- 10-band parametric equalizer with presets
- AI-powered EQ preset generation via Gemini
- Real-time audio visualization
- Spotify and YouTube playlist integration
- Local audio file playback (FLAC, MP3, WAV)
- Voice control capabilities
- PWA support for installation

## Tech Stack
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Web Audio API
- Google Gemini AI

## Deployment
Static deployment configured with `npm run build` outputting to `dist/` directory.
