import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
from yt_dlp import YoutubeDL
import threading
import urllib.request
import webbrowser

# ==== Verze a URL k aktualizaci ====
APP_VERSION = "0.1.0"
VERSION_URL = "https://raw.githubusercontent.com/Burak987/YT_Downloader/main/version.txt"
UPDATE_URL = "https://github.com/Burak987/YT_Downloader/raw/refs/heads/main/yt_downloader_gui.exe"

class YTDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("620x220")
        self.resizable(False, False)

        # === MENU ===
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Nastavení", menu=settings_menu)
        settings_menu.add_command(label="O aplikaci", command=self.show_about)

        # === UI ===
        tk.Label(self, text="Vlož odkaz na YouTube video:").pack(pady=(10, 2))
        self.url_entry = tk.Entry(self, width=80)
        self.url_entry.pack(pady=5)

        self.option = tk.StringVar(value="audio")
        option_frame = tk.Frame(self)
        option_frame.pack()
        tk.Radiobutton(option_frame, text="Pouze zvuk", variable=self.option, value="audio").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(option_frame, text="Video", variable=self.option, value="video").pack(side=tk.LEFT, padx=10)

        self.download_path = Path.home() / "Desktop"
        path_frame = tk.Frame(self)
        path_frame.pack(pady=10)
        self.path_label = tk.Label(path_frame, text=f"Složka pro uložení: {self.download_path}", width=75, anchor="w", relief="sunken")
        self.path_label.pack(side=tk.LEFT, padx=5)
        tk.Button(path_frame, text="Změnit...", command=self.choose_folder).pack(side=tk.LEFT)

        self.progress_label = tk.Label(self, text="", fg="blue", justify="left", anchor="w")
        self.progress_label.pack(pady=10)

        self.download_button = tk.Button(self, text="Stáhnout", command=self.start_download)
        self.download_button.pack(pady=5)

    # ==== Nastavení / O aplikaci ====
    def show_about(self):
        about_window = tk.Toplevel(self)
        about_window.title("O aplikaci")
        about_window.geometry("350x180")
        about_window.resizable(False, False)

        tk.Label(about_window, text=f"YouTube Downloader", font=("Arial", 14, "bold")).pack(pady=(10, 5))
        tk.Label(about_window, text=f"Verze: {APP_VERSION}", font=("Arial", 12)).pack(pady=5)

        tk.Button(about_window, text="Zkontrolovat aktualizace", command=self.check_update).pack(pady=15)

    def check_update(self):
        try:
            with urllib.request.urlopen(VERSION_URL) as response:
                latest_version = response.read().decode("utf-8").strip()

            if latest_version == APP_VERSION:
                messagebox.showinfo("Aktualizace", "Používáte nejnovější verzi aplikace ✅")
            else:
                answer = messagebox.askyesno("Aktualizace", f"Je dostupná nová verze ({latest_version}).\n"
                                                            f"Chceš ji stáhnout?")
                if answer:
                    webbrowser.open(UPDATE_URL)
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se ověřit aktualizaci:\n{e}")

    # ==== Ostatní funkce zůstávají stejné ====
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Vyber složku pro uložení")
        if folder:
            self.download_path = Path(folder)
            self.path_label.config(text=f"Složka pro uložení: {self.download_path}")

    def get_public_ip(self):
        try:
            with urllib.request.urlopen('https://api.ipify.org') as response:
                ip = response.read().decode('utf-8')
            return ip
        except Exception:
            return "Neznámá"

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            percent = (downloaded_bytes / total_bytes * 100) if total_bytes else 0
            speed = d.get('speed', 0)
            eta = d.get('eta', '?')
            speed_mb = speed / 1024 / 1024 if speed else 0

            public_ip = self.get_public_ip()

            self.progress_label.config(
                text=f"Veřejná IP: {public_ip}\n"
                     f"Staženo: {percent:.2f}% | Rychlost: {speed_mb:.2f} MB/s | Zbývá: {eta} s"
            )
        elif d['status'] == 'finished':
            self.progress_label.config(text="Stažení dokončeno. Zpracovávám soubor...")

    def download_video(self, url, audio_only):
        ydl_opts = {
            'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'quiet': True,
        }

        if audio_only:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Hotovo", f"Soubor byl uložen do:\n{self.download_path}")
        except Exception as e:
            messagebox.showerror("Chyba při stahování", str(e))
        finally:
            self.download_button.config(state=tk.NORMAL)
            self.progress_label.config(text="")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Chybí odkaz", "Zadej prosím platný odkaz na YouTube video.")
            return
        self.download_button.config(state=tk.DISABLED)
        audio_only = self.option.get() == "audio"
        threading.Thread(target=self.download_video, args=(url, audio_only), daemon=True).start()

if __name__ == "__main__":
    app = YTDownloaderApp()
    app.mainloop()
