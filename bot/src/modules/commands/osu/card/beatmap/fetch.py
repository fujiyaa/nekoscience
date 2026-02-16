


import io
import os
import aiohttp
from datetime import datetime, timedelta
from PIL import Image

from .image_utils import add_rounded_corners



async def fetch_cover(
    url,
    beatmap_id,
    cache_dir,
    max_age_hours=12,
    max_attempts=3,
    thumb_size=(300, 300),
    radius=12,
):
    now = datetime.now()
    cached_path = None

    # beatmap_id_*.png
    for f in os.listdir(cache_dir):
        if f.startswith(f"{beatmap_id}_") and f.endswith(".png"):
            path = os.path.join(cache_dir, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if now - mtime < timedelta(hours=max_age_hours):
                cached_path = path
                break

    if cached_path:
        try:
            img = Image.open(cached_path).convert("RGBA")
            img.close()
            print("🍡 using cache (card_beatmap fetch)")
            return cached_path
        except Exception:
            cached_path = None

    timeout = aiohttp.ClientTimeout(total=10)
    img = None
    for attempt in range(max_attempts):
        try:
            print("🔻 HTTP request (card_beatmap fetch)")
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        img = Image.open(io.BytesIO(data)).convert("RGBA")

                        if thumb_size:
                            w, h = img.size
                            target_w, target_h = thumb_size

                            left = (w - target_w) // 2
                            top = (h - target_h) // 2
                            right = left + target_w
                            bottom = top + target_h

                            img = img.crop((left, top, right, bottom))

                        if radius:
                            img = add_rounded_corners(img, radius=radius)

                        fname = f"{beatmap_id}_{now.hour}{now.minute}.png"
                        save_path = os.path.join(cache_dir, fname)
                        img.save(save_path, format="PNG")
                        img.close()

                        return save_path
                    
        except Exception as e:
            print("fetch_cover in card_beatmap error: ", e)

    return None
