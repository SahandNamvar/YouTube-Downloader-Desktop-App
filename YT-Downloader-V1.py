"""

** YouTube Downloader **
Download the HIGHEST QUALITY video and audio seperatley for editing.
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

# Set the appearance mode and color theme for the UI
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

# Create the main application window
app = ctk.CTk()
app.title("YouTube Downloader")
app.geometry("600x450")
app.resizable(False, False)

# Create a frame to hold UI elements
frame = ctk.CTkFrame(app)
frame.pack(pady=10, padx=10, fill="both", expand=True)

# Add an entry field for users to paste YouTube URL
entry = ctk.CTkEntry(frame, placeholder_text="Paste YouTube URL & Press Enter", font=DEFAULT_FONT, text_color="lightblue")
entry.grid(row=0, column=0, columnspan=3, pady=10, padx=20, sticky="ew")

# Create a frame for displaying video information
info_frame = ctk.CTkFrame(frame)
info_frame.grid(row=1, column=0, columnspan=3, pady=10, padx=20, sticky="nsew")

# Function to create and return a label with text wrapping
def create_wrapped_label(parent, text, **kwargs):
    """
    Create and return a wrapped label widget.

    Parameters:
    - parent: The parent widget or frame where the label will be placed.
    - text: The text to display on the label.
    - **kwargs: Additional keyword arguments passed to customize the label.
                These can include font, wraplength, text_color, etc.
    Returns:
    - label: The created label widget.
    """
    
    # Default value for text_color & font if not already provided in kwargs
    kwargs.setdefault('text_color', 'lightblue')
    kwargs.setdefault('font', DEFAULT_FONT)
    
    label = ctk.CTkLabel(parent, text=text, wraplength=500, **kwargs)
    label.pack(anchor="w", padx=5, pady=10, fill="x")
    return label

# Initialize labels for displaying video information
title_label = create_wrapped_label(info_frame, "Title:")
video_resolution_label = create_wrapped_label(info_frame, "Highest MP4 Resolution: ")
audio_resolution_label = create_wrapped_label(info_frame, "Highest MP3 Bitrate: ")
full_stream_label = create_wrapped_label(info_frame, "Legacy Format: ")

# Initially hide the info_frame
info_frame.grid_forget()

# Function to show or hide the info_frame
def toggle_info_section(show):
    if show:
        info_frame.grid(row=1, column=0, columnspan=3, pady=10, padx=20, sticky="nsew")
    else:
        info_frame.grid_forget()

# Function to check if a URL is a valid YouTube URL
def is_valid_youtube_url(url):
    """
    Check if a given URL is a valid YouTube video URL based on predefined patterns.
    
    Parameters:
    - url (str): The URL to be checked.
    
    Returns:
    - bool: True if the URL matches any of the predefined YouTube video URL patterns, False otherwise.
    """
    return any(re.match(pattern, url) for pattern in URL_PATTERNS)

# Function to fetch video details from YouTube
def fetch_details(url):
    """
    __Function__:
    Fetches video details from a YouTube URL and updates UI elements accordingly.

    This function validates the YouTube URL, creates a YouTube object, retrieves
    various video and audio streams, updates UI labels with relevant details,
    and enables download buttons based on available streams.

    Parameters:
    - url (str): The YouTube URL to fetch details from.

    Returns:
    - tuple or None: A tuple containing the full video stream (aka Legacy-Format), video-only stream (highest resolution), and audio-only stream (highest bitrate) if successful, or None if there was an error.

    Raises:
    - Exception: If there is an error during YouTube object creation or stream retrieval.
    
    __ExtraDoc__
    Some streams have both a video codec and audio codec, while others have just video or just audio, this is a result of YouTube supporting a streaming technique called Dynamic Adaptive Streaming over HTTP (DASH). 
    
    In the context of pytubefix, the implications are for the highest quality streams; you now need to download both the audio and video tracks and then post-process to merge them.

    The legacy streams that contain the audio and video in a single file (referred to as "progressive download") are still available, but only for resolutions 720p and below.
    """
    
    # Check if url is valid
    if not is_valid_youtube_url(url):
        update_feedback("Enter a Valid YouTube URL")
        return None

    try:
        yt = YouTube(url)  # Create a YouTube object
        toggle_info_section(True)  # Show video info section

        # Get various streams
        full_stream = yt.streams.get_highest_resolution(progressive=True)  # Full video stream
        video_stream = yt.streams.get_highest_resolution(progressive=False)  # Video stream without audio
        audio_streams = yt.streams.filter(only_audio=True)  # Audio-only streams
        highest_bitrate_stream = max(audio_streams, key=lambda stream: int(stream.abr.replace('kbps', '')))  # Highest bitrate audio stream
        
        # Update the labels with video details
        title_label.configure(text=f"{yt.title}")
        video_resolution_label.configure(text=f"Highest MP4 Resolution: {video_stream.resolution}")
        audio_resolution_label.configure(text=f"Highest MP3 Bitrate: {highest_bitrate_stream.abr}")
        full_stream_label.configure(text=f"Legacy Format (Video & Audio): {full_stream.resolution}")

        # Enable buttons for download options
        for button in [button1, button2, button3]:
            button.configure(state=ctk.NORMAL)
        
        return full_stream, video_stream, highest_bitrate_stream
    except Exception as e:
        update_feedback(f"Error: {e}")
        return None

# Function to handle the event when the user presses Enter in the entry field
def on_return_entry(event):
    """
    Handles the event when the user presses Enter in the entry field.
    
    Parameters:
    - event: The event object associated with the Enter key press.
    """
    url = entry.get().strip()  # Get and clean URL from the entry field
    if len(url) >= VIDEO_ID_LENGTH:
        fetch_data = fetch_details(url) # Fetch video details and display
        if fetch_data:
            update_feedback("Choose Download Type")
    else:
        update_feedback("Enter a Valid YouTube URL")

entry.bind("<Return>", on_return_entry)  # Bind Enter key to the on_return_entry function

# Function to update feedback message and optionally provide a file path link
def update_feedback(message, file_path=None):
    feedback_label.configure(text=message)
    feedback_label.grid(row=3, column=1, padx=5, pady=5)  # Display feedback label
    if file_path:
        feedback_label.configure(cursor="hand2")  # Change cursor to hand for clickable text
        feedback_label.bind("<Button-1>", lambda e: open_directory(file_path))
    else:
        feedback_label.configure(cursor="")
        feedback_label.unbind("<Button-1>")

# Function to open the directory where the file is saved
def open_directory(file_path):
    directory = os.path.dirname(file_path)  # Get the directory of the file
    try:
        if os.name == 'nt':  # Windows
            os.startfile(directory)
        elif os.name == 'posix':  # macOS or Linux
            if sys.platform == 'darwin':
                subprocess.run(["open", directory], check=True)  # macOS
            else:
                subprocess.run(["xdg-open", directory], check=True)  # Linux
    except Exception as e:
        update_feedback(f"Error opening directory: {e}")

# Function to handle the download process in a separate thread
def download_handler(stream, filename, message):
    def run():
        try:
            file_path = os.path.join(os.getcwd(), filename)  # Define where the file will be saved
            stream.download(filename=filename)  # Download the stream
            update_feedback(f"{file_path}", file_path)  # Update feedback with file path
        except Exception as e:
            update_feedback(f"Error: {e}")
        finally:
            global downloading
            downloading = False  # Reset the downloading flag

    threading.Thread(target=run).start()  # Start the download in a new thread

# Function to start the download based on the selected type
def download(type_key):
    url = entry.get().strip()  # Get URL from the entry field
    if not is_valid_youtube_url(url):
        update_feedback("Enter a Valid YouTube URL")
        return

    # Toggle downloading flag
    global downloading
    downloading = True
    fetch_data = fetch_details(url)  # Fetch video details
    
    if fetch_data:
        # Choose the appropriate stream and filename based on the download type
        if type_key == "legacy":
            stream, filename = fetch_data[0], DOWNLOAD_TYPES[type_key]
        elif type_key == "mp4":
            stream, filename = fetch_data[1], DOWNLOAD_TYPES[type_key]
        elif type_key == "mp3":
            stream, filename = fetch_data[2], DOWNLOAD_TYPES[type_key]
        
        update_feedback(f"Downloading {type_key.upper()} @ {stream.resolution if type_key != 'mp3' else stream.abr}...")
        download_handler(stream, filename, f"Downloading {type_key.upper()}...")

# Create a label for displaying feedback messages
feedback_label = ctk.CTkLabel(frame, text="", text_color="gold")
feedback_label.grid(row=3, column=1, padx=5, pady=5)
feedback_label.grid_forget()  # Initially hide the feedback label

# Function to create a button with text and command
def create_button(text, command):
    return ctk.CTkButton(frame, text=text, command=command, font=DEFAULT_BTN_FONT)

# Default button font style
DEFAULT_BTN_FONT = ("Comfortaa", 13)

# Create download buttons and place them in the grid
button1 = create_button("MP4", lambda: download("mp4"))
button1.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
button1.configure(state=ctk.DISABLED)  # Initially disable the button

button2 = create_button("Legacy", lambda: download("legacy"))
button2.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
button2.configure(state=ctk.DISABLED)  # Initially disable the button

button3 = create_button("MP3", lambda: download("mp3"))
button3.grid(row=4, column=2, padx=5, pady=5, sticky="ew")
button3.configure(state=ctk.DISABLED)  # Initially disable the button

# Configure the grid layout to adjust row and column weights
frame.grid_rowconfigure(1, weight=1)
frame.grid_rowconfigure(2, weight=0)
frame.grid_rowconfigure(4, weight=0)
frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)
frame.columnconfigure(2, weight=1)

# Start the main event loop to run the application
app.mainloop()