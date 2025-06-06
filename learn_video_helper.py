import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urlparse
from tqdm import tqdm
from config import VIDEOS_DIR, AUDIOS_DIR, SUBTITLES_DIR

class VideoDownloader:
    def __init__(self, url):
        self.url = url

    def fetch_entry_id_and_title(self):
        print("🌍 Requesting URL... 🔄")
        response = requests.get(self.url)
        if response.status_code != 200:
            print(f"❌ Failed to load page: {response.status_code}")
            return None, None

        print("🧐 Parsing HTML content... 📄")
        soup = BeautifulSoup(response.text, 'html.parser')

        entry_id_meta = soup.find('meta', {'name': 'entryId'})
        entry_id = entry_id_meta.get('content') if entry_id_meta else None

        title_meta = soup.find('meta', {'property': 'og:title'})
        title = title_meta.get('content') if title_meta else 'video'
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        title = re.sub(r'\s+', " ", title)

        if entry_id:
            print(f"🔍 Found entryId: {entry_id}")
        else:
            print("❌ entryId not found.")

        return entry_id, title

    def fetch_video_data(self, entry_id):
        api_url = f"https://learn.microsoft.com/api/video/public/v1/entries/{entry_id}?isAMS=false"
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Failed to fetch video data: {response.status_code}")
            return None

    def download_file(self, file_url, output_path, progress_callback=None):
        print(f"📥 Downloading file from {file_url}...")
        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 8192
            downloaded = 0

            if progress_callback is None:
                with open(output_path, 'wb') as f, tqdm(
                    total=total_size, unit='B', unit_scale=True, desc="Downloading"
                ) as progress_bar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            progress_bar.update(len(chunk))
            else:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = downloaded / total_size * 100 if total_size else 0
                            progress_callback(f"{os.path.basename(output_path)} — {percent:.1f}%")

            msg = f"✅ Finished: {output_path}"
            if progress_callback:
                progress_callback(msg)
            else:
                print(msg)
        except requests.exceptions.RequestException as e:
            msg = f"❌ Error downloading file: {e}"
            if progress_callback:
                progress_callback(msg)
            else:
                print(msg)

    def get_file_extension(self, url):
        path = urlparse(url).path
        return os.path.splitext(path)[1]

    def run(self, download_high_quality=True, download_medium_quality=False, download_low_quality=False,
            download_audio=True, download_captions=True, preferred_languages=None):
        self._run_internal(
            download_high_quality,
            download_medium_quality,
            download_low_quality,
            download_audio,
            download_captions,
            preferred_languages,
            progress_callback=None
        )

    def run_with_callback(self, download_high_quality=True, download_medium_quality=False, download_low_quality=False,
                          download_audio=True, download_captions=True, preferred_languages=None,
                          progress_callback=None):
        self._run_internal(
            download_high_quality,
            download_medium_quality,
            download_low_quality,
            download_audio,
            download_captions,
            preferred_languages,
            progress_callback
        )

    def _run_internal(self, download_high_quality, download_medium_quality, download_low_quality,
                      download_audio, download_captions, preferred_languages, progress_callback):
        def log(msg):
            if progress_callback:
                progress_callback(msg)
            else:
                print(msg)

        entry_id, title = self.fetch_entry_id_and_title()
        if not entry_id:
            log("❌ Could not find entryId.")
            return

        video_data = self.fetch_video_data(entry_id)
        if not video_data:
            log("❌ Failed to fetch video data.")
            return

        # High quality video
        if download_high_quality:
            url = video_data['publicVideo'].get('highQualityVideoUrl')
            if url:
                self.download_file(url, os.path.join(VIDEOS_DIR, f'{title}_high_quality{self.get_file_extension(url)}'), progress_callback)
            else:
                log("⚠️ High quality video not found.")

        # Medium quality video (fallback)
        if download_medium_quality:
            url = video_data['publicVideo'].get('mediumQualityVideoUrl')
            if url:
                self.download_file(url, os.path.join(VIDEOS_DIR, f'{title}_medium_quality{self.get_file_extension(url)}'), progress_callback)
            else:
                log("⚠️ Medium quality video not found.")

        # Low quality video
        if download_low_quality:
            url = video_data['publicVideo'].get('lowQualityVideoUrl')
            if url:
                self.download_file(url, os.path.join(VIDEOS_DIR, f'{title}_low_quality{self.get_file_extension(url)}'), progress_callback)
            else:
                log("⚠️ Low quality video not found.")

        # Audio
        if download_audio:
            url = video_data['publicVideo'].get('audioUrl')
            if url:
                self.download_file(url, os.path.join(AUDIOS_DIR, f'{title}_audio{self.get_file_extension(url)}'), progress_callback)
            else:
                log("🔇 Audio not found.")

        # Captions
        if download_captions:
            captions = video_data['publicVideo'].get('captions', [])
            for caption in captions:
                language = caption['language']
                if preferred_languages is None or language in preferred_languages:
                    url = caption['url']
                    self.download_file(url, os.path.join(SUBTITLES_DIR, f'{title}_{language}{self.get_file_extension(url)}'), progress_callback)
                else:
                    log(f"⚠️ Skipping subtitle in {language}")


if __name__ == "__main__":
    urls = [
        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-4/",
    ]
    preferred_languages = ['en-us', 'ru-ru']
    for url in urls:
        downloader = VideoDownloader(url)
        downloader.run(
            download_high_quality=True,
            download_medium_quality=False,
            download_low_quality=False,
            download_audio=True,
            download_captions=True,
            preferred_languages=preferred_languages
        )
