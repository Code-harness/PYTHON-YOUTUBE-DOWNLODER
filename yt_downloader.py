# yt_downloader.py
import os
import re
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs


class DownloadCancelled(Exception):
    """Raised when the user cancels the download."""
    pass


# Quality label -> max height cap (None = uncapped / best available, up to 8K)
QUALITY_PRESETS = {
    "Best Available": None,
    "4K (2160p)": 2160,
    "1440p (QHD)": 1440,
    "1080p (FHD)": 1080,
    "720p (HD)": 720,
    "480p": 480,
}


def clean_youtube_url(url: str) -> str:
    """
    Clean and normalize YouTube URLs while preserving playlist info if present.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    if 'v' in qs and 'list' in qs:
        return f"https://www.youtube.com/watch?v={qs['v'][0]}&list={qs['list'][0]}"
    elif 'list' in qs:
        return f"https://www.youtube.com/playlist?list={qs['list'][0]}"
    elif 'v' in qs:
        return f"https://www.youtube.com/watch?v={qs['v'][0]}"

    return url.strip()


def is_valid_youtube_url(url: str) -> bool:
    """
    Basic sanity check that the string looks like a YouTube URL.
    """
    if not url:
        return False
    pattern = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+'
    return bool(re.match(pattern, url.strip(), re.IGNORECASE))


def is_playlist_url(url: str) -> bool:
    """
    Detect whether a URL points to a playlist or a video inside a playlist.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return 'list' in qs or 'playlist' in parsed.path.lower()


def format_speed(speed):
    """
    Convert raw bytes/sec into readable speed text.
    """
    if not speed:
        return "0 KB/s"

    speed = float(speed)
    for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if speed < 1024:
            return f"{speed:.1f} {unit}"
        speed /= 1024

    return f"{speed:.1f} TB/s"


def format_eta(seconds):
    """
    Convert ETA seconds into HH:MM:SS or MM:SS format.
    """
    if seconds is None:
        return "--:--"

    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)

    if hrs > 0:
        return f"{hrs:02}:{mins:02}:{secs:02}"
    return f"{mins:02}:{secs:02}"


def format_filesize(num_bytes):
    """
    Convert raw byte count into readable size text.
    """
    if not num_bytes:
        return "--"
    num_bytes = float(num_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def get_video_info(url: str):
    """
    Fetch lightweight video/playlist metadata without downloading.
    Much faster for previews.
    """
    url = clean_youtube_url(url)

    options = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': 'in_playlist',  # faster for playlists
        'ignoreerrors': True,
    }

    with YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def get_fast_title(url: str):
    """
    Get a fast title/playlist label for UI without doing deep extraction.
    """
    try:
        info = get_video_info(url)

        if not info:
            return "Unknown"

        if info.get('_type') == 'playlist':
            title = info.get('title', 'Unknown Playlist')
            count = len(info.get('entries', []) or [])
            return f"Playlist: {title} ({count} videos)"

        return info.get('title', 'Unknown Video')

    except Exception:
        return "Loading..."


def _build_format_string(quality: str) -> str:
    """
    Build a yt-dlp format selector that actually grabs the best available
    resolution rather than being hard-capped at 1080p.

    Key fix: the old selector forced ext=mp4 on the video stream, which on
    YouTube silently throws away the true best quality (4K/1440p and most
    modern high-bitrate streams are served as VP9/AV1 in a WebM container,
    not H.264/mp4). We now select on resolution only and let
    merge_output_format handle remuxing to mp4 afterward.
    """
    max_height = QUALITY_PRESETS.get(quality, None)

    if max_height:
        return (
            f'bestvideo[height<={max_height}]+bestaudio/'
            f'best[height<={max_height}]'
        )

    # No cap -> true best available, including 4K/8K sources
    return 'bestvideo+bestaudio/best'


def download_video(
    url,
    folder,
    progress_callback=None,
    mode="playlist",
    cancel_flag=None,
    title_callback=None,
    log_callback=None,
    quality="Best Available",
):
    """
    Download YouTube content.

    Parameters:
    - url: YouTube video or playlist URL
    - folder: destination folder
    - progress_callback: function(progress_dict)
    - mode: 'playlist' or 'single'
    - cancel_flag: function() -> bool, returns True if download should stop
    - title_callback: function(title: str), updates current title
    - log_callback: function(message: str), sends log messages to UI
    - quality: one of QUALITY_PRESETS keys, controls max resolution
    """
    url = clean_youtube_url(url)

    if not url:
        raise ValueError("No URL provided")

    if not is_valid_youtube_url(url):
        raise ValueError("That doesn't look like a valid YouTube URL")

    playlist_detected = is_playlist_url(url)

    # Output template and playlist behavior
    if mode == "playlist":
        outtmpl = (
            os.path.join(folder, '%(playlist_title)s', '%(playlist_index)02d - %(title)s.%(ext)s')
            if playlist_detected
            else os.path.join(folder, '%(title)s.%(ext)s')
        )
        noplaylist = False if playlist_detected else True

    elif mode == "single":
        outtmpl = os.path.join(folder, '%(title)s.%(ext)s')
        noplaylist = True

    else:
        raise ValueError("Invalid mode. Use 'playlist' or 'single'.")

    # Hook wrapper
    def hook(d):
        if cancel_flag and cancel_flag():
            raise DownloadCancelled("Download cancelled by user")

        if progress_callback:
            progress_callback(d)

    # Custom logger for GUI output
    class Logger:
        def debug(self, msg):
            if log_callback and msg.strip():
                log_callback(msg)

        def warning(self, msg):
            if log_callback and msg.strip():
                log_callback(f"WARNING: {msg}")

        def error(self, msg):
            if log_callback and msg.strip():
                log_callback(f"ERROR: {msg}")

    format_string = _build_format_string(quality)

    options = {
        'format': format_string,
        # Prefer the highest resolution / best codec available; mp4 is only
        # used as a final tiebreaker so we don't discard higher-quality
        # webm/av1 streams the way a hard ext=mp4 filter would.
        'format_sort': ['res', 'fps', 'hdr:12', 'codec:vp9.2', 'codec:av01', 'br'],
        'merge_output_format': 'mp4',
        'outtmpl': outtmpl,
        'noplaylist': noplaylist,
        'quiet': True,
        'ignoreerrors': True,
        'progress_hooks': [hook],
        'logger': Logger(),
        'concurrent_fragment_downloads': 4,
        'retries': 10,
        'fragment_retries': 10,
    }

    # Fast title preview only (lightweight)
    if title_callback:
        title_callback(get_fast_title(url))

    with YoutubeDL(options) as ydl:
        ydl.download([url])