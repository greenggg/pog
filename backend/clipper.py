import ffmpeg
import subprocess
import os

import sys
print(sys.executable)
print(sys.path)

def cut_clip(input_file, start, end, output_file):
    (
        ffmpeg
        .input(input_file, ss=start, to=end)
        .output(output_file)
        .run(overwrite_output=True)
    )

from moviepy.editor import VideoFileClip, concatenate_videoclips

def stitch_clips(clip_paths, output_path="highlight_reel.mp4"):
    clips = []
    for path in clip_paths:
        clip = VideoFileClip(path)
        # Apply fade in/out
        faded = clip.fadein(0.5).fadeout(0.5)
        clips.append(faded)

    if not clips:
        raise ValueError("No clips to stitch")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=30)

    return output_path

