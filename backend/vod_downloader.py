import yt_dlp

def download_vod(vod_url, output_path="temp_vod.mp4"):
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]',
        'noplaylist': True,
        'no_warnings': False,
        'progress_hooks': [lambda d: print(f"[yt-dlp] {d['status']}: {d.get('filename', '')}")],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([vod_url])

    return output_path
