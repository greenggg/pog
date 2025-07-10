import whisper

model = whisper.load_model("base")

def transcribe(file_path, update_callback=None):
    result = model.transcribe(file_path)
    if update_callback:
        update_callback(0.5)  # Rough midpoint, adjust as needed
    return result['segments']

def detect_highlights(segments, update_callback=None):
    highlights = []
    seen_texts = set()
    last_end = 0

    min_spacing = 30
    skip_initial = 60
    min_length = 3
    banned_phrases = ["starting soon", "welcome", "music", "waiting", "subscribe"]

    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip().lower()

        if start < skip_initial or (end - start) < min_length:
            continue
        if any(phrase in text for phrase in banned_phrases):
            continue
        if text in seen_texts or (start - last_end) < min_spacing:
            continue

        loudness = seg.get('avg_logprob', -10)
        keywords = ["no way", "omg", "wtf", "insane", "let's go", "crazy", "bro", "dude"]
        keyword_score = sum(k in text for k in keywords)
        score = keyword_score + max(0, loudness + 5)

        if score > 2.0:
            highlights.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "text": text,
                "score": round(score, 2)
            })
            seen_texts.add(text)
            last_end = end

        if update_callback:
            update_callback((i + 1) / len(segments))  # Fractional progress

    highlights = sorted(highlights, key=lambda x: x['score'], reverse=True)
    return highlights[:5]
