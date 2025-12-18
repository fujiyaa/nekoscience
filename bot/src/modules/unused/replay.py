


import os, subprocess
from osrparse import Replay
from bot.src.modules.external.osu_api import get_beatmapset_id_from_md5

async def get_beatmapset_md5(replay_path: str) -> str:
    replay = Replay.from_path(replay_path)
    return replay.beatmap_hash

async def get_beatmapset_id(replay_path: str, token: str) -> int:
    md5_hash = await get_beatmapset_md5(replay_path)
    return await get_beatmapset_id_from_md5(md5_hash, token)



# эту хрень не использовать лучше и вообще ничего подобного не использовать

def compress_video_if_needed(input_path: str, max_size_mb: int = 45) -> str:   
    file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    if file_size_mb <= max_size_mb:        
        return input_path

    base, ext = os.path.splitext(input_path)
    compressed_path = f"{base}_compressed{ext}"

    ffmpeg_command = [
        "ffmpeg",
        "-y",  
        "-i", input_path,
        "-vcodec", "libx264",
        "-crf", "28",      
        "-preset", "fast",  
        "-acodec", "aac",
        compressed_path
    ]

    subprocess.run(ffmpeg_command, check=True)

    return compressed_path