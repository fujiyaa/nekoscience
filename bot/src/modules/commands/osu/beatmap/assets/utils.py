


import re
import os
from typing import Optional



async def beatmap_artists_and_audio_path(folder_path: str) -> tuple[Optional[str], Optional[str]]:
    osu_files = [f for f in os.listdir(folder_path) if f.endswith(".osu")]
    if not osu_files:
        print(f"beatmap_artists_and_audio_path {folder_path} нет .osu файлов")
        return None, None

    path_to_map = os.path.join(folder_path, osu_files[0])

    title = None
    artist = None
    title_unicode = None
    artist_unicode = None
    audio_filename = None
    bg_path = None

    try:
        with open(path_to_map, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TitleUnicode:"):
                    title_unicode = line.split(":", 1)[1].strip()
                elif line.startswith("ArtistUnicode:"):
                    artist_unicode = line.split(":", 1)[1].strip()
                elif line.startswith("Title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("Artist:"):
                    artist = line.split(":", 1)[1].strip()
                elif line.startswith("AudioFilename:"):
                    audio_filename = line.split(":", 1)[1].strip()
                elif '"' in line and any(ext in line.lower() for ext in [".jpg", ".jpeg", ".png"]):
                    m = re.search(r'"([^"]+\.(?:jpg|jpeg|png))"', line, re.IGNORECASE)
                    if m:
                        bg_path = m.group(1)
                if (title_unicode or title) and (artist_unicode or artist) and audio_filename and bg_path:
                    break
    except Exception as e:
        print(f"beatmap_artists_and_audio_path {path_to_map}: {e}")
        return None, None, None, None

    final_title = title_unicode if title_unicode else title
    final_artist = artist_unicode if artist_unicode else artist

    return final_title, final_artist, audio_filename, bg_path
