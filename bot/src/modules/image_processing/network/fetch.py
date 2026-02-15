


import io
import os
import aiohttp
from datetime import datetime, timedelta
from PIL import Image, ImageOps

from ..elements.image_utils import add_rounded_corners



async def fetch_image(
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

    timeout = aiohttp.ClientTimeout(total=30)
    img = None
    for attempt in range(max_attempts):
        try:
            print("🔻 HTTP request (card_score_compare fetch)")
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        img = Image.open(io.BytesIO(data)).convert("RGBA")

                        if thumb_size:
                            img = ImageOps.fit(img, thumb_size, Image.LANCZOS)

                        if radius:
                            img = add_rounded_corners(img, radius=radius)

                        fname = f"{beatmap_id}_{now.hour}{now.minute}.png"
                        save_path = os.path.join(cache_dir, fname)
                        img.save(save_path, format="PNG")
                        img.close()

                        return save_path

                    else:
                        print("fetch_cover in card_beatmap error, status: ",resp.status)
                    
        except Exception as e:
            print("fetch_cover in card_beatmap error: ", e)

    return None
