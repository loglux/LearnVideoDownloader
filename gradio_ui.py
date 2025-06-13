import gradio as gr
from fetch_from_file import process_links_from_file
from learn_video_helper import VideoDownloader
from url_generator import generate_urls_from_pattern
import tempfile
import os
import io
import sys
from tqdm import tqdm  # keep tqdm for CLI

choices = [
    "en-us",
    "ru-ru",
    "zh-cn",
    "zh-tw",
    "ko-kr",
    "it-it",
    "pt-pt",
    "ja-jp",
    "pl-pl",
    "de-de",
    "cs-cz",
    "es-es",
    "fr-fr"
]

default_download_types = ["Video", "Audio", "Subtitles"]

def process_manual_urls_stream(urls_text, languages, download_types):
    """Process manual URLs with streaming updates"""
    urls = [url.strip() for url in urls_text.strip().splitlines() if url.strip()]
    total = len(urls)

    if not urls:
        yield "❌ No URLs provided", 0
        return

    download_high_quality = "Video" in download_types
    download_audio = "Audio" in download_types
    download_captions = "Subtitles" in download_types

    for idx, url in enumerate(urls, 1):
        log_lines = [f"🔗 Processing URL {idx}/{total}: {url}"]
        yield "\n".join(log_lines), int((idx - 1) / total * 100)

        def callback(msg):
            log_lines.append(msg)

        try:
            downloader = VideoDownloader(url)
            for percent in run_with_yield_callback(
                downloader,
                languages,
                download_high_quality,
                download_audio,
                download_captions,
                callback
            ):
                yield "\n".join(log_lines), max(percent, int((idx - 1) / total * 100))
        except Exception as e:
            log_lines.append(f"❌ Error: {e}")
            yield "\n".join(log_lines), int((idx - 1) / total * 100)

        log_lines.append("✅ Done")
        yield "\n".join(log_lines), int(idx / total * 100)

def run_with_yield_callback(
    downloader,
    languages,
    download_high_quality,
    download_audio,
    download_captions,
    callback_fn
):
    """Run downloader with streaming progress updates"""
    last_percent = 0

    def progress(msg):
        nonlocal last_percent
        if "—" in msg:
            try:
                _, percent = msg.rsplit("—", 1)
                last_percent = float(percent.strip("% "))
            except Exception:
                pass
        callback_fn(msg)
        return last_percent

    def yield_msg(msg):
        percent = progress(msg)
        yield percent

    def wrapped():
        def inner_callback(msg):
            for p in yield_msg(msg):
                yield p

        # Fixed: proper callback handling
        try:
            downloader.run_with_callback(
                download_high_quality=download_high_quality,
                download_medium_quality=False,  # Always False - smart fallback in VideoDownloader
                download_low_quality=False,     # Always False - smart fallback in VideoDownloader
                download_audio=download_audio,
                download_captions=download_captions,
                preferred_languages=languages,
                progress_callback=lambda msg: [inner_callback(msg)]  # Fixed callback
            )
            yield 100
        except Exception as e:
            callback_fn(f"❌ Download failed: {e}")
            yield 0

    yield from wrapped()

def process_generated_urls_stream(sample_url1, sample_url2, num_links, languages, download_types):
    """Generate URLs and process with streaming updates"""
    # First generate URLs
    urls = generate_urls_from_pattern(sample_url1.strip(), sample_url2.strip(), num_links)

    if not urls:
        yield "❌ Error: Could not generate URLs. Please check that the sample URLs have a changing numeric pattern.", 0
        return

    # Show generated URLs
    log_lines = [f"✅ Generated {len(urls)} URLs:"]
    for i, url in enumerate(urls, 1):
        log_lines.append(f"  {i}. {url}")
    log_lines.append("")  # Empty line
    yield "\n".join(log_lines), 5

    # Now process them
    download_high_quality = "Video" in download_types
    download_audio = "Audio" in download_types
    download_captions = "Subtitles" in download_types

    total = len(urls)
    for idx, url in enumerate(urls, 1):
        log_lines.append(f"🔗 Processing URL {idx}/{total}: {url}")
        yield "\n".join(log_lines), int(5 + (idx - 1) / total * 95)

        def callback(msg):
            log_lines.append(msg)

        try:
            downloader = VideoDownloader(url)
            for percent in run_with_yield_callback(
                downloader,
                languages,
                download_high_quality,
                download_audio,
                download_captions,
                callback
            ):
                current_progress = int(5 + (idx - 1) / total * 95 + percent / total * 0.95)
                yield "\n".join(log_lines), current_progress
        except Exception as e:
            log_lines.append(f"❌ Error: {e}")
            yield "\n".join(log_lines), int(5 + (idx - 1) / total * 95)

        log_lines.append("✅ Done")
        log_lines.append("")  # Empty line for readability
        yield "\n".join(log_lines), int(5 + idx / total * 95)

def process_from_file_stream(file_obj, languages, download_types):
    """Process file with streaming updates"""
    if not file_obj:
        yield "❌ No file uploaded", 0
        return

    # Create temp file and read URLs
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        with open(file_obj.name, 'r', encoding='utf-8') as f:
            content = f.read()

    try:
        urls = [line.strip() for line in content.splitlines() if line.strip()]
        if not urls:
            yield "❌ No valid URLs found in file", 0
            return

        log_lines = [f"📁 Processing file: {file_obj.name}"]
        log_lines.append(f"📋 Found {len(urls)} URLs")
        log_lines.append("")
        yield "\n".join(log_lines), 5

        download_high_quality = "Video" in download_types
        download_audio = "Audio" in download_types
        download_captions = "Subtitles" in download_types

        total = len(urls)
        for idx, url in enumerate(urls, 1):
            log_lines.append(f"🔗 Processing URL {idx}/{total}: {url}")
            yield "\n".join(log_lines), int(5 + (idx - 1) / total * 95)

            def callback(msg):
                log_lines.append(msg)

            try:
                downloader = VideoDownloader(url)
                for percent in run_with_yield_callback(
                    downloader,
                    languages,
                    download_high_quality,
                    download_audio,
                    download_captions,
                    callback
                ):
                    current_progress = int(5 + (idx - 1) / total * 95 + percent / total * 0.95)
                    yield "\n".join(log_lines), current_progress
            except Exception as e:
                log_lines.append(f"❌ Error: {e}")
                yield "\n".join(log_lines), int(5 + (idx - 1) / total * 95)

            log_lines.append("✅ Done")
            log_lines.append("")  # Empty line
            yield "\n".join(log_lines), int(5 + idx / total * 95)

    except Exception as e:
        yield f"❌ Error processing file: {e}", 0
    finally:
        os.remove(temp_path)

# Create interface - KEEP SAME LAYOUT AS CURRENT
with gr.Blocks() as demo:
    gr.Markdown("# Microsoft Learn Downloader Interface\nChoose a method to download videos, audio, and subtitles.")

    with gr.Tab("Manual URL List"):
        urls_input = gr.Textbox(
            label="Enter URLs (one per line)",
            lines=5,
            placeholder="https://learn.microsoft.com/...\nhttps://learn.microsoft.com/..."
        )
        langs_input1 = gr.CheckboxGroup(
            label="Preferred Subtitle Languages",
            choices=choices,
            value=["en-us"]
        )
        download_types1 = gr.CheckboxGroup(
            label="What to download?",
            choices=["Video", "Audio", "Subtitles"],
            value=default_download_types
        )
        log_output1 = gr.Textbox(label="Logs", lines=2, max_lines=20)
        progress1 = gr.Slider(minimum=0, maximum=100, label="Overall Progress")
        btn1 = gr.Button("Download")
        btn1.click(
            fn=process_manual_urls_stream,
            inputs=[urls_input, langs_input1, download_types1],
            outputs=[log_output1, progress1]
        )

    with gr.Tab("Generate from Base URL"):
        gr.Markdown(
            "### Enter two sample URLs that show the pattern\n"
            "For example:\n"
            "    https://learn.microsoft.com/.../module-4\n"
            "    https://learn.microsoft.com/.../module-5\n"
            "The tool will detect the changing number pattern and generate a sequence starting from 1.\n"
            "For example, if you enter module-4 and module-5 and request 3 URLs, you'll get:\n"
            "    .../module-1\n"
            "    .../module-2\n"
            "    .../module-3"
        )
        sample_url1_input = gr.Textbox(
            label="First Sample URL",
            placeholder="https://learn.microsoft.com/.../module-4"
        )
        sample_url2_input = gr.Textbox(
            label="Second Sample URL",
            placeholder="https://learn.microsoft.com/.../module-5"
        )
        count_input = gr.Number(
            label="Number of URLs to Generate (starting from 1)",
            precision=0,
            value=5
        )
        langs_input2 = gr.CheckboxGroup(
            label="Preferred Subtitle Languages",
            choices=choices,
            value=["en-us"]
        )
        download_types2 = gr.CheckboxGroup(
            label="What to download?",
            choices=["Video", "Audio", "Subtitles"],
            value=default_download_types
        )
        log_output2 = gr.Textbox(label="Logs", lines=2, max_lines=20)  # Fixed: more lines
        progress2 = gr.Slider(minimum=0, maximum=100, label="Overall Progress")
        btn2 = gr.Button("Generate and Download")
        btn2.click(
            fn=process_generated_urls_stream,
            inputs=[sample_url1_input, sample_url2_input, count_input, langs_input2, download_types2],
            outputs=[log_output2, progress2]
        )

    with gr.Tab("Upload File"):
        file_input = gr.File(label="Upload .txt file with URLs")
        langs_input3 = gr.CheckboxGroup(
            label="Preferred Subtitle Languages",
            choices=choices,
            value=["en-us"]
        )
        download_types3 = gr.CheckboxGroup(
            label="What to download?",
            choices=["Video", "Audio", "Subtitles"],
            value=default_download_types
        )
        log_output3 = gr.Textbox(label="Logs", lines=2, max_lines=20)  # Fixed: more lines
        progress3 = gr.Slider(minimum=0, maximum=100, label="Overall Progress")
        btn3 = gr.Button("Download from File")
        btn3.click(
            fn=process_from_file_stream,
            inputs=[file_input, langs_input3, download_types3],
            outputs=[log_output3, progress3]
        )

if __name__ == "__main__":
    demo.launch()