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
        print(f"🔗 URL: {self.url}")  # Show the URL being processed

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
            data = response.json()

            # Enhanced diagnostic logging for available content
            if 'publicVideo' in data:
                video_info = data['publicVideo']
                available_qualities = []

                high_url = video_info.get('highQualityVideoUrl')
                medium_url = video_info.get('mediumQualityVideoUrl')
                low_url = video_info.get('lowQualityVideoUrl')
                audio_url = video_info.get('audioUrl')

                if high_url:
                    available_qualities.append('high')
                if medium_url:
                    available_qualities.append('medium')
                if low_url:
                    available_qualities.append('low')
                if audio_url:
                    available_qualities.append('audio')

                captions_count = len(video_info.get('captions', []))

                print(f"📊 Available content: {', '.join(available_qualities) if available_qualities else 'NONE'}")
                print(f"📝 Captions available: {captions_count}")

                # Show available languages if captions exist
                if captions_count > 0:
                    captions = video_info.get('captions', [])
                    languages = [caption['language'] for caption in captions]
                    print(f"🌐 Caption languages: {', '.join(languages)}")

            return data
        else:
            print(f"⚠️ Failed to fetch video data: {response.status_code}")
            return None

    def download_file(self, file_url, output_path, progress_callback=None):
        print(f"📥 Downloading file from {file_url}...")
        print(f"💾 Saving to: {output_path}")

        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 8192
            downloaded = 0

            # Show file size info
            if total_size > 0:
                size_mb = total_size / (1024 * 1024)
                print(f"📦 File size: {size_mb:.1f} MB")

            # ALWAYS show tqdm in console, regardless of progress_callback
            with open(output_path, 'wb') as f, tqdm(
                    total=total_size, unit='B', unit_scale=True, desc="Downloading"
            ) as progress_bar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))

                        # ALSO send progress to GUI if callback exists
                        if progress_callback:
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
        # print("🔥 run_with_callback CALLED!")  # Keep this debug line
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

        print("=" * 80)
        print(f"🚀 STARTING DOWNLOAD SESSION")
        print(f"🔗 URL: {self.url}")
        print("=" * 80)

        entry_id, title = self.fetch_entry_id_and_title()
        if not entry_id:
            log("❌ Could not find entryId")
            return

        print(f"📝 Video title: {title}")

        video_data = self.fetch_video_data(entry_id)
        if not video_data:
            log("❌ Failed to fetch video data")
            return

        if 'publicVideo' not in video_data:
            log("❌ No video data in response")
            return

        public_video = video_data['publicVideo']
        download_count = 0

        # Analyze available content
        high_url = public_video.get('highQualityVideoUrl')
        medium_url = public_video.get('mediumQualityVideoUrl')
        low_url = public_video.get('lowQualityVideoUrl')
        audio_url = public_video.get('audioUrl')
        captions = public_video.get('captions', [])

        # Show what will be downloaded
        print("\n" + "─" * 60)
        print("📋 DOWNLOAD PLAN:")
        print("─" * 60)
        print(f"🎬 Video: {'✅ YES' if download_high_quality else '❌ NO'}")
        print(f"🎵 Audio: {'✅ YES' if download_audio else '❌ NO'}")
        print(f"📝 Captions: {'✅ YES' if download_captions else '❌ NO'}")
        if preferred_languages:
            print(f"🌐 Languages: {', '.join(preferred_languages)}")
        print("─" * 60)

        # VIDEO PROCESSING with smart fallback
        wants_video = download_high_quality or download_medium_quality or download_low_quality

        if wants_video:
            print("\n🎬 PROCESSING VIDEO CONTENT...")
            print("📊 Quality analysis:")
            print(f"   🔴 High: {'✅ Available' if high_url else '❌ Not available'}")
            print(f"   🟡 Medium: {'✅ Available' if medium_url else '❌ Not available'}")
            print(f"   🟢 Low: {'✅ Available' if low_url else '❌ Not available'}")

            video_downloaded = False

            # ATTEMPT 1: HIGH quality
            if not video_downloaded and high_url:
                print("\n📹 Downloading HIGH quality...")
                try:
                    self.download_file(high_url, os.path.join(VIDEOS_DIR,
                                                              f'{title}_high_quality{self.get_file_extension(high_url)}'),
                                       progress_callback)
                    video_downloaded = True
                    download_count += 1
                    print("✅ HIGH quality downloaded successfully")
                except Exception as e:
                    print(f"❌ HIGH quality failed: {e}")

            # ATTEMPT 2: MEDIUM quality (fallback)
            if not video_downloaded and medium_url:
                if high_url:
                    print("\n🔄 Falling back to MEDIUM quality...")
                else:
                    print("\n📹 Downloading MEDIUM quality (best available)...")
                try:
                    self.download_file(medium_url, os.path.join(VIDEOS_DIR,
                                                                f'{title}_medium_quality{self.get_file_extension(medium_url)}'),
                                       progress_callback)
                    video_downloaded = True
                    download_count += 1
                    print("✅ MEDIUM quality downloaded successfully")
                except Exception as e:
                    print(f"❌ MEDIUM quality failed: {e}")

            # ATTEMPT 3: LOW quality (last fallback)
            if not video_downloaded and low_url:
                if high_url or medium_url:
                    print("\n🔄 Falling back to LOW quality...")
                else:
                    print("\n📹 Downloading LOW quality (only available)...")
                try:
                    self.download_file(low_url, os.path.join(VIDEOS_DIR,
                                                             f'{title}_low_quality{self.get_file_extension(low_url)}'),
                                       progress_callback)
                    video_downloaded = True
                    download_count += 1
                    print("✅ LOW quality downloaded successfully")
                except Exception as e:
                    print(f"❌ LOW quality failed: {e}")

            # Video download summary
            if not video_downloaded:
                print("❌ No video could be downloaded")
            else:
                print("🎬 Video download completed")

        # AUDIO PROCESSING
        if download_audio:
            print("\n🎵 PROCESSING AUDIO...")
            if audio_url:
                print("🎵 Downloading audio...")
                try:
                    self.download_file(audio_url,
                                       os.path.join(AUDIOS_DIR, f'{title}_audio{self.get_file_extension(audio_url)}'),
                                       progress_callback)
                    download_count += 1
                    print("✅ Audio downloaded successfully")
                except Exception as e:
                    print(f"❌ Audio failed: {e}")
            else:
                print("🔇 Audio not available")

        # CAPTIONS PROCESSING
        if download_captions:
            print("\n📝 PROCESSING CAPTIONS...")
            if captions:
                caption_count = 0
                preferred_str = ', '.join(preferred_languages) if preferred_languages else 'all'
                print(f"📝 Downloading captions (preferred: {preferred_str})...")

                for caption in captions:
                    language = caption['language']
                    if preferred_languages is None or language in preferred_languages:
                        url = caption['url']
                        print(f"   📥 Downloading {language} captions...")
                        try:
                            self.download_file(url, os.path.join(SUBTITLES_DIR,
                                                                 f'{title}_{language}{self.get_file_extension(url)}'),
                                               progress_callback)
                            caption_count += 1
                            print(f"   ✅ {language} captions downloaded")
                        except Exception as e:
                            print(f"   ❌ {language} captions failed: {e}")
                    else:
                        print(f"   ⏭️ Skipped {language} (not preferred)")

                if caption_count > 0:
                    download_count += caption_count
                    print(f"📝 Captions completed: {caption_count} files")
                else:
                    print("📝 No captions downloaded")
            else:
                print("📝 No captions available")

        # FINAL SUMMARY
        print("\n" + "=" * 80)
        print("🎉 DOWNLOAD SESSION COMPLETED")
        print("=" * 80)

        summary_parts = []
        if wants_video and video_downloaded:
            summary_parts.append("1 video")
        if download_audio and audio_url:
            summary_parts.append("1 audio")
        if download_captions and captions:
            downloaded_captions = len(
                [c for c in captions if preferred_languages is None or c['language'] in preferred_languages])
            if downloaded_captions > 0:
                summary_parts.append(f"{downloaded_captions} captions")

        if summary_parts:
            print(f"🎉 Files downloaded: {', '.join(summary_parts)}")
        else:
            print("⚠️ No files downloaded")

        print(f"📁 Files saved to: {os.path.dirname(VIDEOS_DIR)}")
        print("=" * 80)


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