import whisper

model = whisper.load_model("base")

def transcribe(file_path, update_callback=None):
    result = model.transcribe(file_path)
    segments = result['segments']
    highlights = []

    seen_texts = set()
    last_end = 0

    min_spacing = 30     # Seconds between highlights
    skip_initial = 60    # Skip first 60 seconds (usually "starting soon")
    min_length = 3       # Min length of a segment
    banned_phrases = ["starting soon", "welcome", "music", "waiting", "subscribe"]

    total = len(segments)
    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        text = seg['text'].strip().lower()

        # Basic filters
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

        # Scoring
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

        # Report progress
        if update_callback:
            update_callback(int((i + 1) / total * 100))

    highlights = sorted(highlights, key=lambda x: x['score'], reverse=True)
    return highlights[:5]
