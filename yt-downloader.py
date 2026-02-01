#!/usr/bin/env python3
"""
YouTube Downloader GUI
Author: <Your Name>
Description: Download the best 1080p video from YouTube using a simple Tkinter GUI.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from yt_dlp import YoutubeDL
import os

def download_video(url, folder):
    """
    Download the best 1080p video to the selected folder.
    """
    if not url:
        messagebox.showwarning("Error", "Please enter a video URL")
        return

    options = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'noplaylist': True
    }

    try:
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        messagebox.showinfo("Success", "Download completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download video:\n{e}")

def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path.set(folder_selected)

def start_download():
    url = url_entry.get().strip()
    folder = folder_path.get()
    if not folder:
        messagebox.showwarning("Error", "Please select a download folder")
        return
    download_video(url, folder)

# ----------------- Tkinter GUI -----------------
root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("500x200")
root.resizable(False, False)

# URL input
tk.Label(root, text="YouTube Video URL:").pack(pady=(10, 0))
url_entry = tk.Entry(root, width=60)
url_entry.pack(pady=(0, 10))

# Folder selection
folder_path = tk.StringVar()
tk.Label(root, text="Download Folder:").pack()
folder_frame = tk.Frame(root)
folder_frame.pack(pady=(0, 10))
folder_entry = tk.Entry(folder_frame, textvariable=folder_path, width=45)
folder_entry.pack(side=tk.LEFT, padx=(0,5))
browse_btn = tk.Button(folder_frame, text="Browse", command=browse_folder)
browse_btn.pack(side=tk.LEFT)

# Download button
download_btn = tk.Button(root, text="Download Video", command=start_download, bg="#4CAF50", fg="white")
download_btn.pack(pady=(10, 10))

root.mainloop()
