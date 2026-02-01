# yt_downloader.py
import os
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, parse_qs

def clean_youtube_url(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if 'v' in qs:
        return f"https://www.youtube.com/watch?v={qs['v'][0]}"
    return url

def download_video(url, folder,progress_callback=None):
    url = clean_youtube_url(url)

    if not url:
        raise ValueError("No URL provided")

    options = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': False,
        'progress_hooks': [progress_callback] if progress_callback else [],
    }

    with YoutubeDL(options) as ydl:
        ydl.download([url])
