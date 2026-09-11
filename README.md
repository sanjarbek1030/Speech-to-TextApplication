# Speech-to-Subtitles Video Generator

Automatically transcribe the spoken audio in a video and burn the result in as subtitles — no paid APIs, no internet required after setup. Everything runs locally using [OpenAI's Whisper](https://github.com/openai/whisper) (open-source) and [MoviePy](https://zulko.github.io/moviepy/).

## What it does

1. Extracts the audio track from `input.mp4`
2. Transcribes that audio locally with Whisper, capturing text **and** the start/end timestamp of each spoken segment
3. Overlays each segment as a subtitle on the video at the correct moment
4. Exports the result as `output_subtitled.mp4`

## Requirements

- Python 3.9+
- A video file named `input.mp4` in the project folder

## Installation

```bash
pip install moviepy openai-whisper imageio-ffmpeg
```

## Usage

1. Place your video in the project folder and name it `input.mp4`
2. Run the script:

```bash
python main.py
```

3. Once it finishes, `output_subtitled.mp4` will appear in the same folder

## Configuration

**Whisper model size** — change in `transcribe_audio(audio_file, model_size="base")`:

| Model    | Speed        | Accuracy  |
|----------|--------------|-----------|
| `tiny`   | Fastest      | Lowest    |
| `base`   | Balanced (default) | Good |
| `small` / `medium` / `large` | Slower | Higher |

**Subtitle vertical position** — in `overlay_subtitles()`:

```python
.with_position(("center", 0.85), relative=True)  # 0.0 = top, 1.0 = bottom
```

Lower the number to push subtitles up, raise it to push them down.

## Troubleshooting

**`FileNotFoundError: [WinError 2]` when transcribing (Windows)**
Whisper calls `ffmpeg` directly and can't find it on your PATH. Add this near the top of the script, before transcription runs:

```python
import os
import shutil
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)

ffmpeg_named_correctly = os.path.join(ffmpeg_dir, "ffmpeg.exe")
if not os.path.exists(ffmpeg_named_correctly):
    shutil.copy(ffmpeg_exe, ffmpeg_named_correctly)

os.environ["PATH"] += os.pathsep + ffmpeg_dir
```

If that still doesn't work, install ffmpeg system-wide: `winget install ffmpeg` (Windows, run PowerShell as Administrator), then restart PyCharm.

**ImageMagick-related errors when drawing text**
Only relevant on older MoviePy (1.x). Install ImageMagick, then point MoviePy to it:

```python
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.x\magick.exe"})
```

**`UserWarning: FP16 is not supported on CPU`**
Not an error — just Whisper letting you know it's running on CPU instead of GPU. Safe to ignore.

**Transcription is slow**
Normal on CPU-only machines. Switch `model_size` to `"tiny"` for a speed boost, at some cost to accuracy.

## License

MIT — feel free to use, modify, and share.
