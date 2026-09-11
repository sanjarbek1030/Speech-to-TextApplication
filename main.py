"""
Speech-to-Subtitles Video Generator
====================================
What this script does, in plain English:

    1. Opens "input.mp4" and pulls out just the audio track.
    2. Feeds that audio to Whisper (a free, open-source speech-to-text model
       that runs entirely on YOUR computer -- no internet, no paid API).
    3. Whisper gives us back the spoken text PLUS the exact start/end time
       of each sentence.
    4. We take the original video and "stamp" each sentence onto it at the
       right moment in time, like subtitles.
    5. We save the final result as "output_subtitled.mp4".

BEFORE YOU RUN THIS (do this once, in PyCharm's Terminal tab at the bottom):

    pip install moviepy
    pip install openai-whisper
    pip install imageio-ffmpeg

You also need ffmpeg installed on your actual computer (not just the Python
package). See the TROUBLESHOOTING section at the very bottom of this file.

Put a video called "input.mp4" in the same folder as this script, then just
click the green "Run" arrow in PyCharm.
"""

# --- Imports -----------------------------------------------------------
# whisper = the speech-to-text engine
import whisper

# These come from moviepy and let us edit video/audio in Python
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import os
import shutil
import imageio_ffmpeg

# Find the ffmpeg exe that imageio_ffmpeg downloaded
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)

# Make a copy of it literally named "ffmpeg.exe" (Whisper looks for this exact name)
ffmpeg_named_correctly = os.path.join(ffmpeg_dir, "ffmpeg.exe")
if not os.path.exists(ffmpeg_named_correctly):
    shutil.copy(ffmpeg_exe, ffmpeg_named_correctly)

# Add that folder to PATH so Whisper can find "ffmpeg.exe"
os.environ["PATH"] += os.pathsep + ffmpeg_dir

# -------------------------------------------------------------------------
# STEP 1: Extract the audio from the video
# -------------------------------------------------------------------------
def extract_audio(video_path, audio_output_path="extracted_audio.wav"):
    """
    Takes a video file, pulls out ONLY the sound, and saves it as its own
    audio file. Whisper needs an audio file to work with, not a video file.
    """
    print("Step 1: Extracting audio from video...")

    video = VideoFileClip(video_path)                 # load the whole video into memory
    video.audio.write_audiofile(audio_output_path)     # save just the sound track to disk
    video.close()                                       # release the file so it's not "locked"

    print(f"  -> Audio saved to: {audio_output_path}")
    return audio_output_path


# -------------------------------------------------------------------------
# STEP 2: Transcribe the audio into text with timestamps
# -------------------------------------------------------------------------
def transcribe_audio(audio_path, model_size="base"):
    """
    Loads a local Whisper model and converts speech -> text.

    model_size options (bigger = more accurate but slower):
        "tiny"  -> fastest, least accurate, smallest download
        "base"  -> good balance for beginners (recommended)
        "small", "medium", "large" -> more accurate, much slower on a CPU

    Returns a list of "segments". Each segment is a small dictionary like:
        {"start": 1.2, "end": 3.8, "text": " Hello, welcome back."}
    """
    print(f"Step 2: Loading Whisper model ('{model_size}')...")
    model = whisper.load_model(model_size)   # downloads the model the first time you run this

    print("  -> Transcribing audio (this can take a while, be patient)...")
    result = model.transcribe(audio_path)     # this is where the actual speech recognition happens

    segments = result["segments"]             # a list of {start, end, text} dictionaries
    print(f"  -> Done! Found {len(segments)} sentence/segment chunks.")
    return segments


# -------------------------------------------------------------------------
# STEP 3: Overlay the text onto the video as subtitles
# -------------------------------------------------------------------------
def overlay_subtitles(video_path, segments, output_path="output_subtitled.mp4"):
    """
    Takes the original video plus the list of transcribed segments, and
    creates one small text clip per segment, timed to appear and disappear
    exactly when that sentence is spoken. Then it "flattens" everything
    (video + all the text clips) into one final video file.
    """
    print("Step 3: Building the subtitle text clips...")
    video = VideoFileClip(video_path)

    subtitle_clips = []  # we will fill this with one TextClip per sentence

    for segment in segments:
        start_time = segment["start"]           # when this sentence starts, in seconds
        end_time = segment["end"]               # when this sentence ends, in seconds
        text = segment["text"].strip()          # the actual words, with extra spaces removed
        duration = end_time - start_time        # how long this subtitle should stay on screen

        # Create one piece of subtitle text.
        # "method='caption'" makes long lines automatically wrap instead of
        # running off the edge of the screen.
        txt_clip = TextClip(
            text=text,
            font_size=40,
            color="white",
            stroke_color="black",      # a thin black outline makes text readable
            stroke_width=1,            # on any background color
            size=(int(video.w * 0.9), None),   # cap the width at 90% of video width
            method="caption",
        )

        # Tell moviepy WHERE on screen and WHEN in time this text should appear.
        txt_clip = (
            txt_clip
            .with_position(("center", 0.85), relative=True)  # 85% down the screen, not flush at the bottom
            .with_start(start_time)
            .with_duration(duration)
        )

        subtitle_clips.append(txt_clip)

    print("Step 4: Combining the original video with all subtitle clips...")
    # CompositeVideoClip layers everything on top of each other:
    # the original video on the bottom, and every subtitle clip on top.
    final_video = CompositeVideoClip([video] + subtitle_clips)

    print(f"Step 5: Exporting final video to '{output_path}'...")
    print("  (This is usually the slowest step -- just let it run.)")
    final_video.write_videofile(
        output_path,
        codec="libx264",     # a standard, widely-supported video format
        audio_codec="aac",   # a standard, widely-supported audio format
        fps=video.fps,       # keep the same frame rate as the original video
    )

    # Always close clips when you're done, to free memory and unlock files
    video.close()
    final_video.close()

    print("All done! Open 'output_subtitled.mp4' to see your result.")


# -------------------------------------------------------------------------
# MAIN: this runs all three steps in order
# -------------------------------------------------------------------------
def main():
    input_video = "input.mp4"

    # 1) Get the audio out of the video
    audio_file = extract_audio(input_video)

    # 2) Turn that audio into text + timestamps using Whisper
    segments = transcribe_audio(audio_file, model_size="base")

    # 3) Stamp the text onto the video and save the final result
    overlay_subtitles(input_video, segments, output_path="output_subtitled.mp4")


if __name__ == "__main__":
    main()


# =========================================================================
# TROUBLESHOOTING TIPS
# =========================================================================
#
# ERROR mentioning "ffmpeg" (e.g. "ffmpeg not found" or "No such file"):
#   - moviepy needs the real ffmpeg program installed on your computer,
#     not just the Python package.
#   - Easiest fix: run  pip install imageio-ffmpeg
#     This installs a private copy of ffmpeg that moviepy can find
#     automatically -- no system install needed.
#   - Alternative: install ffmpeg yourself and make sure it's on your
#     system PATH (search "install ffmpeg Windows/Mac" for a guide).
#
# ERROR mentioning "ImageMagick" or "convert" (older moviepy versions,
# 1.x, use ImageMagick to draw text -- newer moviepy 2.x versions do not
# usually need it, since they draw text with Pillow instead):
#   - Install ImageMagick from https://imagemagick.org/script/download.php
#   - On Windows, after installing, open ImageMagick's "policy.xml" file
#     and make sure there is no line that blocks "text" or "@" -- some
#     default installs restrict this for security reasons.
#   - You may also need to tell moviepy exactly where ImageMagick lives:
#         from moviepy.config import change_settings
#         change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.x\magick.exe"})
#     Put this near the top of the script, before you create any TextClip.
#
# ERROR about a missing font, or subtitles look wrong:
#   - You can point TextClip at a specific font file on your system, e.g.
#         TextClip(text=text, font="C:/Windows/Fonts/arial.ttf", ...)
#
# Whisper feels very slow:
#   - Switch model_size from "base" to "tiny" in transcribe_audio() -- it's
#     faster but slightly less accurate. This is normal on a CPU-only
#     computer; a GPU speeds this up a lot if you have one set up.
# =========================================================================
