# gui.py
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from yt_downloader import download_video

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader")
        self.geometry("600x320")
        self.resizable(False, False)

        self.label = ctk.CTkLabel(self, text="YouTube Video Downloader",
                                  font=ctk.CTkFont(size=20, weight="bold"))
        self.label.pack(pady=20)

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL here...",
                                      width=500, height=35)
        self.url_entry.pack(pady=10)

        self.folder_frame = ctk.CTkFrame(self)
        self.folder_frame.pack(pady=10, padx=20, fill="x")

        self.folder_path = ctk.StringVar()
        self.folder_entry = ctk.CTkEntry(self.folder_frame,
                                         textvariable=self.folder_path,
                                         placeholder_text="Select download folder")
        self.folder_entry.pack(side="left", expand=True, fill="x", padx=(10, 5))

        self.browse_btn = ctk.CTkButton(self.folder_frame, text="Browse",
                                        command=self.browse_folder)
        self.browse_btn.pack(side="right", padx=(5, 10))

        self.download_btn = ctk.CTkButton(self, text="Start Download",
                                          fg_color="#2ecc71",
                                          hover_color="#27ae60",
                                          command=self.start_download)
        self.download_btn.pack(pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def start_download(self):
        url = self.url_entry.get().strip()
        folder = self.folder_path.get()

        if not url or not folder:
            messagebox.showwarning("Error", "URL and folder are required")
            return

        self.download_btn.configure(state="disabled")
        threading.Thread(
            target=self.run_download,
            args=(url, folder),
            daemon=True
        ).start()

    def run_download(self, url, folder):
        try:
            download_video(url, folder)
            messagebox.showinfo("Success", "Download completed!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.download_btn.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
