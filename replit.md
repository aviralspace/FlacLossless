# FlacLossless (SonicPulse AI)

## Overview

FlacLossless is an AI-powered, studio-grade music player with advanced audio processing capabilities. It combines a React/TypeScript frontend with a Python Flask backend to deliver high-fidelity audio playback, real-time visualizations, and intelligent audio manipulation. The application supports YouTube audio extraction, Spotify integration, and professional-grade audio effects processing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- React 19.2.0 with TypeScript
- Vite 6.2.0 for build tooling and development server
- Tailwind CSS 4.1.17 for styling
- Web Audio API for real-time audio processing

**Design Pattern:**
The frontend follows a component-based architecture with service-oriented business logic separation. Audio processing is handled entirely client-side using the Web Audio API, while media sourcing is delegated to the backend.

**Key Architectural Decisions:**

1. **Client-Side Audio Graph**: All audio effects (EQ, reverb, stereo widening, compression) run in the browser using Web Audio API nodes. This allows real-time, zero-latency audio manipulation without server round-trips.

2. **Service Layer Abstraction**: Business logic is separated into dedicated services (`audioGraph.ts`, `backendService.ts`, `youtubeService.ts`, etc.) to keep components focused on UI concerns.

3. **Progressive Web App (PWA)**: Service worker registration enables offline capabilities and app-like experience on mobile devices.

4. **Real-Time Visualization**: Audio analysis runs on AnimationFrame loops with throttling to maintain 60fps performance while rendering complex visualizations (particles, shockwaves, frequency bars).

### Backend Architecture

**Technology Stack:**
- Python 3.11 with Flask 3.0.0
- yt-dlp 2025.1.26 for YouTube audio extraction
- FFmpeg for audio format conversion
- Server-Sent Events (SSE) for real-time progress streaming

**Design Pattern:**
Job-based processing with SSE for real-time progress updates. The backend acts as a proxy/cache layer between the frontend and YouTube.

**Key Architectural Decisions:**

1. **Job Queue System**: Download requests create jobs that are processed asynchronously. This prevents timeout issues on slow networks and allows progress tracking.

2. **File-Based Caching**: Downloaded MP3 files are cached on disk with JSON metadata. Cache entries include video ID mapping to avoid re-downloading the same content.

3. **Cookie-Based Authentication**: YouTube cookies can be uploaded to bypass bot detection. The system checks multiple locations (environment variables, file paths) for cookie files.

4. **Server-Sent Events (SSE)**: Real-time progress updates stream from backend to frontend without polling. This provides responsive UI feedback during lengthy downloads.

5. **Cleanup Strategy**: Automatic file cleanup after 24 hours (configurable) prevents disk space exhaustion while maintaining short-term cache benefits.

### Data Flow

**Audio Playback Pipeline:**
```
User Input → YouTube Search (Backend) → yt-dlp Download → MP3 Conversion → 
File Cache → Stream URL → HTML Audio Element → Web Audio Graph → 
10-Band EQ → Vocal Filter → Reverb → Stereo Width → Limiter → Output
```

**AI EQ Generation:**
```
User Prompt + Track Metadata + Audio Analysis → Gemini API → 
JSON Response → Parse Gains → Apply to Audio Graph
```

### External Dependencies

**Third-Party APIs:**

1. **Google Gemini API** (`@google/genai` 1.30.0)
   - Purpose: AI-powered EQ preset generation and voice control
   - Integration: Direct API calls from frontend service layer
   - Authentication: API key via environment variable (`GEMINI_API_KEY`)
   - Features Used: Function calling for audio controls, content generation for EQ suggestions

2. **Spotify Web API** (Optional)
   - Purpose: Playlist import and track search
   - Integration: OAuth2 client credentials flow
   - Authentication: Client ID/Secret via environment variables
   - Rationale: Provides legal music discovery without storing copyrighted content

3. **YouTube** (via yt-dlp backend)
   - Purpose: Audio extraction from YouTube videos
   - Integration: Backend service using yt-dlp library
   - Authentication: Optional cookie-based authentication for bot detection bypass
   - Rationale: yt-dlp handles complex YouTube extraction logic, format negotiation, and DASH manifest parsing

**Backend Services:**

1. **Flask Backend** (Self-Hosted)
   - Deployment: Railway.app, Render, or local server
   - Communication: REST API + Server-Sent Events
   - Endpoints: `/download`, `/stream`, `/metadata`, `/search`, `/cookies`
   - Rationale: Isolated server-side processing prevents CORS issues and keeps API keys secure

**System Libraries:**

1. **FFmpeg**
   - Purpose: Audio format conversion (WebM/M4A → MP3)
   - Integration: System-level dependency invoked by yt-dlp
   - Requirement: Must be installed on backend host

**Audio Processing:**

1. **Web Audio API** (Browser Native)
   - Purpose: Real-time audio effects and analysis
   - Nodes Used: BiquadFilter (EQ), ConvolverNode (reverb), DynamicsCompressor (limiter), AnalyserNode (visualization)
   - Rationale: Hardware-accelerated, low-latency processing without external dependencies

**Progressive Web App:**

1. **Service Worker API** (Browser Native)
   - Purpose: Offline caching and PWA functionality
   - Implementation: Custom service worker registration in `serviceWorkerRegistration.ts`

**Build & Development:**

1. **Vite Development Server**
   - Purpose: HMR, TypeScript compilation, proxy configuration
   - Proxy Setup: Routes `/api`, `/download`, `/stream` requests to backend (port 3001)
   - Rationale: Enables seamless local development with separate frontend/backend servers

**Deployment Architecture:**

- Frontend: Vercel (static site hosting)
- Backend: Railway.app/Render (containerized Python server)
- Communication: CORS-enabled REST API with environment-based URL configuration
- Environment Variables: `VITE_BACKEND_URL` points frontend to deployed backend