import gradio as gr
from fetch_from_file import process_links_from_file
from learn_video_helper import VideoDownloader
from url_generator import generate_urls_from_pattern
import tempfile
import os
import io
import sys
from tqdm import tqdm  # keep tqdm for CLI


def process_manual_urls_stream(urls_text, languages):
    urls = [url.strip() for url in urls_text.strip().splitlines() if url.strip()]
    total = len(urls)

    for idx, url in enumerate(urls, 1):
        log_lines = [f"🔗 Processing URL {idx}/{total}: {url}"]
        yield "\n".join(log_lines), int((idx - 1) / total * 100)

        def callback(msg):
            log_lines.append(msg)

        try:
            downloader = VideoDownloader(url)
            for percent in run_with_yield_callback(downloader, languages, callback):
                yield "\n".join(log_lines), percent
        except Exception as e:
            log_lines.append(f"❌ Error: {e}")
            yield "\n".join(log_lines), int((idx - 1) / total * 100)

        log_lines.append("✅ Done")
        yield "\n".join(log_lines), int((idx) / total * 100)


def run_with_yield_callback(downloader, languages, callback_fn):
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

        downloader.run_with_callback(
            download_high_quality=True,
            download_medium_quality=False,
            download_low_quality=False,
            download_audio=True,
            download_captions=True,
            preferred_languages=languages,
            progress_callback=lambda msg: None if inner_callback(msg) is None else None
        )
        yield 100

    yield from wrapped()


def process_generated_urls_stream(sample_url1, sample_url2, num_links, languages):
    # Generate URLs using the new pattern-based generator
    urls = generate_urls_from_pattern(sample_url1.strip(), sample_url2.strip(), num_links)

    if not urls:
        yield "❌ Error: Could not generate URLs. Please check that the sample URLs have a changing numeric pattern.", 0
        return

    total = len(urls)
    for idx, url in enumerate(urls, 1):
        log_lines = [f"🔗 Processing URL {idx}/{total}: {url}"]
        yield "\n".join(log_lines), int((idx - 1) / total * 100)

        def callback(msg):
            log_lines.append(msg)

        try:
            downloader = VideoDownloader(url)
            for percent in run_with_yield_callback(downloader, languages, callback):
                yield "\n".join(log_lines), percent
        except Exception as e:
            log_lines.append(f"❌ Error: {e}")
            yield "\n".join(log_lines), int((idx - 1) / total * 100)

        log_lines.append("✅ Done")
        yield "\n".join(log_lines), int(idx / total * 100)


def process_from_file_stream(file_obj, languages):
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(file_obj.read().decode('utf-8'))
        temp_path = temp_file.name

    buffer = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buffer

    try:
        process_links_from_file(temp_path, languages)
    except Exception as e:
        yield f"❌ Error: {e}", None
    finally:
        sys.stdout = sys_stdout
        os.remove(temp_path)
        yield buffer.getvalue(), 100


with gr.Blocks() as demo:
    gr.Markdown("""# Microsoft Learn Downloader Interface
Choose a method to download videos, audio, and subtitles.""")

    with gr.Tab("Manual URL List"):
        urls_input = gr.Textbox(label="Enter URLs (one per line)", lines=5,
                                placeholder="https://learn.microsoft.com/...\nhttps://learn.microsoft.com/...")
        langs_input1 = gr.CheckboxGroup(label="Preferred Subtitle Languages", choices = [
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
,
                                        value=["en-us"])
        log_output1 = gr.Textbox(label="Logs", lines=20)
        progress1 = gr.Slider(minimum=0, maximum=100, label="Overall Progress")
        btn1 = gr.Button("Download")
        btn1.click(fn=process_manual_urls_stream, inputs=[urls_input, langs_input1], outputs=[log_output1, progress1])

    with gr.Tab("Generate from Base URL"):
        gr.Markdown("""### Enter two sample URLs that show the pattern
For example:
```
https://learn.microsoft.com/.../module-4
https://learn.microsoft.com/.../module-5
```
The tool will detect the changing number pattern and generate a sequence starting from 1.
For example, if you enter module-4 and module-5 and request 3 URLs, you'll get:
```
.../module-1
.../module-2
.../module-3
```""")
        sample_url1_input = gr.Textbox(label="First Sample URL", placeholder="https://learn.microsoft.com/.../module-4")
        sample_url2_input = gr.Textbox(label="Second Sample URL",
                                       placeholder="https://learn.microsoft.com/.../module-5")
        count_input = gr.Number(label="Number of URLs to Generate (starting from 1)", precision=0, value=5)
        langs_input2 = gr.CheckboxGroup(label="Preferred Subtitle Languages", choices=["en-us", "ru-ru"],
                                        value=["en-us"])
        log_output2 = gr.Textbox(label="Logs", lines=20)
        progress2 = gr.Slider(minimum=0, maximum=100, label="Overall Progress")
        btn2 = gr.Button("Generate and Download")
        btn2.click(fn=process_generated_urls_stream,
                   inputs=[sample_url1_input, sample_url2_input, count_input, langs_input2],
                   outputs=[log_output2, progress2])

    with gr.Tab("Upload File"):
        file_input = gr.File(label="Upload .txt file with URLs")
        langs_input3 = gr.CheckboxGroup(label="Preferred Subtitle Languages", choices=["en-us", "ru-ru"],
                                        value=["en-us"])
        log_output3 = gr.Textbox(label="Logs", lines=20)
        progress3 = gr.Slider(minimum=0, maximum=100, label="Overall Progress")
        btn3 = gr.Button("Download from File")
        btn3.click(fn=process_from_file_stream, inputs=[file_input, langs_input3], outputs=[log_output3, progress3])

if __name__ == "__main__":
    demo.launch()
