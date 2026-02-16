


import asyncio, os
from datetime import datetime

from .....systems.translations import UTILS_ISO_TO_DAYSMONTHSYEAR as T



def format_length(seconds: int) -> str:
                h, m = divmod(seconds, 3600)
                m, s = divmod(m, 60)
                if h > 0:
                    return f"{h}:{m:02}:{s:02}"
                return f"{m}:{s:02}"

def iso_to_DaysMonthYear(iso_str: str, lang: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

        d, m, y = dt.strftime("%d"), dt.strftime("%b"), dt.strftime("%Y")

        m = T.get(str(m), m)[lang]
        
        return f"{d} {m} {y}"
    
    except:
        return '???'

def stars_to_prop(stars, max_stars=10):
    stars = int(max(0, min(stars, max_stars)))
    xs = ["x"] * stars
    dashes = ["-"] * (max_stars - stars)
    return " ".join(xs + dashes)

def trim_text(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text

    words = text.split()
    trimmed = ""
    for word in words:
        if len(trimmed + word) + (1 if trimmed else 0) <= max_len - 3:
            trimmed += (" " if trimmed else "") + word
        else:
            break

    if len(trimmed) < max_len // 2:
        trimmed = text[:max_len - 3]

    return trimmed + "...."

async def delayed_remove(path, delay=5):
    await asyncio.sleep(delay)
    os.remove(path)