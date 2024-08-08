"""
** YouTube Downloader **
Download the HIGHEST QUALITY video and audio separately for editing.
Or download the Legacy Format Stream that includes both video and audio at a lower quality 720p or lower.

@author: Sahand
"""

import os
import threading
import re
import subprocess
import sys
from pytubefix import YouTube
import customtkinter as ctk

# Constants for configuration
DEFAULT_FONT = ("Comfortaa", 16)
VIDEO_ID_LENGTH = 11
URL_PATTERNS = [
    r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}$',
    r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]{11}$'
]
DOWNLOAD_TYPES = {
    "legacy": "legacy.mp4",
    "mp4": "video.mp4",
    "mp3": "audio.mp3"
}

class YouTubeDownloader:
    def __init__(self, app):
        self.app = app
        self.downloading = False
        self.setup_ui()

    def setup_ui(self):
        # Set the appearance mode and color theme for the UI
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        # Create the main application window
        self.app.title("YouTube Downloader")
        self.app.geometry("600x450")
        self.app.resizable(False, False)

        # Create a frame to hold UI elements
        self.frame = ctk.CTkFrame(self.app)
        self.frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Add an entry field for users to paste YouTube URL
        self.entry = ctk.CTkEntry(self.frame, placeholder_text="Paste YouTube URL & Press Enter", font=DEFAULT_FONT, text_color="lightblue")
        self.entry.grid(row=0, column=0, columnspan=3, pady=10, padx=20, sticky="ew")

        # Create a frame for displaying video information
        self.info_frame = ctk.CTkFrame(self.frame)
        self.info_frame.grid(row=1, column=0, columnspan=3, pady=10, padx=20, sticky="nsew")

        # Initialize labels for displaying video information
        self.title_label = self.create_wrapped_label(self.info_frame, "Title:")
        self.video_resolution_label = self.create_wrapped_label(self.info_frame, "Highest MP4 Resolution: ")
        self.audio_resolution_label = self.create_wrapped_label(self.info_frame, "Highest MP3 Bitrate: ")
        self.full_stream_label = self.create_wrapped_label(self.info_frame, "Legacy Format: ")

        # Initially hide the info_frame
        self.info_frame.grid_forget()

        # Create download buttons and place them in the grid
        self.button1 = self.create_button("MP4", lambda: self.download("mp4"))
        self.button1.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        self.button1.configure(state=ctk.DISABLED)

        self.button2 = self.create_button("Legacy", lambda: self.download("legacy"))
        self.button2.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.button2.configure(state=ctk.DISABLED)

        self.button3 = self.create_button("MP3", lambda: self.download("mp3"))
        self.button3.grid(row=4, column=2, padx=5, pady=5, sticky="ew")
        self.button3.configure(state=ctk.DISABLED)

        # Configure the grid layout to adjust row and column weights
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=0)
        self.frame.grid_rowconfigure(4, weight=0)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.columnconfigure(2, weight=1)

        # Create a label for displaying feedback messages
        self.feedback_label = ctk.CTkLabel(self.frame, text="", text_color="gold")
        self.feedback_label.grid(row=3, column=1, padx=5, pady=5)
        self.feedback_label.grid_forget()  # Initially hide the feedback label

        # Bind Enter key to the on_return_entry function
        self.entry.bind("<Return>", self.on_return_entry)

    def create_wrapped_label(self, parent, text, **kwargs):
        """
        Create and return a wrapped label widget.
        """
        kwargs.setdefault('text_color', 'lightblue')
        kwargs.setdefault('font', DEFAULT_FONT)
        label = ctk.CTkLabel(parent, text=text, wraplength=500, **kwargs)
        label.pack(anchor="w", padx=5, pady=10, fill="x")
        return label

    def create_button(self, text, command):
        return ctk.CTkButton(self.frame, text=text, command=command, font=("Comfortaa", 13))

    def is_valid_youtube_url(self, url):
        """
        Check if a given URL is a valid YouTube video URL based on predefined patterns.
        """
        return any(re.match(pattern, url) for pattern in URL_PATTERNS)

    def fetch_details(self, url):
        """
        Fetches video details from a YouTube URL and updates UI elements accordingly.
        """
        if not self.is_valid_youtube_url(url):
            self.update_feedback("Enter a Valid YouTube URL")
            return None

        try:
            yt = YouTube(url)
            self.toggle_info_section(True)

            full_stream = yt.streams.get_highest_resolution(progressive=True)
            video_stream = yt.streams.get_highest_resolution(progressive=False)
            audio_streams = yt.streams.filter(only_audio=True)
            highest_bitrate_stream = max(audio_streams, key=lambda stream: int(stream.abr.replace('kbps', '')))

            self.update_feedback(f"{yt.title}")
            self.update_ui_labels(video_stream, highest_bitrate_stream, full_stream)

            # Enable buttons for download options
            for button in [self.button1, self.button2, self.button3]:
                button.configure(state=ctk.NORMAL)

            return full_stream, video_stream, highest_bitrate_stream
        except Exception as e:
            self.update_feedback(f"Error: {e}")
            return None

    def update_ui_labels(self, video_stream, highest_bitrate_stream, full_stream):
        """
        Updates UI labels with video details.
        """
        self.title_label.configure(text=f"Title: {video_stream.title}")
        self.video_resolution_label.configure(text=f"Highest MP4 Resolution: {video_stream.resolution}")
        self.audio_resolution_label.configure(text=f"Highest MP3 Bitrate: {highest_bitrate_stream.abr}")
        self.full_stream_label.configure(text=f"Legacy Format (Video & Audio): {full_stream.resolution}")

    def toggle_info_section(self, show):
        if show:
            self.info_frame.grid(row=1, column=0, columnspan=3, pady=10, padx=20, sticky="nsew")
        else:
            self.info_frame.grid_forget()

    def update_feedback(self, message, file_path=None):
        """
        Update feedback message and optionally provide a file path link.
        """
        self.feedback_label.configure(text=message)
        self.feedback_label.grid(row=3, column=1, padx=5, pady=5)
        if file_path:
            self.feedback_label.configure(cursor="hand2")
            self.feedback_label.bind("<Button-1>", lambda e: self.open_directory(file_path))
        else:
            self.feedback_label.configure(cursor="")
            self.feedback_label.unbind("<Button-1>")

    def update_feedback_safe(self, message, file_path=None):
        """
        Update feedback safely from a thread.
        """
        self.app.after(0, self.update_feedback, message, file_path)

    def open_directory(self, file_path):
        directory = os.path.dirname(file_path)
        try:
            if os.name == 'nt':
                os.startfile(directory)
            elif os.name == 'posix':
                if sys.platform == 'darwin':
                    subprocess.run(["open", directory], check=True)
                else:
                    subprocess.run(["xdg-open", directory], check=True)
        except Exception as e:
            self.update_feedback(f"Error opening directory: {e}")

    def download_handler(self, stream, filename, message):
        """
        Handles the download process in a separate thread.
        """
        def run():
            try:
                file_path = os.path.join(os.getcwd(), filename)
                stream.download(filename=filename)
                self.update_feedback_safe(f"{file_path}", file_path)
            except Exception as e:
                self.update_feedback_safe(f"Error: {e}")
            finally:
                self.downloading = False

        threading.Thread(target=run).start()

    def download(self, type_key):
        url = self.entry.get().strip()
        if not self.is_valid_youtube_url(url):
            self.update_feedback("Enter a Valid YouTube URL")
            return

        self.downloading = True
        fetch_data = self.fetch_details(url)

        if fetch_data:
            if type_key == "legacy":
                stream, filename = fetch_data[0], DOWNLOAD_TYPES[type_key]
            elif type_key == "mp4":
                stream, filename = fetch_data[1], DOWNLOAD_TYPES[type_key]
            elif type_key == "mp3":
                stream, filename = fetch_data[2], DOWNLOAD_TYPES[type_key]

            self.update_feedback(f"Downloading {type_key.upper()} @ {stream.resolution if type_key != 'mp3' else stream.abr}...")
            self.download_handler(stream, filename, f"Downloading {type_key.upper()}...")

    def on_return_entry(self, event):
        url = self.entry.get().strip()
        if len(url) >= VIDEO_ID_LENGTH:
            self.fetch_details(url)
            if not self.downloading:
                self.update_feedback("Choose Download Type")
        else:
            self.update_feedback("Enter a Valid YouTube URL")

# Create the main application window and start the app
if __name__ == "__main__":
    app = ctk.CTk()
    downloader = YouTubeDownloader(app)
    app.mainloop()