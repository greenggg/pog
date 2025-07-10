import whisper
import numpy as np
import torch
import os

model = whisper.load_model("base")

def detect_highlights(file_path, update_callback=None):
    if update_callback:
        update_callback(0.1)

    # Defensive fallback: convert audio if needed
    try:
        result = model.transcribe(file_path)
    except TypeError as e:
        # Manually process audio if transcribe fails due to type issues
        audio = whisper.load_audio(file_path)
        if isinstance(audio, list):
            audio = np.array(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        options = whisper.DecodingOptions()
        result = whisper.decode(model, mel, options)

        # Fake segment for compatibility if needed
        result = {"segments": [{
            "start": 0,
            "end": len(audio) / whisper.audio.SAMPLE_RATE,
            "text": result.text,
            "avg_logprob": -1.0
        }]}

    segments = result.get('segments', [])
    highlights = []

    seen_texts = set()
    last_end = 0

    min_spacing = 30     # Seconds between highlights
    skip_initial = 60    # Skip first 60 seconds
    min_length = 3       # Min length of a segment
    banned_phrases = ["starting soon", "welcome", "music", "waiting", "subscribe"]

    for seg in segments:
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip().lower()

        if start < skip_initial:
            continue
        if (end - start) < min_length:
            continue
        if any(phrase in text for phrase in banned_phrases):
            continue
        if text in seen_texts:
            continue
        if start - last_end < min_spacing:
            continue

        loudness = seg.get('avg_logprob', -10)
        keywords = ["no way", "omg", "wtf", "insane", "let's go", "crazy", "bro", "dude"]
        keyword_score = sum(k in text for k in keywords)
        score = keyword_score + max(0, loudness + 5)

        highlights.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "text": text,
            "score": round(score, 2)
        })

        seen_texts.add(text)
        last_end = end

    highlights = sorted(highlights, key=lambda x: x['score'], reverse=True)

    # Always return top 5, even if they’re weak
    return highlights[:5]
