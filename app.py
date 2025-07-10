import streamlit as st
import imageio
import os
import sys
import base64
import streamlit.components.v1 as components
from moviepy.editor import VideoFileClip

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("clips", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Password gate
password = st.text_input("Enter password to continue", type="password")
if password != st.secrets["access_password"]:
    st.stop()

# Add backend folder to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Imports
from backend.highlight_detector import detect_highlights
from backend.clipper import cut_clip, stitch_clips
from backend.vod_downloader import download_vod

# App setup
st.set_page_config(page_title="PogClips", layout="centered")
st.title("🎥 PogClips")

input_mode = st.radio("Select Input Method", ["Upload Clip", "Twitch VOD Link"])
temp_path = None

# Input handling
if input_mode == "Upload Clip":
    uploaded = st.file_uploader("Upload Stream Clip (.mp4)", type=["mp4"])
    if uploaded:
        temp_path = os.path.join("uploads", uploaded.name)
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

# Main logic
if temp_path:
    st.info("Transcribing and detecting highlights...")
    progress_bar = st.progress(0.0)

    segments = detect_highlights(temp_path, update_callback=lambda pct: progress_bar.progress(pct * 0.5))
    highlights = detect_highlights(temp_path, update_callback=lambda pct: progress_bar.progress(pct))
    progress_bar.progress(1.0)

    if not highlights:
        st.warning("No hype moments detected 😢")
    else:
        st.success(f"{len(highlights)} highlight(s) found!")

        video = VideoFileClip(temp_path)
        video_duration = video.duration
        video.close()

        clips = []
        PADDING_BEFORE = 1.5
        PADDING_AFTER = 1.5

        for i, h in enumerate(highlights):
            start = max(h["start"] - PADDING_BEFORE, 0)
            end = min(h["end"] + PADDING_AFTER, video_duration)
            st.markdown(f"**Clip {i + 1}**: `{start:.2f}s → {end:.2f}s` – *{h['text']}*")
            out_path = os.path.join("clips", f"clip_{i + 1}.mp4")
            cut_clip(temp_path, start, end, out_path)
            clips.append(out_path)

        st.info("Stitching top highlights into a reel...")
        try:
            final_reel_path = os.path.join("output", "highlight_reel.mp4")
            stitch_clips(clips, output_path=final_reel_path)

            if os.path.exists(final_reel_path):
                def load_video_base64(video_path):
                    with open(video_path, "rb") as f:
                        return base64.b64encode(f.read()).decode()

                video_base64 = load_video_base64(final_reel_path)
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
                        if (current < highlights.length - 1) goTo(current + 1);
                      }}
                      function prevHighlight() {{
                        if (current > 0) goTo(current - 1);
                      }}
                    </script>
                  </body>
                </html>
                """, height=460)
        except Exception as e:
            st.error(f"Reel stitching failed: {e}")
