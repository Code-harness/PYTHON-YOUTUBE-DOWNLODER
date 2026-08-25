import os
import re
import shutil
from urllib.parse import parse_qs, urlparse
from yt_dlp import YoutubeDL


class DownloadCancelled(Exception):
    """Raised when the user cancels the download."""

    pass


# Fallback resolution ladder, used only when a video's real format list
# can't be probed ahead of time (e.g. detection failed or was skipped).
QUALITY_PRESETS = {
    "Best Available": None,
    "4K (2160p)": 2160,
    "1440p (QHD)": 1440,
    "1080p (FHD)": 1080,
    "720p (HD)": 720,
    "480p": 480,
    "360p": 360,
}

# yt-dlp format-selector fragments for restricting to a codec family.
# H.264 is the safest default for compatibility; VP9/AV1 give smaller
# files at the same visual quality but need modern players/hardware.
CODEC_FILTERS = {
    "Auto": "",
    "H.264 (Best Compatibility)": "[vcodec^=avc1]",
    "VP9 (Balanced)": "[vcodec^=vp9]",
    "AV1 (Best Efficiency)": "[vcodec^=av01]",
}

AUDIO_FORMATS = ["mp3", "m4a", "opus", "wav", "flac"]
AUDIO_QUALITIES = ["320", "256", "192", "128"]
CONTAINERS = ["mp4", "mkv", "webm"]

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
}

# NOTE on player_client: we deliberately do NOT force a fixed client
# list for downloads anymore. YouTube now requires a PO Token (proof of
# origin) for ios/android clients to unlock their high-bitrate formats;
# without one those formats are silently skipped, which starves the
# format selector down to whatever the unauthenticated "web" client
# offers (often capped well below 1080p). Forcing a client list also
# disables yt-dlp's own adaptive client fallback, which the maintainers
# update frequently to track YouTube's changes. Leaving player_client
# unset lets yt-dlp pick its current best-working combination itself.
#
# If you still get low-quality results, the fix is authentication, not
# a different client list:
#   - cookies_from_browser (recommended): reuses your logged-in session,
#     which unlocks far more formats without needing a PO Token at all.
#   - po_token (advanced): manually supply a PO token if you have one,
#     see https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide
EXTRACTOR_ARGS_PROBE = {}


def _find_deno_path():
    """
    Locate a Deno binary even if the current process's PATH doesn't
    include it (common when the GUI is launched from a different shell
    session than the one where Deno was installed/PATH-exported).
    Returns an absolute path string, or None if not found anywhere.
    """
    found = shutil.which("deno")
    if found:
        return found

    common_locations = [
        os.path.expanduser("~/.deno/bin/deno"),
        "/usr/local/bin/deno",
        "/usr/bin/deno",
        "/opt/homebrew/bin/deno",
    ]
    for path in common_locations:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def _js_runtimes_option():
    """
    Build the js_runtimes option yt-dlp needs to decipher YouTube's
    signatures via Deno. Passing an explicit path means it works no
    matter which shell/environment launched this script.
    """
    deno_path = _find_deno_path()
    if deno_path:
        return {"deno": {"path": deno_path}}
    return {}


def clean_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    if "v" in qs and "list" in qs:
        return (
            f"https://www.youtube.com/watch?v={qs['v'][0]}&list={qs['list'][0]}"
        )
    elif "list" in qs:
        return f"https://www.youtube.com/playlist?list={qs['list'][0]}"
    elif "v" in qs:
        return f"https://www.youtube.com/watch?v={qs['v'][0]}"

    return url.strip()


def is_valid_youtube_url(url: str) -> bool:
    if not url:
        return False
    pattern = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/.+"
    return bool(re.match(pattern, url.strip(), re.IGNORECASE))


def is_playlist_url(url: str) -> bool:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    return "list" in qs or "playlist" in parsed.path.lower()


def format_speed(speed):
    if not speed:
        return "0 KB/s"
    speed = float(speed)
    for unit in ["B/s", "KB/s", "MB/s", "GB/s"]:
        if speed < 1024:
            return f"{speed:.1f} {unit}"
        speed /= 1024
    return f"{speed:.1f} TB/s"


def format_eta(seconds):
    if seconds is None:
        return "--:--"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    if hrs > 0:
        return f"{hrs:02}:{mins:02}:{secs:02}"
    return f"{mins:02}:{secs:02}"


def format_filesize(num_bytes):
    if not num_bytes:
        return "--"
    num_bytes = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def get_video_info(url: str):
    """Fetch metadata without downloading content."""
    url = clean_youtube_url(url)
    options = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "extractor_args": EXTRACTOR_ARGS_PROBE,
        "http_headers": COMMON_HEADERS,
        "js_runtimes": _js_runtimes_option(),
    }
    with YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=False)


def get_fast_title(url: str):
    try:
        info = get_video_info(url)
        if not info:
            return "Unknown"
        if info.get("_type") == "playlist":
            title = info.get("title", "Unknown Playlist")
            count = len(info.get("entries", []) or [])
            return f"Playlist: {title} ({count} videos)"
        return info.get("title", "Unknown Video")
    except Exception:
        return "Loading..."


def get_available_qualities(url: str):
    """
    Probe a single video (the first entry, if a playlist URL is given)
    and return the real set of resolutions/audio options YouTube is
    actually serving for it, instead of guessing from a fixed ladder.

    Returns:
        {
            "title": str,
            "video_heights": [2160, 1440, 1080, ...]  (descending, deduped),
            "has_audio_only": bool,
        }

    Raises ValueError/yt_dlp errors on failure; callers should fall back
    to QUALITY_PRESETS if this fails.
    """
    url = clean_youtube_url(url)
    options = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "extractor_args": EXTRACTOR_ARGS_PROBE,
        "http_headers": COMMON_HEADERS,
        "js_runtimes": _js_runtimes_option(),
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    if not info:
        raise ValueError("Could not read video information")

    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise ValueError("Playlist has no accessible entries")
        # extract_flat gives shallow entries; re-fetch the first one fully.
        first_url = entries[0].get("url") or entries[0].get("webpage_url")
        if not first_url:
            raise ValueError("Could not resolve first playlist entry")
        with YoutubeDL({**options, "noplaylist": True}) as ydl:
            info = ydl.extract_info(first_url, download=False)
        if not info:
            raise ValueError("Could not read first playlist entry")

    formats = info.get("formats") or []
    heights = set()
    has_audio_only = False

    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")

        if height and vcodec and vcodec != "none":
            heights.add(int(height))

        if (not vcodec or vcodec == "none") and acodec and acodec != "none":
            has_audio_only = True

    return {
        "title": info.get("title", "Unknown Video"),
        "video_heights": sorted(heights, reverse=True),
        "has_audio_only": has_audio_only,
    }


def _build_format_string(quality, codec_preference="Auto"):
    """
    Build a yt-dlp format selector string.

    quality: a key from QUALITY_PRESETS, OR an explicit int height
             (as returned by get_available_qualities()).
    codec_preference: a key from CODEC_FILTERS.
    """
    if isinstance(quality, bool):
        max_height = None
    elif isinstance(quality, int):
        max_height = quality
    else:
        max_height = QUALITY_PRESETS.get(quality, None)

    codec_filter = CODEC_FILTERS.get(codec_preference, "") or ""

    if max_height:
        height_cap = f"[height<={max_height}]"
    else:
        height_cap = ""

    primary = f"bestvideo{height_cap}{codec_filter}+bestaudio"
    height_only_fallback = f"bestvideo{height_cap}+bestaudio"
    last_resort = f"best{height_cap}" if height_cap else "best"

    if codec_filter:
        return f"{primary}/{height_only_fallback}/{last_resort}"
    return f"{primary}/{last_resort}"


def download_video(
    url,
    folder,
    progress_callback=None,
    mode="playlist",
    cancel_flag=None,
    title_callback=None,
    log_callback=None,
    quality="Best Available",
    codec_preference="Auto",
    container="mp4",
    audio_only=False,
    audio_format="mp3",
    audio_quality="192",
    embed_thumbnail=False,
    embed_metadata=True,
    subtitles=False,
    auto_subtitles=False,
    subtitle_langs="en",
    cookies_from_browser=None,
    po_token=None,
):
    """
    Download a single video or playlist with yt-dlp.

    quality may be a QUALITY_PRESETS key ("1080p (FHD)") or a raw int
    height (e.g. 1080) sourced from get_available_qualities(); ignored
    entirely when audio_only=True.

    cookies_from_browser: optional browser name ("chrome", "firefox",
    "edge", "brave", etc.). Passing this makes the download use your
    logged-in session, which unlocks most high-bitrate formats without
    needing a separate PO Token. This is the recommended fix if you're
    only getting low-quality output.

    po_token: optional manually-obtained PO token string (advanced;
    see https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide). Only
    needed if cookies alone don't unlock the quality you want.
    """
    url = clean_youtube_url(url)

    if not url:
        raise ValueError("No URL provided")

    if not is_valid_youtube_url(url):
        raise ValueError("That doesn't look like a valid YouTube URL")

    playlist_detected = is_playlist_url(url)

    if mode == "playlist":
        outtmpl = (
            os.path.join(
                folder,
                "%(playlist_title)s",
                "%(playlist_index)02d - %(title)s.%(ext)s",
            )
            if playlist_detected
            else os.path.join(folder, "%(title)s.%(ext)s")
        )
        noplaylist = False if playlist_detected else True
    elif mode == "single":
        outtmpl = os.path.join(folder, "%(title)s.%(ext)s")
        noplaylist = True
    else:
        raise ValueError("Invalid mode. Use 'playlist' or 'single'.")

    def hook(d):
        if cancel_flag and cancel_flag():
            raise DownloadCancelled("Download cancelled by user")

        if progress_callback:
            progress_callback(d)

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

    postprocessors = []

    if audio_only:
        format_string = "bestaudio/best"
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": audio_quality,
            }
        )
    else:
        format_string = _build_format_string(quality, codec_preference)

    if embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

    if embed_thumbnail:
        postprocessors.append({"key": "EmbedThumbnail"})

    want_subs = subtitles or auto_subtitles

    if want_subs and not audio_only:
        postprocessors.append({"key": "FFmpegEmbedSubtitle"})

    # Only override YouTube's client/token behavior if the caller
    # explicitly asked for it; otherwise leave it to yt-dlp's own
    # adaptive defaults (see the note above EXTRACTOR_ARGS_PROBE).
    youtube_extractor_args = {}
    if po_token:
        youtube_extractor_args["po_token"] = [po_token]

    # If Deno is available, it can fully solve the "web" client's JS
    # signature challenges, and "web" URLs are far less likely to 403
    # than the "android_vr" fallback yt-dlp otherwise reaches for.
    # Without Deno, leave the client unset so yt-dlp falls back to
    # whatever combination currently works without JS.
    if _find_deno_path():
        youtube_extractor_args["player_client"] = ["web", "web_safari", "tv", "web_creator"]

    options = {
        "format": format_string,
        "outtmpl": outtmpl,
        "noplaylist": noplaylist,
        "quiet": True,
        "ignoreerrors": False,
        "progress_hooks": [hook],
        "logger": Logger(),
        "postprocessors": postprocessors,
        "writethumbnail": embed_thumbnail,

        # --- Speed & buffer tuning ---
        "concurrent_fragment_downloads": 5,
        "buffersize": 1024 * 1024,
        "http_chunk_size": 10485760,

        "retries": 10,
        "fragment_retries": 10,
        "ffmpeg_location": "/usr/bin/ffmpeg",

        "http_headers": COMMON_HEADERS,
        "js_runtimes": _js_runtimes_option(),
    }

    if youtube_extractor_args:
        options["extractor_args"] = {"youtube": youtube_extractor_args}

    if not audio_only:
        options["merge_output_format"] = container

    if cookies_from_browser:
        options["cookiesfrombrowser"] = (cookies_from_browser,)

    if want_subs:
        options["writesubtitles"] = subtitles
        options["writeautomaticsub"] = auto_subtitles
        options["subtitleslangs"] = [
            lang.strip() for lang in subtitle_langs.split(",") if lang.strip()
        ] or ["en"]
        options["embedsubtitles"] = not audio_only

    if title_callback:
        title_callback(get_fast_title(url))

    if log_callback:
        deno_path = _find_deno_path()
        if deno_path:
            log_callback(f"Using Deno JS runtime at: {deno_path}")
        else:
            log_callback(
                "No Deno runtime found - some high-quality formats may be "
                "unavailable. Install with: curl -fsSL https://deno.land/install.sh | sh"
            )

    with YoutubeDL(options) as ydl:
        ydl.download([url])