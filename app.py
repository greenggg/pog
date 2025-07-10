
import streamlit as st
import imageio



password = st.text_input("Enter password to continue", type="password")
if password != st.secrets["access_password"]:
    st.stop()

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.highlight_detector import transcribe, detect_highlights
from backend.clipper import cut_clip, stitch_clips
from backend.vod_downloader import download_vod
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="PogClips", layout="centered")
st.title("🎥 PogClips")

input_mode = st.radio("Select Input Method", ["Upload Clip", "Twitch VOD Link"])
temp_path = None

if input_mode == "Upload Clip":
    uploaded = st.file_uploader("Upload Stream Clip (.mp4)", type=["mp4"])
    if uploaded:
        temp_path = "temp.mp4"
        with open(temp_path, "wb") as f:
            f.write(uploaded.read())

elif input_mode == "Twitch VOD Link":
    vod_url = st.text_input("Paste Twitch VOD Link:")
    if vod_url:
        st.info("Downloading VOD from Twitch...")
        try:
            temp_path = download_vod(vod_url)
            st.success("Download complete.")
        except Exception as e:
            if "does not exist" in str(e).lower():
                st.error("❌ This Twitch VOD no longer exists or has expired.")
            else:
                st.error(f"Download failed: {e}")

if temp_path:
    st.info("Transcribing and detecting highlights...")

    progress_bar = st.progress(0.0)
    segments = transcribe(temp_path, update_callback=lambda pct: progress_bar.progress(pct * 0.5))
    highlights = detect_highlights(segments, update_callback=lambda pct: progress_bar.progress(0.5 + pct * 0.5))
    progress_bar.progress(1.0)

    if not highlights:
        st.warning("No hype moments detected 😢")
    else:
        st.success(f"{len(highlights)} highlight(s) found!")

        import moviepy.editor as mp

        video = mp.VideoFileClip(temp_path)
        video_duration = video.duration
        video.close()

        clips = []
        PADDING_BEFORE = 1.5
        PADDING_AFTER = 1.5

        for i, h in enumerate(highlights):
            start = max(h["start"] - PADDING_BEFORE, 0)
            end = min(h["end"] + PADDING_AFTER, video_duration)

            st.markdown(f"**Clip {i + 1}**: `{start:.2f}s → {end:.2f}s` – *{h['text']}*")
            out_path = f"clip_{i + 1}.mp4"
            cut_clip(temp_path, start, end, out_path)
            clips.append(out_path)

        st.info("Stitching top highlights into a reel...")
        try:
            final_reel = stitch_clips(clips)
            st.success("Highlight reel ready!")

            def load_video_base64(video_path):
                with open(video_path, "rb") as f:
                    data = f.read()
                    return base64.b64encode(data).decode()

            if os.path.exists("highlight_reel.mp4"):
                video_base64 = load_video_base64("highlight_reel.mp4")
                highlight_starts = [h["start"] for h in highlights]

                components.html(f"""
                <!DOCTYPE html>
                <html>
                  <body style="text-align:center; background-color: #0e1117;">
                    <video id="highlightVideo" width="720" controls style="border-radius: 12px;">
                      <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                      Your browser does not support the video tag.
                    </video>
                    <br/>
                    <button onclick="prevHighlight()" style="margin: 10px;">⬅️ Previous Highlight</button>
                    <button onclick="nextHighlight()" style="margin: 10px;">➡️ Next Highlight</button>

                    <script>
                      const video = document.getElementById("highlightVideo");
                      const highlights = {highlight_starts};
                      let current = 0;

                      function goTo(index) {{
                        if (index >= 0 && index < highlights.length) {{
                          video.currentTime = highlights[index];
                          current = index;
                        }}
                      }}

                      function nextHighlight() {{
                        if (current < highlights.length - 1) {{
                          goTo(current + 1);
                        }}
                      }}

                      function prevHighlight() {{
                        if (current > 0) {{
                          goTo(current - 1);
                        }}
                      }}
                    </script>
                  </body>
                </html>
                """, height=460)

        except Exception as e:
            st.error(f"Reel stitching failed: {e}")
