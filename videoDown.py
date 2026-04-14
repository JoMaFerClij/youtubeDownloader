import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import yt_dlp


class VideoDownloaderApp:

    def __init__(self, root):
        self.root = root

        # Window config
        self.root.geometry("650x520")
        self.root.resizable(False, False)
        self.root.title("YouTube Downloader (yt-dlp)")
        self.root.config(bg="LightSkyBlue")

        # Variables
        self.video_link = tk.StringVar()
        self.download_path = tk.StringVar()
        self.progress_value = tk.DoubleVar()
        self.status_text = tk.StringVar(value="Idle")
        self.selected_format = tk.StringVar()

        self.formats = []
        self.fetch_job = None  # for debounce

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
        entry = tk.Entry(self.root, textvariable=self.video_link, width=70)
        entry.pack(pady=5)

        # 🔥 AUTO DETECT when user types
        self.video_link.trace_add("write", self.on_url_change)

        # Folder
        tk.Label(self.root, text="Download Folder:", bg="salmon").pack()
        frame = tk.Frame(self.root, bg="LightSkyBlue")
        frame.pack()

        tk.Entry(frame, textvariable=self.download_path, width=50).pack(side=tk.LEFT)
        tk.Button(frame, text="Browse", command=self.browse).pack(side=tk.LEFT, padx=5)

        # Format selector
        tk.Label(self.root, text="Available Formats:", bg="salmon").pack(pady=5)

        self.format_combo = ttk.Combobox(self.root,
                                        textvariable=self.selected_format,
                                        width=90,
                                        state="readonly")
        self.format_combo.pack(pady=5)

        # Progress bar
        ttk.Progressbar(self.root,
                        variable=self.progress_value,
                        maximum=100,
                        length=500).pack(pady=15)

        # Status
        tk.Label(self.root,
                 textvariable=self.status_text,
                 bg="LightSkyBlue").pack()

        # Download button
        tk.Button(self.root,
                  text="Download Selected Format",
                  command=self.start_download,
                  bg="thistle1",
                  font=("Arial", 12)).pack(pady=15)

    # -------------------------
    # URL CHANGE (AUTO FETCH)
    # -------------------------
    def on_url_change(self, *args):

        # Cancel previous scheduled fetch
        if self.fetch_job:
            self.root.after_cancel(self.fetch_job)

        # Wait 1 second after typing stops
        self.fetch_job = self.root.after(1000, self.fetch_formats)

    # -------------------------
    # ACTIONS
    # -------------------------
    def browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path.set(folder)

    def fetch_formats(self):
        thread = threading.Thread(target=self._fetch_formats_thread)
        thread.daemon = True
        thread.start()

    def _fetch_formats_thread(self):

        url = self.video_link.get()

        if not url.strip():
            return

        self.update_status("Fetching formats...")

        try:
            ydl_opts = {
                'quiet': True,

                'js_runtimes': {
                    'node': {
                        'path': r'C:\Program Files\nodejs\node.exe'
                    }
                },

                # 🔥 NEW FIX
                'remote_components': ['ejs:github'],

                'http_headers': {
                    'User-Agent': 'Mozilla/5.0'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            formats = info.get('formats', [])

            self.formats = []
            display_list = []

            for f in formats:
                if f.get('vcodec') != 'none':

                    res = f.get('resolution') or f"{f.get('height')}p"
                    fps = f.get('fps') or ""
                    size = f.get('filesize') or f.get('filesize_approx')

                    size_mb = f"{round(size / (1024*1024), 1)}MB" if size else "?"

                    label = f"{f['format_id']} | {res} | {fps}fps | {size_mb}"

                    self.formats.append((label, f['format_id']))
                    display_list.append(label)

            # Update UI safely
            self.root.after(0, self.format_combo.config, {'values': display_list})

            if display_list:
                self.root.after(0, self.selected_format.set, display_list[0])

            self.update_status("Formats loaded ✅")

        except Exception as e:
            self.update_status("Error ❌")
            messagebox.showerror("Error", str(e))

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

        if not url or not path:
            messagebox.showerror("Error", "Provide URL and folder")
            return

        selected = self.selected_format.get()

        if not selected:
            messagebox.showerror("Error", "Select a format first")
            return

        # Get format_id
        format_id = None
        for label, fid in self.formats:
            if label == selected:
                format_id = fid
                break

        self.update_status("Downloading...")

        ydl_opts = {
            'outtmpl': f'{path}/%(title)s [%(resolution)s].%(ext)s',
            'format': f'{format_id}+bestaudio/best',
            'merge_output_format': 'mp4',
            'progress_hooks': [self.progress_hook],
            'noplaylist': True,

            'js_runtimes': {
                'node': {
                    'path': r'C:\Program Files\nodejs\node.exe'
                }
            },

            # 🔥 NEW FIX
            'remote_components': ['ejs:github'],

            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

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