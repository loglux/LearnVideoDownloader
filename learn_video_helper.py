import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urlparse
from tqdm import tqdm


class VideoDownloader:
    def __init__(self, url):
        self.url = url

    def fetch_entry_id_and_title(self):
        print("🌍 Отправка запроса на URL... 🔄")
        response = requests.get(self.url)
        if response.status_code != 200:
            print(f"❌ Ошибка при загрузке страницы: {response.status_code}")
            return None, None

        print("🧐 Парсинг HTML страницы... 📄")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение entryId
        entry_id_meta = soup.find('meta', {'name': 'entryId'})
        entry_id = entry_id_meta.get('content') if entry_id_meta else None

        # Извлечение заголовка
        title_meta = soup.find('meta', {'property': 'og:title'})
        title = title_meta.get('content') if title_meta else 'video'
        title = re.sub(r'[\\/*?:"<>|]', "", title)  # Удаление недопустимых для имени файла символов
        title = re.sub(r'\s+', " ", title) # Замена табуляции и нескольких пробелов одним пробелом

        if entry_id:
            print(f"🔍 Найден entryId: {entry_id}")
        else:
            print("❌ Не удалось найти entryId.")

        return entry_id, title

    def fetch_video_data(self, entry_id):
        api_url = f"https://learn.microsoft.com/api/video/public/v1/entries/{entry_id}?isAMS=false"
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Ошибка при получении данных: {response.status_code}")
            return None

    def download_file(self, file_url, output_path):
        print(f"📥 Скачивание файла из {file_url}...")
        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()  # Проверка на наличие ошибок HTTP
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 8192

            with open(output_path, 'wb') as f, tqdm(
                    total=total_size, unit='B', unit_scale=True, desc="Скачивание"
            ) as progress_bar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))

            print(f"✅ Файл {output_path} успешно скачан!")
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при скачивании файла: {e}")

    def get_file_extension(self, url):
        path = urlparse(url).path
        return os.path.splitext(path)[1]

    def run(self, download_high_quality=True, download_medium_quality=False, download_low_quality=False,
            download_audio=True, download_captions=True, preferred_languages=None):
        entry_id, title = self.fetch_entry_id_and_title()
        if entry_id:
            video_data = self.fetch_video_data(entry_id)
            if video_data:
                video_url = None

                if download_high_quality:
                    # Скачивание видео высокого качества
                    video_url = video_data['publicVideo']['highQualityVideoUrl']
                    if video_url:
                        self.download_file(video_url,
                                           f'videos/{title}_high_quality{self.get_file_extension(video_url)}')
                    else:
                        print("⚠️ Видео высокого качества не найдено.")

                if download_medium_quality or (download_high_quality and not video_url):
                    # Скачивание видео среднего качества, если эта опция включена или если видео высокого качества не найдено
                    medium_quality_video_url = video_data['publicVideo']['mediumQualityVideoUrl']
                    if medium_quality_video_url:
                        self.download_file(medium_quality_video_url,
                                           f'videos/{title}_medium_quality{self.get_file_extension(medium_quality_video_url)}')
                    else:
                        print("⚠️ Видео среднего качества не найдено.")

                if download_low_quality:
                    # Скачивание видео низкого качества
                    low_quality_video_url = video_data['publicVideo']['lowQualityVideoUrl']
                    if low_quality_video_url:
                        self.download_file(low_quality_video_url,
                                           f'videos/{title}_low_quality{self.get_file_extension(low_quality_video_url)}')
                    else:
                        print("⚠️ Видео низкого качества не найдено.")

                if download_audio:
                    # Скачивание аудио
                    audio_url = video_data['publicVideo']['audioUrl']
                    if audio_url:
                        self.download_file(audio_url, f'audios/{title}_audio{self.get_file_extension(audio_url)}')
                    else:
                        print("🔇 Аудио не найдено.")

                if download_captions:
                    # Скачивание субтитров
                    captions = video_data['publicVideo'].get('captions', [])
                    for caption in captions:
                        language = caption['language']
                        if preferred_languages is None or language in preferred_languages:
                            caption_url = caption['url']
                            self.download_file(caption_url,
                                               f'subtitles/{title}_{language}{self.get_file_extension(caption_url)}')
                        else:
                            print(f"⚠️ Субтитры на языке {language} не включены в предпочтительные.")
            else:
                print("❌ Не удалось получить данные видео.")
        else:
            print("❌ Не удалось найти URL для JSON API.")


if __name__ == "__main__":
    #url = "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-102-module-11"
    urls = [
        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-1/",
        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-2/",
        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-3/",
        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-4/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-5/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-6/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-7/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-8/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-9/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-10/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-11/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-12/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-13/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-14/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-15/",
#        "https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/ai-050-module-16/"
#        "https://learn.microsoft.com/en-us/shows/AI-Show/Bring-Anomaly-Detector-on-premise-with-containers-support"
        #"https://learn.microsoft.com/en-us/shows/on-demand-instructor-led-training-series/dp-600-module-19"
    ]
    preferred_languages = ['en-us', 'ru-ru']  # Пример предпочитаемых языков: английский и русский
    for url in urls:
        downloader = VideoDownloader(url)
        downloader.run(download_high_quality=True,
                       download_medium_quality=False,
                       download_low_quality=False,
                       download_audio=True,
                       download_captions=True,
                       preferred_languages=preferred_languages)
