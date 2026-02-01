#!/usr/bin/env python3
"""
YouTube Downloader
Author: <Your Name>
Description: Download the best 1080p video from YouTube using yt-dlp.
"""

from yt_dlp import YoutubeDL

def download_video(url):
    """
    Download the best 1080p video from the provided URL using yt-dlp.
    """
    options = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'outtmpl': '%(title)s.%(ext)s',  # Save with video title as filename
        'merge_output_format': 'mp4',     # Ensure video + audio merged as mp4
        'noplaylist': True                # Avoid downloading playlists by default
    }

    with YoutubeDL(options) as ydl:
        try:
            ydl.download([url])
            print("Download completed successfully!")
        except Exception as e:
            print(f"Error: {e}")

def main():
    url = input("Please paste the YouTube video URL: ").strip()
    if not url:
        print("No URL entered. Exiting...")
        return
    download_video(url)

if __name__ == "__main__":
    main()
