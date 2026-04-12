import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import yt_dlp


class VideoDownloaderApp:

    def __init__(self, root):
        self.root = root

        # Window config
        self.root.geometry("550x380")
        self.root.resizable(False, False)
        self.root.title("YouTube Downloader (yt-dlp)")
        self.root.config(bg="LightSkyBlue")

        # Variables
        self.video_link = tk.StringVar()
        self.download_path = tk.StringVar()
        self.progress_value = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Idle")
        self.quality = tk.StringVar(value="Best")

        self.create_widgets()

    # -------------------------
    # UI
    # -------------------------
    def create_widgets(self):

        tk.Label(self.root,
                 text="YouTube Video Downloader",
                 font="SegoeUI 14",
                 bg="LightSkyBlue",
                 fg="red").pack(pady=10)

        # URL
        tk.Label(self.root, text="Video URL:", bg="salmon").pack()
        tk.Entry(self.root, textvariable=self.video_link, width=50).pack(pady=5)

        # Folder
        tk.Label(self.root, text="Download Folder:", bg="salmon").pack()
        frame = tk.Frame(self.root, bg="LightSkyBlue")
        frame.pack()

        tk.Entry(frame, textvariable=self.download_path, width=40).pack(side=tk.LEFT)
        tk.Button(frame, text="Browse", command=self.browse).pack(side=tk.LEFT, padx=5)

        # Quality selector
        tk.Label(self.root, text="Quality:", bg="salmon").pack(pady=5)

        ttk.Combobox(self.root,
                     textvariable=self.quality,
                     values=["Best", "1080p", "720p", "Audio (MP3)"],
                     state="readonly").pack()

        # Progress bar
        ttk.Progressbar(self.root,
                        variable=self.progress_value,
                        maximum=100,
                        length=400).pack(pady=15)

        # Status
        tk.Label(self.root,
                 textvariable=self.status_text,
                 bg="LightSkyBlue").pack()

        # Download button
        tk.Button(self.root,
                  text="Download",
                  command=self.start_download,
                  bg="thistle1",
                  font=("Arial", 12)).pack(pady=15)

    # -------------------------
    # ACTIONS
    # -------------------------
    def browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path.set(folder)

    def start_download(self):
        thread = threading.Thread(target=self.download)
        thread.daemon = True
        thread.start()

    # -------------------------
    # DOWNLOAD LOGIC
    # -------------------------
    def download(self):

        url = self.video_link.get()
        path = self.download_path.get()
        quality = self.quality.get()

        if not url or not path:
            messagebox.showerror("Error", "Please provide URL and folder")
            return

        self.update_status("Starting download...")

        ydl_opts = {
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
        }

        # Quality selection
        if quality == "Best":
            ydl_opts['format'] = 'best'
        elif quality == "1080p":
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
        elif quality == "720p":
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
        elif quality == "Audio (MP3)":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.root.after(0, self.update_status, "Completed ✅")
            self.root.after(0, self.set_progress, 100)

            messagebox.showinfo("Success", "Download completed!")

        except Exception as e:
            self.root.after(0, self.update_status, "Error ❌")
            messagebox.showerror("Error", str(e))

    # -------------------------
    # PROGRESS
    # -------------------------
    def progress_hook(self, d):

        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%').replace('%', '').strip()

            try:
                percent = float(percent_str)
                self.root.after(0, self.set_progress, percent)
                self.root.after(0, self.update_status,
                                f"{percent:.1f}% downloading...")
            except:
                pass

        elif d['status'] == 'finished':
            self.root.after(0, self.update_status, "Processing...")

    # -------------------------
    # UI SAFE UPDATE
    # -------------------------
    def set_progress(self, value):
        self.progress_value.set(value)

    def update_status(self, text):
        self.status_text.set(text)