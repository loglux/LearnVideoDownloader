import argparse
import re
from learn_video_helper import VideoDownloader


def generate_urls(base_url, num_links):
    urls = []
    match = re.search(r'(\d+)([a-zA-Z]*)$', base_url)
    if match:
        numeric_part = 1  # starting from 1
        alphabetic_part = match.group(2)
        prefix = base_url[:-len(match.group(0))]

        for i in range(num_links):
            urls.append(f"{prefix}{numeric_part + i}{alphabetic_part}")
    return urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download videos from Microsoft Learn.')
    parser.add_argument('base_url', type=str, help='Base URL for the modules')
    parser.add_argument('num_links', type=int, help='Number of links to generate')
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/') # remove trailing slash
    num_links = args.num_links

    urls = generate_urls(base_url, num_links)
    preferred_languages = ['en-us', 'ru-ru']

    for url in urls:
        print(url)
        downloader = VideoDownloader(url)
        downloader.run(
            download_high_quality=True,
            download_medium_quality=False,
            download_low_quality=False,
            download_audio=True,
            download_captions=True,
            preferred_languages=preferred_languages
        )
