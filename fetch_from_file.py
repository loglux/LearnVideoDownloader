import argparse
from learn_video_helper import VideoDownloader


def process_links_from_file(file_path, preferred_languages):
    with open(file_path, 'r') as file:
        links = file.readlines()

    for link in links:
        link = link.strip()
        print(f"Processing link: {link}")

        downloader = VideoDownloader(link)
        downloader.run(
            download_high_quality=True,
            download_medium_quality=False,
            download_low_quality=False,
            download_audio=True,
            download_captions=True,
            preferred_languages=preferred_languages
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download videos from Microsoft Learn.')
    parser.add_argument('file_path', type=str, help='Path to the text file containing links')
    parser.add_argument('--languages', nargs='+', default=['en-us'], help='Preferred languages for subtitles')
    args = parser.parse_args()

    file_path = args.file_path
    preferred_languages = args.languages

    process_links_from_file(file_path, preferred_languages)
