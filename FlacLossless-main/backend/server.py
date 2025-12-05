"""
FlacLossless Backend: yt-dlp Job Manager with SSE Progress Streaming
Downloads audio from YouTube with real-time progress updates via Server-Sent Events.
"""

from flask import Flask, request, send_file, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import uuid
import json
import threading
import time
from pathlib import Path
import shutil
from datetime import datetime, timedelta
import logging
import re
from queue import Queue
from typing import Dict, Optional, Any
import tempfile
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)

AUDIO_DIR = os.path.abspath(os.getenv('AUDIO_DIR', './audio'))
CACHE_FILE = os.getenv('CACHE_FILE', './cache.json')
CLEANUP_HOURS = int(os.getenv('CLEANUP_HOURS', 24))
MAX_CONCURRENT_JOBS = 3

Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)

cache = load_cache()

def get_youtube_cookies():
    """
    Get cookie file path for yt-dlp authentication.
    Called on each request to pick up newly added cookie files.
    Returns cookie file path or None if unavailable.
    """
    try:
        cookie_file = os.getenv('YT_COOKIES_FILE')
        if cookie_file and os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                content = ''

            # Accept plain text (contains youtube) or JSON cookie exports
            lower = content.lower()
            if 'youtube' in lower and 'your_login_here' not in lower:
                logger.info(f"Using cookies from file: {cookie_file}")
                return cookie_file
            # Try parsing JSON cookie exports
            try:
                parsed = json.loads(content)
                # parsed could be a dict with list of cookies
                items = []
                if isinstance(parsed, dict):
                    # common formats: { cookies: [...] } or top-level list under some key
                    if 'cookies' in parsed and isinstance(parsed['cookies'], list):
                        items = parsed['cookies']
                    else:
                        # if dict looks like a single cookie, treat as single
                        items = [parsed]
                elif isinstance(parsed, list):
                    items = parsed

                for it in items:
                    domain = ''
                    if isinstance(it, dict):
                        domain = str(it.get('domain', '') or it.get('host', '')).lower()
                    if 'youtube' in domain:
                        logger.info(f"Using JSON-format cookies from file: {cookie_file}")
                        return cookie_file
            except Exception:
                pass
        
        default_paths = [
            './youtube_cookies.txt',
            '../youtube_cookies.txt',
            os.path.join(AUDIO_DIR, 'youtube_cookies.txt'),
            os.path.expanduser('~/youtube_cookies.txt'),
            './www.youtube.com_cookies (1).txt',
            '../www.youtube.com_cookies (1).txt',
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lower = content.lower()
                        if 'youtube' in lower and 'your_login_here' not in lower:
                            logger.info(f"Found valid cookies file at: {path}")
                            return path
                        # Try JSON parse for cookie-exporters that save JSON
                        try:
                            parsed = json.loads(content)
                            items = parsed if isinstance(parsed, list) else parsed.get('cookies', []) if isinstance(parsed, dict) else []
                            for it in items:
                                domain = ''
                                if isinstance(it, dict):
                                    domain = str(it.get('domain', '') or it.get('host', '')).lower()
                                if 'youtube' in domain:
                                    logger.info(f"Found JSON-format cookies file at: {path}")
                                    return path
                        except Exception:
                            pass
                except Exception:
                    continue
        
        return None
            
    except Exception as e:
        logger.warning(f"Cookie extraction failed: {e}")
        return None

class DownloadJob:
    def __init__(self, job_id: str, video_id: str, url: str, title: str = ""):
        self.job_id = job_id
        self.video_id = video_id
        self.url = url
        self.title = title
        self.status = "queued"
        self.progress = 0
        self.stage = "Waiting..."
        self.error: Optional[str] = None
        self.stream_url: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.subscribers: list = []
        self.file_path: Optional[str] = None
        
    def to_dict(self):
        return {
            "job_id": self.job_id,
            "video_id": self.video_id,
            "url": self.url,
            "title": self.title,
            "status": self.status,
            "progress": self.progress,
            "stage": self.stage,
            "error": self.error,
            "stream_url": self.stream_url,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    def notify_subscribers(self):
        event_data = json.dumps(self.to_dict())
        for q in self.subscribers:
            try:
                q.put(event_data)
            except:
                pass

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, DownloadJob] = {}
        self.active_count = 0
        self.lock = threading.Lock()
        self.job_queue = Queue()
        for _ in range(MAX_CONCURRENT_JOBS):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
    
    def create_job(self, video_id: str, url: str, title: str = "") -> DownloadJob:
        with self.lock:
            if video_id in cache:
                cached_entry = cache[video_id]
                file_path = cached_entry.get('file', '')
                if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    job = DownloadJob(str(uuid.uuid4()), video_id, url, title)
                    job.status = "completed"
                    job.progress = 100
                    job.stage = "Loaded from cache"
                    job.stream_url = f"/stream/{os.path.basename(file_path)}"
                    job.metadata = cached_entry.get('metadata', {})
                    job.file_path = file_path
                    self.jobs[job.job_id] = job
                    return job
            
            job = DownloadJob(str(uuid.uuid4()), video_id, url, title)
            self.jobs[job.job_id] = job
            self.job_queue.put(job.job_id)
            return job
    
    def get_job(self, job_id: str) -> Optional[DownloadJob]:
        return self.jobs.get(job_id)
    
    def _worker(self):
        while True:
            try:
                job_id = self.job_queue.get()
                job = self.jobs.get(job_id)
                if job and job.status == "queued":
                    self._process_job(job)
            except Exception as e:
                logger.error(f"Worker error: {e}")
            finally:
                self.job_queue.task_done()
    
    def _process_job(self, job: DownloadJob):
        try:
            job.status = "downloading"
            job.stage = "Starting download..."
            job.progress = 5
            job.notify_subscribers()
            
            file_id = str(uuid.uuid4())
            output_template = os.path.join(AUDIO_DIR, f"{file_id}.%(ext)s")
            output_path = os.path.join(AUDIO_DIR, f"{file_id}.mp3")
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        pct = int((downloaded / total) * 60) + 10
                        job.progress = min(pct, 70)
                    else:
                        job.progress = min(job.progress + 1, 70)
                    
                    speed = d.get('speed', 0)
                    if speed:
                        speed_str = f"{speed/1024:.1f} KB/s" if speed < 1024*1024 else f"{speed/1024/1024:.1f} MB/s"
                        job.stage = f"Downloading... ({speed_str})"
                    else:
                        job.stage = "Downloading..."
                    job.notify_subscribers()
                    
                elif d['status'] == 'finished':
                    job.progress = 75
                    job.stage = "Converting to MP3..."
                    job.notify_subscribers()
            
            ffmpeg_location = shutil.which('ffmpeg') or '/home/runner/.nix-profile/bin/ffmpeg'
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'geo_bypass_country': 'US',
                'noplaylist': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'player_skip': ['configs'],
                    }
                },
                'source_address': '0.0.0.0',
                'socket_timeout': 30,
                'retries': 5,
                'fragment_retries': 5,
                'skip_unavailable_fragments': True,
                'ffmpeg_location': os.path.dirname(ffmpeg_location),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                },
            }
            
            job.stage = "Fetching video info..."
            job.progress = 10
            job.notify_subscribers()
            
            success = False
            last_error = None
            
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            ydl_opts['progress_hooks'] = [progress_hook]
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(job.url, download=True)
                    job.metadata = {
                        'title': info.get('title', job.title or 'Unknown'),
                        'duration': info.get('duration', 0),
                        'thumbnail': info.get('thumbnail', ''),
                        'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                    }
                    job.title = job.metadata['title']
                    success = True
                    logger.info(f"Download successful with MP3 conversion")
            except Exception as e1:
                logger.warning(f"MP3 conversion failed: {e1}")
                last_error = e1
            
            if not success:
                logger.info("Trying raw audio download without postprocessor...")
                ydl_opts['postprocessors'] = []
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(job.url, download=True)
                        job.metadata = {
                            'title': info.get('title', job.title or 'Unknown'),
                            'duration': info.get('duration', 0),
                            'thumbnail': info.get('thumbnail', ''),
                            'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                        }
                        job.title = job.metadata['title']
                        success = True
                        logger.info(f"Raw audio download successful (no conversion)")
                except Exception as e2:
                    logger.warning(f"Raw audio download failed: {e2}")
                    last_error = e2
            
            if not success:
                error_msg = str(last_error).lower() if last_error else ""
                
                if 'sign in' in error_msg or 'bot' in error_msg or 'authentication' in error_msg:
                    # Try multiple player clients to maximize success rate
                    client_attempts = [
                        {
                            'name': 'android_embedded',
                            'clients': ['android_embedded', 'android', 'web'],
                            'ua': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
                        },
                        {
                            'name': 'mweb',
                            'clients': ['mweb', 'android', 'web'],
                            'ua': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
                        }
                    ]
                    
                    for attempt in client_attempts:
                        if success:
                            break
                        logger.info(f"Auth error detected, trying {attempt['name']} client...")
                        ydl_opts['extractor_args'] = {
                            'youtube': {
                                'player_client': attempt['clients'],
                                'player_skip': ['configs', 'webpage'],
                            }
                        }
                        ydl_opts['http_headers']['User-Agent'] = attempt['ua']
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                        try:
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(job.url, download=True)
                                job.metadata = {
                                    'title': info.get('title', job.title or 'Unknown'),
                                    'duration': info.get('duration', 0),
                                    'thumbnail': info.get('thumbnail', ''),
                                    'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                                }
                                job.title = job.metadata['title']
                                success = True
                                logger.info(f"Download successful with {attempt['name']} client")
                        except Exception as e_client:
                            logger.warning(f"{attempt['name']} client failed: {e_client}")
                            last_error = e_client
                    
                    if not success:
                        cookies_file = get_youtube_cookies()
                        if cookies_file:
                            logger.info(f"Trying with cookies as last resort: {cookies_file}")
                            ydl_opts['cookiefile'] = cookies_file
                            try:
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    info = ydl.extract_info(job.url, download=True)
                                    job.metadata = {
                                        'title': info.get('title', job.title or 'Unknown'),
                                        'duration': info.get('duration', 0),
                                        'thumbnail': info.get('thumbnail', ''),
                                        'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                                    }
                                    job.title = job.metadata['title']
                                    success = True
                                    logger.info(f"Download successful with cookies")
                            except Exception as e_cookies:
                                logger.warning(f"Cookies download failed: {e_cookies}")
                                last_error = e_cookies
                
                if not success and ('format' in error_msg or 'no formats' in error_msg or 'requested format' in error_msg):
                    logger.warning(f"Format error, trying fallback formats...")
                    
                    ydl_opts_fallback = ydl_opts.copy()
                    ydl_opts_fallback['postprocessors'] = []
                    
                    fallback_formats = ['bestaudio', 'best', 'worstaudio', 'worst']
                    
                    for fmt in fallback_formats:
                        try:
                            logger.info(f"Trying format fallback: {fmt}")
                            ydl_opts_fallback['format'] = fmt
                            with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                                info = ydl.extract_info(job.url, download=True)
                                job.metadata = {
                                    'title': info.get('title', job.title or 'Unknown'),
                                    'duration': info.get('duration', 0),
                                    'thumbnail': info.get('thumbnail', ''),
                                    'uploader': info.get('uploader', info.get('channel', 'Unknown')),
                                }
                                job.title = job.metadata['title']
                                logger.info(f"Format fallback ({fmt}) successful!")
                                success = True
                                break
                        except Exception as fb_error:
                            logger.warning(f"Format fallback ({fmt}) failed: {fb_error}")
                            last_error = fb_error
                            continue
                    
                    if not success and last_error:
                        raise last_error
                elif not success and last_error:
                    raise last_error
            
            job.progress = 85
            job.stage = "Finalizing..."
            job.notify_subscribers()
            
            # Debug: List all files in audio dir
            logger.info(f"Files in {AUDIO_DIR}: {os.listdir(AUDIO_DIR) if os.path.exists(AUDIO_DIR) else 'DIR NOT FOUND'}")
            logger.info(f"Looking for output file: {output_path}")
            logger.info(f"Output path exists: {os.path.exists(output_path)}")
            
            if not os.path.exists(output_path):
                logger.warning(f"Expected output file not found: {output_path}")
                logger.info(f"Searching for alternative audio files with file_id: {file_id}")
                
                for ext in ['mp3', 'm4a', 'mp4', 'webm', 'opus', 'ogg', 'wav', 'aac', 'flac']:
                    alt_path = os.path.join(AUDIO_DIR, f"{file_id}.{ext}")
                    logger.info(f"Checking for: {alt_path} - exists: {os.path.exists(alt_path)}")
                    
                    if os.path.exists(alt_path) and os.path.getsize(alt_path) > 0:
                        logger.info(f"Found audio file: {alt_path} (size: {os.path.getsize(alt_path)} bytes)")
                        if ext != 'mp3':
                            logger.info(f"Converting {ext} to MP3...")
                            try:
                                import subprocess
                                result = subprocess.run(
                                    ['ffmpeg', '-i', alt_path, '-acodec', 'libmp3lame', '-q:a', '2', '-y', output_path],
                                    capture_output=True, timeout=120, text=True
                                )
                                if result.returncode == 0:
                                    logger.info(f"Conversion successful")
                                    os.remove(alt_path)
                                else:
                                    logger.error(f"FFmpeg conversion failed: {result.stderr}")
                            except Exception as conv_err:
                                logger.error(f"Conversion error: {conv_err}")
                        else:
                            output_path = alt_path
                            logger.info(f"File is already MP3, using it directly")
                        break
            
            logger.info(f"Final check - output file exists: {os.path.exists(output_path)}")
            if os.path.exists(output_path):
                logger.info(f"Final output file size: {os.path.getsize(output_path)} bytes")
            
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise Exception("Download failed - no output file created")
            
            cache[job.video_id] = {
                'file': output_path,
                'metadata': job.metadata,
                'downloaded_at': datetime.now().isoformat(),
                'file_id': file_id
            }
            save_cache(cache)
            
            job.file_path = output_path
            job.stream_url = f"/stream/{os.path.basename(output_path)}"
            job.progress = 100
            job.stage = "Complete!"
            job.status = "completed"
            job.notify_subscribers()
            
            logger.info(f"Job {job.job_id} completed: {job.title}")
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Job {job.job_id} failed: {error_str}")
            
            # Check for authentication/cookie-related errors
            if any(keyword in error_str.lower() for keyword in [
                'sign in to confirm', 
                'bot', 
                'authentication',
                'unable to download',
                'youtube returned'
            ]):
                # Check if cookies are actually being used
                cookies_file = get_youtube_cookies()
                if cookies_file:
                    job.error = "YouTube is blocking this server's IP address. Try: 1) Export FRESH cookies from an incognito window while logged into YouTube, 2) Upload via the Cookies button, 3) Try a different video. Cloud servers have ~50% success rate with YouTube."
                else:
                    job.error = "YouTube is blocking this server. Upload fresh cookies from a logged-in YouTube session via the Cookies button. Export from incognito/private window for best results."
                job.stage = "Server Blocked"
            # Check for format-related errors - should be caught by fallback
            elif any(keyword in error_str.lower() for keyword in [
                'requested format is not available',
                'no formats found',
                'no matching format',
                'format not available'
            ]):
                job.error = "This video's format is not available. This often happens on cloud servers. Try a different video or upload fresh YouTube cookies."
                job.stage = "Format Unavailable"
            else:
                job.error = error_str
                job.stage = "Failed"
            
            job.status = "failed"
            job.notify_subscribers()

job_manager = JobManager()

def extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'v=([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'audio_dir': AUDIO_DIR,
        'cached_videos': len(cache),
        'active_jobs': len([j for j in job_manager.jobs.values() if j.status in ['queued', 'downloading']]),
        'yt_dlp_version': yt_dlp.version.__version__
    })


@app.route('/debug/test-video', methods=['GET'])
def debug_test_video():
    """Debug endpoint to test if a specific video works and what error it returns"""
    video_id = request.args.get('video_id', 'dQw4w9WgXcQ')  # Default: Rick Roll
    use_cookies = request.args.get('cookies', 'false').lower() == 'true'
    
    cookies_file = None
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
        }
        
        if use_cookies:
            cookies_file = get_youtube_cookies()
            if cookies_file:
                ydl_opts['cookiefile'] = cookies_file
                logger.info(f"Using cookies: {cookies_file}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('acodec') != 'none']
            return jsonify({
                'success': True,
                'video_id': video_id,
                'title': info.get('title'),
                'formats_available': len(formats),
                'audio_formats': len(audio_formats),
                'cookies_used': cookies_file is not None,
            })
    
    except Exception as e:
        error_msg = str(e)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': type(e).__name__,
            'cookies_used': cookies_file is not None,
            'is_auth_error': 'sign in' in error_msg.lower() or 'bot' in error_msg.lower(),
            'is_format_error': 'format' in error_msg.lower(),
        }), 400


@app.route('/cookies', methods=['POST'])
def upload_cookies():
    """Upload YouTube cookies file for authentication."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.txt'):
            return jsonify({'success': False, 'error': 'Only .txt files are allowed'}), 400
        
        # Save cookies file to parent directory (where it's being detected)
        cookies_path = os.path.join(os.path.dirname(AUDIO_DIR), 'youtube_cookies.txt')
        file.save(cookies_path)
        
        # Validate the file
        with open(cookies_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if 'youtube.com' not in content.lower():
                os.remove(cookies_path)
                return jsonify({'success': False, 'error': 'Invalid YouTube cookies file - must contain youtube.com cookies'}), 400
        
        logger.info(f"Cookies file uploaded successfully: {cookies_path}")
        
        return jsonify({
            'success': True,
            'message': 'Cookies file uploaded successfully',
            'path': cookies_path
        }), 200
    
    except Exception as e:
        logger.error(f"Cookies upload error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500


@app.route('/cookies', methods=['GET'])
def get_cookies_status():
    """Check if valid cookies are available."""
    try:
        cookies_file = get_youtube_cookies()
        if cookies_file and os.path.exists(cookies_file):
            return jsonify({
                'has_cookies': True,
                'path': cookies_file,
                'file_size': os.path.getsize(cookies_file)
            })
        else:
            return jsonify({
                'has_cookies': False,
                'path': None,
                'message': 'No valid YouTube cookies found. Please upload a cookies file.'
            })
    
    except Exception as e:
        logger.error(f"Cookies status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/search', methods=['GET'])
def search_youtube():
    query = request.args.get('q', '')
    max_results = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        logger.info(f"Searching YouTube for: {query}")
        
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'nocheckcertificate': True,
            'geo_bypass': True,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web', 'mweb'],
                    'skip': ['hls', 'dash'],
                }
            },
            'retries': 3,
        }
        
        cookies_file = get_youtube_cookies()
        if cookies_file:
            ydl_opts['cookiefile'] = cookies_file
        
        logger.info(f"yt-dlp version: {yt_dlp.version.__version__}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Attempting search: ytsearch{max_results}:{query}")
            result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
        
        logger.info(f"Search returned {len(result.get('entries', []))} results")
        
        videos = []
        for entry in result.get('entries', []):
            if entry:
                videos.append({
                    'id': entry.get('id', ''),
                    'title': entry.get('title', 'Unknown'),
                    'channelTitle': entry.get('uploader', entry.get('channel', 'Unknown')),
                    'thumbnail': entry.get('thumbnail', f"https://img.youtube.com/vi/{entry.get('id', '')}/mqdefault.jpg"),
                    'videoId': entry.get('id', ''),
                    'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                    'duration': entry.get('duration', 0),
                })
        
        logger.info(f"Returning {len(videos)} formatted videos")
        return jsonify({'results': videos})
    
    except Exception as e:
        logger.error(f"Search failed: {type(e).__name__}: {e}", exc_info=True)
        return jsonify({'error': str(e), 'results': []}), 500


@app.route('/jobs', methods=['POST'])
def create_download_job():
    data = request.get_json() or {}
    url = data.get('url', '')
    title = data.get('title', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    job = job_manager.create_job(video_id, url, title)
    
    return jsonify(job.to_dict())


@app.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job.to_dict())


@app.route('/jobs/<job_id>/events', methods=['GET'])
def job_events(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    def generate():
        q = Queue()
        job.subscribers.append(q)
        
        try:
            yield f"data: {json.dumps(job.to_dict())}\n\n"
            
            while True:
                try:
                    data = q.get(timeout=30)
                    yield f"data: {data}\n\n"
                    
                    event_data = json.loads(data)
                    if event_data.get('status') in ['completed', 'failed']:
                        break
                except:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
                    if job.status in ['completed', 'failed']:
                        break
        finally:
            if q in job.subscribers:
                job.subscribers.remove(q)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*',
        }
    )


@app.route('/download', methods=['GET', 'POST'])
def download_audio():
    url = request.args.get('url')
    if request.method == 'POST':
        data = request.get_json() or {}
        url = url or data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    if video_id in cache:
        cached_entry = cache[video_id]
        file_path = cached_entry.get('file', '')
        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return jsonify({
                'file': f"/stream/{os.path.basename(file_path)}",
                'metadata': cached_entry.get('metadata', {}),
                'cached': True,
                'video_id': video_id
            })
    
    job = job_manager.create_job(video_id, url, "")
    
    timeout = 180
    start = time.time()
    while job.status not in ['completed', 'failed'] and (time.time() - start) < timeout:
        time.sleep(0.5)
    
    if job.status == 'completed':
        return jsonify({
            'file': job.stream_url,
            'metadata': job.metadata,
            'cached': False,
            'video_id': video_id
        })
    else:
        return jsonify({'error': job.error or 'Download timed out'}), 500


@app.route('/stream/<filename>')
def stream_audio(filename):
    if '..' in filename or '/' in filename:
        return 'Forbidden', 403
    
    file_path = os.path.join(AUDIO_DIR, filename)
    
    if not os.path.exists(file_path):
        return 'Not Found', 404
    
    file_size = os.path.getsize(file_path)
    
    range_header = request.headers.get('Range')
    if range_header:
        try:
            byte_range = range_header.replace('bytes=', '').split('-')
            start = int(byte_range[0]) if byte_range[0] else 0
            end = int(byte_range[1]) if byte_range[1] else file_size - 1
            
            length = end - start + 1
            
            def generate():
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
            
            response = Response(
                generate(),
                status=206,
                mimetype='audio/mpeg',
                direct_passthrough=True
            )
            response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = length
            response.headers['Cache-Control'] = 'no-cache'
            return response
        except Exception as e:
            logger.warning(f"Range request error: {e}")
    
    response = send_file(file_path, mimetype='audio/mpeg')
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Length'] = file_size
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/metadata/<video_id>')
def get_metadata(video_id):
    if video_id not in cache:
        return jsonify({'error': 'Not in cache'}), 404
    
    entry = cache[video_id]
    return jsonify({
        'video_id': video_id,
        'metadata': entry.get('metadata', {}),
        'file': f"/stream/{os.path.basename(entry['file'])}",
        'downloaded_at': entry.get('downloaded_at')
    })


@app.route('/cache')
def list_cache():
    items = []
    for vid, entry in cache.items():
        items.append({
            'video_id': vid,
            'title': entry.get('metadata', {}).get('title', 'Unknown'),
            'downloaded_at': entry.get('downloaded_at'),
            'file_exists': os.path.exists(entry.get('file', ''))
        })
    return jsonify({'cached': len(items), 'items': items})


@app.route('/cache/<video_id>', methods=['DELETE'])
def delete_cached(video_id):
    if video_id not in cache:
        return jsonify({'error': 'Not found'}), 404
    
    entry = cache[video_id]
    file_path = entry.get('file')
    
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        del cache[video_id]
        save_cache(cache)
        return jsonify({'deleted': video_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def cleanup_worker():
    while True:
        try:
            time.sleep(3600)
            
            now = datetime.now()
            cutoff = now - timedelta(hours=CLEANUP_HOURS)
            deleted = 0
            
            for video_id, entry in list(cache.items()):
                try:
                    dl_time_str = entry.get('downloaded_at')
                    if dl_time_str:
                        dl_time = datetime.fromisoformat(dl_time_str)
                        if dl_time < cutoff:
                            file_path = entry.get('file')
                            if file_path and os.path.exists(file_path):
                                os.remove(file_path)
                            del cache[video_id]
                            deleted += 1
                except Exception as e:
                    logger.warning(f"Cleanup error for {video_id}: {e}")
            
            if deleted > 0:
                save_cache(cache)
                logger.info(f"Cleanup: deleted {deleted} old MP3(s)")
        
        except Exception as e:
            logger.error(f"Cleanup worker error: {e}")


cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
cleanup_thread.start()

# Note: When using Gunicorn, don't call app.run()
# Gunicorn will handle starting the server
if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    
    logger.info(f"FlacLossless Backend starting on 0.0.0.0:{port}")
    logger.info(f"Audio dir: {AUDIO_DIR}")
    logger.info(f"yt-dlp version: {yt_dlp.version.__version__}")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
