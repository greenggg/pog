import ffmpeg
import subprocess
import os

def cut_clip(input_file, start, end, output_file):
    (
        ffmpeg
        .input(input_file, ss=start, to=end)
        .output(output_file)
        .run(overwrite_output=True)
    )

def stitch_clips(clips, output_file="highlight_reel.mp4"):
    list_file = "clip_list.txt"

    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_file
    ], check=True)

    os.remove(list_file)
    return output_file
