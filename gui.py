import threading
import customtkinter as ctk
from tkinter import filedialog
from yt_downloader import download_video  # Core logic

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TubeStream Downloader v1.0")
        self.geometry("700x450")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="TubeStream",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.pack(pady=20)

        self.appearance_label = ctk.CTkLabel(self.sidebar, text="Theme:")
        self.appearance_label.pack(pady=(100, 0))

        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light", "System"],
            command=ctk.set_appearance_mode
        )
        self.theme_menu.pack(pady=10)

        # Main area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=30, pady=20, sticky="nsew")

        self.header = ctk.CTkLabel(
            self.main_frame,
            text="Download New Video",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.header.pack(anchor="w", pady=(10, 30))

        self.url_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="https://youtube.com/watch?v=...",
            height=40
        )
        self.url_entry.pack(fill="x", pady=(0, 20))

        self.folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.folder_frame.pack(fill="x", pady=(0, 20))

        self.folder_path = ctk.StringVar()
        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            textvariable=self.folder_path,
            height=40
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            self.folder_frame,
            text="Browse",
            width=100,
            command=self.browse_folder
        )
        self.browse_btn.pack(side="right")

        self.status_label = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.status_label.pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, height=10)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=10)

        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="Download Video",
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        self.download_btn.pack(fill="x", pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def update_status(self, text, color="white"):
        self.status_label.configure(text=text, text_color=color)

    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.folder_path.get()

        if not url or not folder:
            self.update_status("Error: Missing URL or Folder", "#e74c3c")
            return

        self.download_btn.configure(state="disabled", text="Downloading...")
        self.progress_bar.set(0)
        self.update_status("Connecting to YouTube...", "#f1c40f")

        threading.Thread(
            target=self.run_download,
            args=(url, folder),
            daemon=True
        ).start()

    def run_download(self, url, folder):

        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)

                if total:
                    progress = downloaded / total
                    self.after(0, lambda: self.progress_bar.set(progress))
                    self.after(0, lambda: self.update_status(
                        f"Downloading… {int(progress * 100)}%", "#3498db"
                    ))

            elif d['status'] == 'finished':
                self.after(0, lambda: self.update_status(
                    "Finalizing file…", "#f1c40f"
                ))

        try:
            download_video(url, folder, progress_hook)
            self.after(0, lambda: self.update_status(
                "Success! Video Downloaded", "#2ecc71"
            ))
        except Exception as e:
                error_msg = str(e)
                self.after(0, lambda msg=error_msg: self.update_status(
                    f"Error: {msg}", "#e74c3c"
                ))
        finally:
            self.after(0, self.reset_ui)

    def reset_ui(self):
        self.download_btn.configure(state="normal", text="Download Video")
        self.progress_bar.set(0)


if __name__ == "__main__":
    app = App()
    app.mainloop()
