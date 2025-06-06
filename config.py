import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base directory for all downloads
BASE_DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', os.path.join(os.path.dirname(__file__), 'downloads'))

# Create the base directory if it doesn't exist
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

# Specific directories for different types of content
VIDEOS_DIR = os.path.join(BASE_DOWNLOAD_DIR, 'videos')
AUDIOS_DIR = os.path.join(BASE_DOWNLOAD_DIR, 'audios')
SUBTITLES_DIR = os.path.join(BASE_DOWNLOAD_DIR, 'subtitles')

# Create all subdirectories
for directory in [VIDEOS_DIR, AUDIOS_DIR, SUBTITLES_DIR]:
    os.makedirs(directory, exist_ok=True) 