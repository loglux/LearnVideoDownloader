import argparse
from learn_video_helper import VideoDownloader

def generate_urls(base_url, num_links):
    urls = [f"{base_url}{i}" for i in range(1, num_links + 1)]
    return urls

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download videos from Microsoft Learn.')
    parser.add_argument('base_url', type=str, help='Base URL for the modules')
    parser.add_argument('num_links', type=int, help='Number of links to generate')
    args = parser.parse_args()

    base_url = args.base_url
    num_links = args.num_links

    urls = generate_urls(base_url, num_links)
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
