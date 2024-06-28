# LearnVideoDownloader

*LearnVideoDownloader* is a Python script designed to download videos, audios and subtitles from the Microsoft Learn platform. The script allows users to specify the quality of videos and the preferred languages for subtitles.

## Features

- Download videos in high, medium, or low quality.
- Download audio files.
- Download subtitles in specified languages.
- Fetches video and subtitle URLs from the Microsoft Learn platform.

## Requirements

- Python 3.x
- Requests library
- BeautifulSoup library

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/LearnVideoDownloader.git
```

Navigate to the project directory:

```bash
cd LearnVideoDownloader
```

Install the required libraries:
```bash
pip install requests beautifulsoup4
```
## Usage
Edit the urls list in the script to include the URLs of the Microsoft Learn videos you want to download.

Set your preferred languages for subtitles by modifying the preferred_languages list.

Run the script:
``` bash
python learn_video_helper.py
```
Example
```python

if __name__ == "__main__":
    urls = [
        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-1/",
        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-2/",
        # Add more URLs as needed
    ]
    preferred_languages = ['en-us', 'ru-ru']  # Example preferred languages: English and Russian subtitles
    for url in urls:
        downloader = VideoDownloader(url)
        downloader.run(download_high_quality=True,
                       download_medium_quality=False,
                       download_low_quality=False,
                       download_audio=True,
                       download_captions=True,
                       preferred_languages=preferred_languages)
```
## License
This project is licensed under the MIT License.
