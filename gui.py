import os
import sys
import json
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog

from yt_downloader import (
    download_video,
    format_speed,
    format_eta,
    is_valid_youtube_url,
    QUALITY_PRESETS,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "2.0.0"

# Settings are stored next to the app so preferences survive restarts
SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "settings.json"
)


def load_settings():
    defaults = {
        "folder": os.path.join(os.path.expanduser("~"), "Downloads"),
        "mode": "playlist",
        "quality": "Best Available",
        "theme": "Dark",
    }
    try:
        with open(SETTINGS_PATH, "r") as f:
            data = json.load(f)
            defaults.update(data)
    except Exception:
        pass
    return defaults


def save_settings(settings: dict):
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def open_in_file_manager(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()

        self.title("TubeStream Downloader Pro")
        self.geometry("960x700")
        self.minsize(900, 650)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.cancel_requested = False
        self.last_folder = self.settings["folder"]

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="TubeStream Pro",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.logo_label.pack(pady=(28, 4))

        self.tagline_label = ctk.CTkLabel(
            self.sidebar,
            text="High-quality YouTube downloads",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            wraplength=160,
            justify="center",
        )
        self.tagline_label.pack(pady=(0, 30))

        # Mode
        ctk.CTkLabel(self.sidebar, text="Download Mode", anchor="w").pack(
            fill="x", padx=20, pady=(0, 4)
        )
        self.mode_var = ctk.StringVar(value=self.settings["mode"])
        self.mode_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["playlist", "single"],
            variable=self.mode_var,
            command=lambda _: self._persist_settings(),
        )
        self.mode_menu.pack(fill="x", padx=20, pady=(0, 20))

        # Quality
        ctk.CTkLabel(self.sidebar, text="Video Quality", anchor="w").pack(
            fill="x", padx=20, pady=(0, 4)
        )
        self.quality_var = ctk.StringVar(value=self.settings["quality"])
        self.quality_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=list(QUALITY_PRESETS.keys()),
            variable=self.quality_var,
            command=lambda _: self._persist_settings(),
        )
        self.quality_menu.pack(fill="x", padx=20, pady=(0, 20))

        # Theme
        ctk.CTkLabel(self.sidebar, text="Theme", anchor="w").pack(
            fill="x", padx=20, pady=(0, 4)
        )
        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light", "System"],
            command=self._on_theme_change,
        )
        self.theme_menu.pack(fill="x", padx=20, pady=(0, 20))
        self.theme_menu.set(self.settings["theme"])
        ctk.set_appearance_mode(self.settings["theme"])

        # Spacer + version footer
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=10),
            text_color="gray50",
        )
        self.version_label.pack(pady=14)

    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=30, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkLabel(
            self.main_frame,
            text="Download YouTube Videos & Playlists",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        self.header.pack(anchor="w", pady=(4, 20))

        # URL row (entry + paste button)
        self.url_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.url_frame.pack(fill="x", pady=(0, 14))

        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="Paste YouTube video or playlist URL...",
            height=44,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda _e: self.start_download())

        self.paste_btn = ctk.CTkButton(
            self.url_frame, text="Paste", width=90, height=44, command=self.paste_url
        )
        self.paste_btn.pack(side="right")

        # Folder row
        self.folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.folder_frame.pack(fill="x", pady=(0, 20))

        self.folder_path = ctk.StringVar(value=self.last_folder)
        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            textvariable=self.folder_path,
            placeholder_text="Choose download folder...",
            height=44,
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            self.folder_frame, text="Browse", width=110, height=44, command=self.browse_folder
        )
        self.browse_btn.pack(side="right")

        # Current title
        self.current_title = ctk.CTkLabel(
            self.main_frame,
            text="Current: None",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.current_title.pack(fill="x", pady=(4, 10))

        # Status
        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray", anchor="w")
        self.status_label.pack(fill="x", pady=(0, 8))

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, height=14)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=10)

        # Speed / ETA / Size
        self.stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 10))

        self.speed_label = ctk.CTkLabel(self.stats_frame, text="Speed: --")
        self.speed_label.pack(side="left", padx=(0, 24))

        self.eta_label = ctk.CTkLabel(self.stats_frame, text="ETA: --")
        self.eta_label.pack(side="left", padx=(0, 24))

        self.percent_label = ctk.CTkLabel(self.stats_frame, text="0%")
        self.percent_label.pack(side="left")

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=15)

        self.download_btn = ctk.CTkButton(
            self.button_frame,
            text="Download Now",
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.start_download,
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.skip_btn = ctk.CTkButton(
            self.button_frame,
            text="Skip / Stop",
            height=48,
            width=120,
            fg_color="#e67e22",
            hover_color="#d35400",
            command=self.skip_download,
        )
        self.skip_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            height=48,
            width=120,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.cancel_download,
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))

        self.open_folder_btn = ctk.CTkButton(
            self.button_frame,
            text="Open Folder",
            height=48,
            width=130,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self.open_download_folder,
            state="disabled",
        )
        self.open_folder_btn.pack(side="left")

        # Log box header row
        self.log_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.log_header.pack(fill="x", pady=(15, 4))

        ctk.CTkLabel(
            self.log_header, text="Activity Log", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        self.clear_log_btn = ctk.CTkButton(
            self.log_header, text="Clear", width=70, height=26, command=self.clear_log
        )
        self.clear_log_btn.pack(side="right")

        # Log Box
        self.log_box = ctk.CTkTextbox(self.main_frame, height=200)
        self.log_box.pack(fill="both", expand=True)
        self.log_box.insert("end", "TubeStream Pro initialized...\n")
        self.log_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------
    def _persist_settings(self):
        self.settings.update(
            {
                "folder": self.folder_path.get().strip() or self.last_folder,
                "mode": self.mode_var.get(),
                "quality": self.quality_var.get(),
                "theme": self.theme_menu.get(),
            }
        )
        save_settings(self.settings)

    def _on_theme_change(self, value):
        ctk.set_appearance_mode(value)
        self._persist_settings()

    def on_close(self):
        self._persist_settings()
        self.destroy()

    # ------------------------------------------------------------------
    # UI actions
    # ------------------------------------------------------------------
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path.get() or None)
        if folder:
            self.folder_path.set(folder)
            self._persist_settings()

    def paste_url(self):
        try:
            clipboard_text = self.clipboard_get().strip()
        except Exception:
            clipboard_text = ""

        if clipboard_text:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard_text)

    def open_download_folder(self):
        folder = self.folder_path.get().strip()
        if folder and os.path.isdir(folder):
            open_in_file_manager(folder)

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def update_title(self, title):
        self.current_title.configure(text=f"Current: {title}")

    def update_log(self, text):
        def append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", text + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.after(0, append)

    def cancel_download(self):
        self.cancel_requested = True
        self.update_status("Cancelling download...", "#e74c3c")
        self.update_log("User requested cancellation.")

    def skip_download(self):
        self.cancel_requested = True
        self.update_status("Skipping / stopping current download...", "#e67e22")
        self.update_log("User requested skip/stop.")

    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.folder_path.get().strip()
        mode = self.mode_var.get()
        quality = self.quality_var.get()

        if not url:
            self.update_status("Error: Please enter a URL", "#e74c3c")
            return

        if not is_valid_youtube_url(url):
            self.update_status("Error: That doesn't look like a YouTube URL", "#e74c3c")
            return

        if not folder:
            self.update_status("Error: Please choose a download folder", "#e74c3c")
            return

        os.makedirs(folder, exist_ok=True)
        self.last_folder = folder
        self._persist_settings()

        self.cancel_requested = False
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.open_folder_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.speed_label.configure(text="Speed: --")
        self.eta_label.configure(text="ETA: --")
        self.percent_label.configure(text="0%")

        if mode == "playlist":
            self.update_status("Preparing playlist download...", "#f1c40f")
        else:
            self.update_status("Preparing single video download...", "#f1c40f")

        self.update_log(f"Starting {mode} download at quality: {quality}...")

        threading.Thread(
            target=self.run_download,
            args=(url, folder, mode, quality),
            daemon=True,
        ).start()

    def run_download(self, url, folder, mode, quality):
        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed")
                eta = d.get("eta")

                if total:
                    progress = downloaded / total
                    pct = int(progress * 100)
                    self.after(0, lambda: self.progress_bar.set(progress))
                    self.after(0, lambda: self.percent_label.configure(text=f"{pct}%"))
                    self.after(
                        0,
                        lambda: self.update_status(f"Downloading... {pct}%", "#3498db"),
                    )

                self.after(
                    0, lambda: self.speed_label.configure(text=f"Speed: {format_speed(speed)}")
                )
                self.after(0, lambda: self.eta_label.configure(text=f"ETA: {format_eta(eta)}"))

            elif d["status"] == "finished":
                self.after(0, lambda: self.update_status("Finalizing file...", "#f1c40f"))
                self.after(0, lambda: self.speed_label.configure(text="Speed: --"))
                self.after(0, lambda: self.eta_label.configure(text="ETA: --"))

        try:
            download_video(
                url,
                folder,
                progress_callback=progress_hook,
                mode=mode,
                cancel_flag=lambda: self.cancel_requested,
                title_callback=lambda title: self.after(0, lambda: self.update_title(title)),
                log_callback=self.update_log,
                quality=quality,
            )

            if self.cancel_requested:
                self.after(0, lambda: self.update_status("Download stopped by user.", "#e67e22"))
            else:
                success_text = (
                    "Success! Playlist Downloaded"
                    if mode == "playlist"
                    else "Success! Video Downloaded"
                )
                self.after(0, lambda: self.update_status(success_text, "#2ecc71"))
                self.after(0, lambda: self.open_folder_btn.configure(state="normal"))
                self.update_log("Download completed successfully.")

        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: self.update_status(f"Error: {msg}", "#e74c3c"))
            self.update_log(f"ERROR: {error_msg}")

        finally:
            self.after(0, self.reset_ui)

    def reset_ui(self):
        self.download_btn.configure(state="normal", text="Download Now")
        self.progress_bar.set(0)
        self.speed_label.configure(text="Speed: --")
        self.eta_label.configure(text="ETA: --")
        self.percent_label.configure(text="0%")


if __name__ == "__main__":
    app = App()
    app.mainloop()