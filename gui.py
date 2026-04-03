import threading
import customtkinter as ctk
from tkinter import filedialog
from yt_downloader import download_video, format_speed, format_eta

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TubeStream Downloader Pro")
        self.geometry("860x650")
        self.minsize(860, 650)

        self.cancel_requested = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="TubeStream Pro",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.pack(pady=25)

        self.appearance_label = ctk.CTkLabel(self.sidebar, text="Theme")
        self.appearance_label.pack(pady=(80, 0))

        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light", "System"],
            command=ctk.set_appearance_mode
        )
        self.theme_menu.pack(pady=10)
        self.theme_menu.set("Dark")

        self.mode_label_sidebar = ctk.CTkLabel(self.sidebar, text="Mode")
        self.mode_label_sidebar.pack(pady=(30, 0))

        self.mode_var = ctk.StringVar(value="playlist")
        self.mode_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["playlist", "single"],
            variable=self.mode_var
        )
        self.mode_menu.pack(pady=10)

        # Main Frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=30, pady=20, sticky="nsew")

        self.header = ctk.CTkLabel(
            self.main_frame,
            text="Download YouTube Videos & Playlists",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.header.pack(anchor="w", pady=(10, 25))

        self.url_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="Paste YouTube video or playlist URL...",
            height=45
        )
        self.url_entry.pack(fill="x", pady=(0, 20))

        # Folder row
        self.folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.folder_frame.pack(fill="x", pady=(0, 20))

        self.folder_path = ctk.StringVar()
        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            textvariable=self.folder_path,
            placeholder_text="Choose download folder...",
            height=45
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            self.folder_frame,
            text="Browse",
            width=120,
            command=self.browse_folder
        )
        self.browse_btn.pack(side="right")

        # Current title
        self.current_title = ctk.CTkLabel(
            self.main_frame,
            text="Current: None",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.current_title.pack(anchor="w", pady=(5, 10))

        # Status
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Ready",
            text_color="gray"
        )
        self.status_label.pack(anchor="w", pady=(0, 8))

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, height=14)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=10)

        # Speed / ETA
        self.stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 10))

        self.speed_label = ctk.CTkLabel(self.stats_frame, text="Speed: --")
        self.speed_label.pack(side="left", padx=(0, 20))

        self.eta_label = ctk.CTkLabel(self.stats_frame, text="ETA: --")
        self.eta_label.pack(side="left")

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", pady=15)

        self.download_btn = ctk.CTkButton(
            self.button_frame,
            text="Download Now",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.skip_btn = ctk.CTkButton(
            self.button_frame,
            text="Skip / Stop",
            height=50,
            fg_color="#e67e22",
            hover_color="#d35400",
            command=self.skip_download
        )
        self.skip_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            height=50,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.cancel_download
        )
        self.cancel_btn.pack(side="left")

        # Log Box
        self.log_box = ctk.CTkTextbox(self.main_frame, height=220)
        self.log_box.pack(fill="both", expand=True, pady=(15, 0))
        self.log_box.insert("end", "TubeStream Pro initialized...\n")
        self.log_box.configure(state="disabled")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

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

        if not url or not folder:
            self.update_status("Error: Missing URL or Folder", "#e74c3c")
            return

        self.cancel_requested = False
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.progress_bar.set(0)
        self.speed_label.configure(text="Speed: --")
        self.eta_label.configure(text="ETA: --")

        if mode == "playlist":
            self.update_status("Preparing playlist download...", "#f1c40f")
        else:
            self.update_status("Preparing single video download...", "#f1c40f")

        self.update_log(f"Starting {mode} download...")

        threading.Thread(
            target=self.run_download,
            args=(url, folder, mode),
            daemon=True
        ).start()

    def run_download(self, url, folder, mode):

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed')
                eta = d.get('eta')

                if total:
                    progress = downloaded / total
                    self.after(0, lambda: self.progress_bar.set(progress))
                    self.after(0, lambda: self.update_status(
                        f"Downloading... {int(progress * 100)}%", "#3498db"
                    ))

                self.after(0, lambda: self.speed_label.configure(
                    text=f"Speed: {format_speed(speed)}"
                ))
                self.after(0, lambda: self.eta_label.configure(
                    text=f"ETA: {format_eta(eta)}"
                ))

            elif d['status'] == 'finished':
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
                log_callback=self.update_log
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


if __name__ == "__main__":
    app = App()
    app.mainloop()