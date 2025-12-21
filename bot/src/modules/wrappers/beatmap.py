


import os
import io
import asyncio
from datetime import datetime, timedelta
import aiohttp 
from PIL import Image, ImageDraw, ImageFont

from ...config import BOT_DIR, TEMP_DIR, AVATARS_DIR, COVERS_DIR



async def create_beatmap_image(score: dict) -> str | None:
    timeout = aiohttp.ClientTimeout(total=10)
    
    def wrap_text(text, font, max_w):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if draw.textlength(test_line, font=font) <= max_w:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines
    
    def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
        mask = Image.new("L", img.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
        img.putalpha(mask)
        return img

    def draw_text_with_shadow(draw_obj, position, text, font, fill=(255, 255, 255, 255), shadowcolor=(0, 0, 0, 255), shadow_offset=4):
        x, y = position
        for dx in range(-shadow_offset, shadow_offset + 1):
            for dy in range(-shadow_offset, shadow_offset + 1):
                if dx == 0 and dy == 0:
                    continue
                draw_obj.text((x + dx, y + dy), text, font=font, fill=shadowcolor)
        draw_obj.text((x, y), text, font=font, fill=fill)

    def paste_with_shadow(base_img: Image.Image, overlay_img: Image.Image, position: tuple[int, int],
                          shadow_offset: int = 5, shadow_color=(0, 0, 0, 180)):
        x, y = position
        shadow = Image.new("RGBA", overlay_img.size, shadow_color)
        shadow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        shadow_layer.paste(shadow, (x + shadow_offset, y + shadow_offset), overlay_img)
        base_img.alpha_composite(shadow_layer)
        base_img.paste(overlay_img, (x, y), overlay_img)

    cover_id = score.get("beatmapset", {}).get("id")
    if not cover_id:
        return None

    cover_path = os.path.join(COVERS_DIR, f"{cover_id}.png")

    if os.path.exists(cover_path) and os.path.getsize(cover_path) > 0:
        try:
            image = Image.open(cover_path).convert("RGBA")
            print("using cached cover")
        except Exception as e:
            print(f"⚠ Ошибка открытия кэшированной обложки: {e}")
            image = Image.open(f"{BOT_DIR}/cards/assets/rs/default_cover.png").convert("RGBA")

    else:
        cover_url = (
            score["beatmapset"].get("covers", {}).get("cover@2x")
            or score["beatmapset"].get("covers", {}).get("cover")
        )
        if not cover_url:
            print("⚠ Нет ссылки на обложку, используем fallback")
            image = Image.open(f"{BOT_DIR}/cards/assets/rs/default_cover.png").convert("RGBA")

        else:
            for attempt in range(3):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(cover_url) as resp:
                            if resp.status != 200:
                                raise Exception(f"HTTP {resp.status}")
                            img_data = await resp.read()
                            image = Image.open(io.BytesIO(img_data)).convert("RGBA")
                            image.save(cover_path, format="PNG")
                            break
                except Exception as e:
                    print(f"⚠ Ошибка загрузки обложки (попытка {attempt+1}/2): {e}")
                    if attempt < 1:
                        await asyncio.sleep(1)
                    else:
                        image = Image.open("assets/default_cover.png").convert("RGBA")

    avatar_url = score["user"]["avatar_url"]
    user_id = score["user"]["id"]
    
    now = datetime.now()
    avatar_file = None
    for f in os.listdir(AVATARS_DIR):
        if f.startswith(f"{user_id}_") and f.endswith(".png"):
            path = os.path.join(AVATARS_DIR, f)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if now - mtime < timedelta(hours=1):
                avatar_file = path
                break
            
    MAX_ATTEMPTS = 3

    if avatar_file:
        extra_img = Image.open(avatar_file).convert("RGBA")
        avatar_path = avatar_file
        print("using cached avatar")
    else:
        avatar_path = os.path.join(AVATARS_DIR, "default.png")
        extra_img = None
        for attempt_avatar in range(1, MAX_ATTEMPTS + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=3)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(avatar_url) as resp:
                        if resp.status == 200:
                            def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
                               
                                big_size = (img.size[0]*2, img.size[1]*2)
                                mask = Image.new("L", big_size, 0)
                                draw_mask = ImageDraw.Draw(mask)
                                draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)
                                
                                mask = mask.resize(img.size, Image.LANCZOS)
                                
                                img.putalpha(mask)
                                return img
                            extra_img_data = await resp.read()
                            extra_img = Image.open(io.BytesIO(extra_img_data)).convert("RGBA")
                            extra_img.thumbnail((512, 512))
                            extra_img = add_rounded_corners(extra_img, radius=12)
                            avatar_filename = f"{user_id}_{now.hour}{now.minute}.png"
                            avatar_path = os.path.join(AVATARS_DIR, avatar_filename)
                            extra_img.save(avatar_path, format="PNG")
                            break
            except Exception as e:
                print(f"Ошибка при скачивании аватарки: {e}")

    width, height = image.size

    if width > 350:
        image = image.crop((350, 0, width - 350, height))
    else:
        pass

    draw = ImageDraw.Draw(image)

    try:
        font_title = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 50)
        font_info = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 40)
        font_star = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 80)
        font_username = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 60)
        font_total_pp = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 40)
    except IOError:
        font_title = ImageFont.load_default()
        font_info = ImageFont.load_default()
        font_star = ImageFont.load_default()
        font_username = ImageFont.load_default()
        font_total_pp = ImageFont.load_default()

    title = score["beatmapset"].get("title") or score["beatmapset"].get("title", "")
    artist = score["beatmapset"].get("artist", "")
    mapper = score["beatmapset"].get("creator", "unknown")
    version = score["beatmap"].get("version", "")
    sr = score["sr"]

    left_margin = 10
    right_margin = 10

    max_width = image.width - left_margin - right_margin

    title_text = f"{title} by {artist}"

    

    title_lines = wrap_text(title_text, font_title, max_width)

    y_offset = 20
    for line in title_lines:
        draw_text_with_shadow(draw, (left_margin, y_offset), line, font_title, fill=(255, 255, 255, 220), shadowcolor=(0, 0, 0, 200))
        bbox = draw.textbbox((0, 0), line, font=font_title)
        line_height = bbox[3] - bbox[1]
        y_offset += line_height + 5

    mapper_line = f"{mapper} [{version}]"
    draw_text_with_shadow(draw, (left_margin, y_offset), mapper_line, font_info, fill=(255, 255, 255, 200), shadowcolor=(0, 0, 0, 180))

    star_text = f"★ {sr:.2f}"
    bbox = draw.textbbox((0, 0), star_text, font=font_star)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw_text_with_shadow(draw, (image.width - text_w - right_margin, image.height - text_h - 20), star_text, font_star, fill=(255, 255, 255, 200), shadowcolor=(0, 0, 0, 180))

    
    
    extra_img = extra_img.resize((120, 120))

    if extra_img:
        extra_x = 10
        extra_y = image.height - extra_img.height - 10
        paste_with_shadow(image, extra_img, (extra_x, extra_y), shadow_offset=6, shadow_color=(0, 0, 0, 180))

        text_offset_x = extra_x + extra_img.width + 20
        text_offset_y = extra_y + 10

        text1 = score["user"]["username"]
        draw_text_with_shadow(draw, (text_offset_x, text_offset_y), text1, font_username,
                              fill=(255, 255, 255, 220), shadowcolor=(0, 0, 0, 200))

        bbox1 = draw.textbbox((0, 0), text1, font=font_username)
        line_height1 = bbox1[3] - bbox1[1]
        text2 = str(score["total_pp"]) + 'pp'
        draw_text_with_shadow(draw, (text_offset_x, text_offset_y + line_height1 + 10), text2, font_total_pp,
                              fill=(255, 255, 255, 200), shadowcolor=(0, 0, 0, 180))

    score_id = f'{score["user"]["username"]}{score.get("id", "unknown")}'
    file_path = os.path.join(TEMP_DIR, f"{score_id}.png")
    image.save(file_path, format="PNG")
    print("Image saved to", file_path)
    return file_path