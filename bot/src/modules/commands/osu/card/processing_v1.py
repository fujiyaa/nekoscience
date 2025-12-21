


import io
import aiohttp
import asyncio
import colorsys
import tempfile
from datetime import date
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .....config import BOT_DIR, GRAPH_PNG



async def create_profile_image(user_data: dict, best_pp: str) -> str | None:
    final_w, final_h = 1000, 400

    cover_url = user_data.get("cover_url")
    if cover_url:
        async with aiohttp.ClientSession() as session:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(cover_url, timeout=timeout) as resp:
                    if resp.status == 200:
                        bg_bytes = await resp.read()
                        banner = Image.open(io.BytesIO(bg_bytes)).convert("RGBA")
                        bw, bh = banner.size
                        target_ratio = final_w / final_h
                        banner_ratio = bw / bh
                        if banner_ratio > target_ratio:
                            new_w = int(bh * target_ratio)
                            left = (bw - new_w) // 2
                            banner = banner.crop((left, 0, left + new_w, bh))
                        else:
                            new_h = int(bw / target_ratio)
                            top = (bh - new_h) // 2
                            banner = banner.crop((0, top, bw, top + new_h))
                        banner = banner.resize((final_w, final_h), Image.LANCZOS)
                    else:
                        banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                print(f"Failed to load cover_url: {e}")
                banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))
    else:
        banner = Image.new("RGBA", (final_w, final_h), (40, 40, 40, 255))

    draw = ImageDraw.Draw(banner)

    try:
        font_name = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 60)
        font_stats = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 28)
        font_small = ImageFont.truetype(f"{BOT_DIR}/cards/Jua.ttf", 24)
    except IOError:
        font_name = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_small = ImageFont.load_default()

    def draw_text_with_shadow_3(draw, pos, text, font, fill, shadowcolor):
        x, y = pos

        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)

        draw.text((x, y), text, font=font, fill=fill)

    def draw_text_with_shadow(draw_obj, position, text, font, fill=(255, 255, 255, 255),
                              shadowcolor=(0, 0, 0, 255), shadow_offset=3):
        x, y = position
        for dx in range(-shadow_offset, shadow_offset + 1):
            for dy in range(-shadow_offset, shadow_offset + 1):
                if dx == 0 and dy == 0:
                    continue
                draw_obj.text((x + dx, y + dy), text, font=font, fill=shadowcolor)
        draw_obj.text((x, y), text, font=font, fill=fill)

    avatar_top = 35
    async with aiohttp.ClientSession() as session:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(user_data["avatar_url"], timeout=timeout) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                    avatar_img = avatar_img.resize((200, 200))
                    mask = Image.new("L", avatar_img.size, 0)
                    mask_draw = ImageDraw.Draw(mask)
                    corner_radius = 20 
                    mask_draw.rounded_rectangle((0, 0, 200, 200), radius=corner_radius, fill=255)
                    avatar_img.putalpha(mask)
                    shadow = Image.new("RGBA", avatar_img.size, (0, 0, 0, 180))
                    banner.paste(shadow, (50 + 5, avatar_top + 5), mask)
                    banner.paste(avatar_img, (50, avatar_top), avatar_img)
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"Failed to load avatar_url: {e}")

    try:
        short_name = ""
        team_flag_url = user_data.get("team", {}).get("flag_url")
        if team_flag_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(team_flag_url) as resp:
                    if resp.status == 200:
                        flag_bytes = await resp.read()
                        flag_img = Image.open(io.BytesIO(flag_bytes)).convert("RGBA")
                        fw, fh = flag_img.size
                        scale_factor = 200 / fw  
                        new_w = int(fw * scale_factor)
                        new_h = int(fh * scale_factor)
                        flag_img = flag_img.resize((new_w, new_h), Image.LANCZOS)
                        
                        shadow = Image.new("RGBA", flag_img.size, (0, 0, 0, 180))
                        
                        flag_alpha = flag_img.split()[3]

                        flag_y = avatar_top + 200 + 10
                        shadow_offset = (5, 5) 

                        
                        banner.paste(shadow, (50 + shadow_offset[0], flag_y + shadow_offset[1]), flag_alpha)
                        
                        banner.paste(flag_img, (50, flag_y), flag_img)

        short_name = "team tag:  " + user_data.get("team", {}).get("short_name", "")
        if short_name:
            flag_y_bottom = avatar_top + 200 + 15 + (new_h if team_flag_url else 0)
            draw_text_with_shadow_3(draw, (50, flag_y_bottom + 5), short_name, font_stats, fill=(255, 255, 255, 230), shadowcolor=(0,0,0,150))
    except Exception as e: 
        print(e)
        
    username = user_data["username"]
    draw_text_with_shadow(draw, (280, 40), username, font_name)

    stats = user_data["statistics"]
    country_rank = stats.get("rank", {}).get("country", None)

    def hue_to_rgba(hue, saturation=1.0, lightness=0.5, alpha=255):
        if hue is None:
            hue = 349
        h = (hue % 360) / 360.0
        r, g, b = colorsys.hls_to_rgb(h, lightness, saturation)
        return (int(r * 255), int(g * 255), int(b * 255), alpha)

    def draw_text_with_shadow_2(draw, pos, text, font, fill, shadowcolor):
        x, y = pos

        for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)

        draw.text((x, y), text, font=font, fill=fill)

    def draw_text_with_shadow(draw, pos, text, font, fill, shadowcolor):
        x, y = pos

        draw.text((x + 1, y + 1), text, font=font, fill=shadowcolor)
        draw.text((x, y), text, font=font, fill=fill)

    def draw_stat_line(draw, pos, key_text, value_text, font_key, font_value,
                    key_fill, key_shadow, value_fill, value_shadow, gap=8):
        x, y = pos

        draw_text_with_shadow(draw, (x, y), key_text, font_key, fill=key_fill, shadowcolor=key_shadow)

        bbox = draw.textbbox((x, y), key_text, font=font_key)
        key_w = bbox[2] - bbox[0]

        draw_text_with_shadow(draw, (x + key_w + gap, y), value_text, font_value, fill=value_fill, shadowcolor=value_shadow)

    stat_lines = [
        f"PP: {round(stats.get('pp', 0), 2)}",
        f"Country Rank: #{country_rank}" if country_rank else "Country Rank: N/A",
        f"Accuracy: {round(stats.get('hit_accuracy', 0), 2)}%",
        f"Playcount: {stats.get('play_count', 0):,}",
        f"Max Combo: {stats.get('maximum_combo', 0):,}",
        f"Playtime: {stats.get('play_time', 0) // 3600}h",
        f"Hits/Play: {round(stats.get('total_hits', 0) / max(stats.get('play_count', 1), 1), 2)}",
        f" ",
        f" ",
        f"Max PP: {best_pp}",       
        f"Replays Watched: {stats.get('replays_watched_by_others', 0):,}", 
        
    ]

    profile_hue = user_data.get("profile_hue", 211)
    glow_color = hue_to_rgba(profile_hue, saturation=1, lightness=0.5, alpha=180)

    overlay_x, overlay_y = 270, 106
    overlay_w, overlay_h = 680, 240
    overlay = Image.new("RGBA", (overlay_w, overlay_h), (0, 0, 0, 190))
    banner.paste(overlay, (overlay_x, overlay_y), overlay)

    col_gap = 340
    left_x, right_x = 280, 280 + col_gap
    y_start = 120

    for i, line in enumerate(stat_lines):
        col = i % 2
        row = i // 2
        x_pos = left_x if col == 0 else right_x
        y_pos = y_start + row * 32

        if ": " in line:
            key_text, value_text = line.split(": ", 1)
            key_text += ":"
        else:
            key_text, value_text = line, ""

        draw_stat_line(
            draw, (x_pos, y_pos),
            key_text, value_text,
            font_stats, font_stats,
            key_fill=(255, 255, 255, 220), key_shadow=(0, 0, 0, 180),
            value_fill=glow_color, value_shadow=(0, 255, 255, 180),
            gap=8
        )

    lvl_current = stats.get("level", {}).get("current", 0)
    lvl_progress = stats.get("level", {}).get("progress", 0)
    bar_x, bar_y = 280, final_h - 35
    bar_width, bar_height = 480, 15
    
    shadow_offset = (10, 10)
    shadow_color = (0, 0, 0, 200)
    shadow_radius = 35  

    shadow_layer = Image.new("RGBA", banner.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_draw.rounded_rectangle(
        [bar_x + shadow_offset[0], bar_y + shadow_offset[1], bar_x + bar_width + shadow_offset[0], bar_y + bar_height + shadow_offset[1]],
        radius=12,
        fill=shadow_color
    )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_radius))

    banner = Image.alpha_composite(banner, shadow_layer)

    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                        radius=12, fill=(60, 60, 60, 200))
    fill_width = int(bar_width * (lvl_progress / 100))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height],
                        radius=12, fill=(glow_color))
    
    text = f"Level {lvl_current} ({lvl_progress}%)"
    bbox = draw.textbbox((0, 0), text, font=font_small)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    text_x = bar_x + bar_width + 10 
    text_y = bar_y + (bar_height - text_h) // 2

    draw_text_with_shadow_2(draw, (text_x, text_y), text, font_small, fill=(255, 255, 255, 230), shadowcolor=(0,0,0,150))

    def draw_neon_glow(base_img, points, glow_color, glow_width=15, blur_radius=10):
        glow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)

        glow_draw.line(points, fill=glow_color, width=glow_width, joint="curve")

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur_radius))

        base_img.alpha_composite(glow_layer)

    def draw_gradient_line(draw, points, start_color, end_color, width=3):
        n = len(points)
        for i in range(n - 1):
            t = i / (n - 2) if n > 2 else 0
            r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
            a = int(start_color[3] + (end_color[3] - start_color[3]) * t)

            color = (r, g, b, a)
            draw.line([points[i], points[i+1]], fill=color, width=width, joint="curve")

    extra_height = 200
    new_banner = Image.new("RGBA", (banner.width, banner.height + extra_height), (30, 30, 30, 255))
    new_banner.paste(banner, (0, 0))
    banner = new_banner
    draw = ImageDraw.Draw(banner)

    background_img = Image.open(GRAPH_PNG).convert("RGBA")

    banner.paste(background_img, (0, 400), background_img) 


    rank_history = user_data.get("rank_history", {}).get("data")
    if rank_history:
        graph_x = 50
        graph_y = banner.height - extra_height + 20
        graph_width = banner.width - 100
        graph_height = extra_height - 40

        min_rank = min(rank_history)
        max_rank = max(rank_history)
        rank_range = max_rank - min_rank if max_rank != min_rank else 1

        points = []
        for i, rank in enumerate(rank_history):
            x = graph_x + (i / (len(rank_history) - 1)) * graph_width
            y = graph_y + ((rank - min_rank) / rank_range) * graph_height

            points.append((x, y))
        draw_neon_glow(banner, points, glow_color, glow_width=15, blur_radius=15)

        start_color = (255, 255, 255, 255)
        end_color = glow_color
        draw_gradient_line(draw, points, start_color, end_color, width=3)

        draw.rectangle([graph_x, graph_y, graph_x + graph_width, graph_y + graph_height], outline=(150, 150, 150, 255), width=1)

    points = []
    for i, rank in enumerate(rank_history):
        x = graph_x + (i / (len(rank_history) - 1)) * graph_width
        y = graph_y + graph_height - ((rank - min_rank) / rank_range) * graph_height
        points.append((x, y))

    # ...

    rank_text = f"#{stats.get('global_rank'):,}" if stats.get("global_rank") else "Global Rank: N/A"
    bbox = draw.textbbox((0, 0), rank_text, font=font_name)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    last_point_x, last_point_y = points[-1]
    mid_y = graph_y + graph_height / 2
    padding = 5

    text_x = graph_x + graph_width - text_w 

    if last_point_y > mid_y:
        text_y = max(last_point_y - text_h - padding, graph_y)
    else:
        text_y = min(last_point_y + padding, graph_y + graph_height - text_h)

    draw_text_with_shadow(
        draw,
        (text_x, text_y),
        rank_text,
        font=font_name,
        fill=(255, 255, 255, 200),
        shadowcolor=(0, 0, 0, 180)
    )

    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    banner.save(tmp_file.name, "PNG")
    tmp_file.close()
    return tmp_file.name
