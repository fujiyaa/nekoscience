


import io
import aiohttp
import asyncio
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .....systems.translations import CARD_PROFILE as T
from .....utils.text_format import format_osu_date2
from .utils import hue_to_rgba

from config import BOT_DIR, GRAPH_PNG




async def create_profile_image(user_data: dict, best_pp: str) -> str | None: 
    username = user_data.get("username", "Name")
    country_code = user_data.get("country_code", "RU")
    l = user_data.get("lang", "ru")
    medals = len(user_data.get("user_achievements", {}))  
    profile_hue = user_data.get("profile_hue", 211)
    glow_color = hue_to_rgba(profile_hue, saturation=1, lightness=0.5, alpha=180)
    
    flag_path = f"{BOT_DIR}/cards/assets/flags/{country_code}.png"
    flag_ico_img = Image.open(flag_path).convert("RGBA")    
    
    final_w, final_h = 1500, 740  
    
    joined = format_osu_date2(user_data['join_date'], "%Y-%m-%d %H:%M:%S", True, l)  

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
        select = "ExtraBold"
        font_name = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/PlaypenSans-{select}.ttf", 72)
        font_stats = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/PlaypenSans-{select}.ttf", 36)
        font_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/PlaypenSans-{select}.ttf", 36)
    except IOError:
        font_name = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_small = ImageFont.load_default()
   

    def draw_text_with_shadow_3(draw, pos, text, font, fill, shadowcolor, shadow_offset = 2):
        x, y = pos

        for dx, dy in [(-shadow_offset,0), (shadow_offset,0), (0,-shadow_offset), (0,shadow_offset)]:
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


    avatar_top = 80    
    avatar_dims = 300
    corner_radius = 30 
    blocks_transparency = 190

    async with aiohttp.ClientSession() as session:
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(user_data["avatar_url"], timeout=timeout) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                    avatar_img = avatar_img.resize((avatar_dims, avatar_dims))
                    mask = Image.new("L", avatar_img.size, 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.rounded_rectangle((0, 0, avatar_dims, avatar_dims), radius=corner_radius, fill=255)
                    avatar_img.putalpha(mask)
                    shadow = Image.new("RGBA", avatar_img.size, (0, 0, 0, blocks_transparency))
                    banner.paste(shadow, (50 + 5, avatar_top + 5), mask)
                    banner.paste(avatar_img, (50, avatar_top), avatar_img)
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"Failed to load avatar_url: {e}")

    try:
        short_name = ""
        team_flag_url = user_data.get("team") and user_data.get("team").get("flag_url")

        if team_flag_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(team_flag_url) as resp:
                    if resp.status == 200:
                        flag_dims = 300
                        flag_bytes = await resp.read()
                        flag_img = Image.open(io.BytesIO(flag_bytes)).convert("RGBA")
                        fw, fh = flag_img.size
                        scale_factor = flag_dims / fw  
                        new_w = int(fw * scale_factor)
                        new_h = int(fh * scale_factor)
                        flag_img = flag_img.resize((new_w, new_h), Image.LANCZOS)
                        
                        shadow = Image.new("RGBA", flag_img.size, (0, 0, 0, blocks_transparency))
                        
                        flag_y = avatar_top + flag_dims + 30
                        shadow_offset = (5, 5)                         

                        mask = Image.new("L", flag_img.size, 0)
                        mask_draw = ImageDraw.Draw(mask)
                        mask_draw.rounded_rectangle(
                            (0, 0, flag_img.width, flag_img.height),
                            radius=corner_radius,
                            fill=255
                        )

                        flag_img.putalpha(mask)

                        
                        banner.paste(shadow, (50 + shadow_offset[0], flag_y + shadow_offset[1]), mask)
                        
                        banner.paste(flag_img, (50, flag_y), flag_img)

        team_data = user_data.get("team")
        short_name = team_data.get("short_name") if team_data and team_data.get("short_name") else None

        if short_name:
            short_name = f"{T.get('team tag')[l]}: {short_name}"
            team_text_shadow_offset = 3
            flag_y_bottom = avatar_top + flag_dims + 15 + (new_h if team_flag_url else 0)
            draw_text_with_shadow_3(draw, (50, flag_y_bottom + 25), short_name, font_small, fill=(255, 255, 255, 230), shadowcolor=(0,0,0,150), shadow_offset=team_text_shadow_offset)
    except Exception as e: 
        print(e)
        
    username_pos = (400, 30)

    username_shadow_offset = (6, 6)
    username_shadow_color = (255, 255, 255, 200)
    username_shadow_radius = 20
    username_padding = (20, 8)

    bbox = draw.textbbox(username_pos, username, font=font_name)
    x0, y0, x1, y1 = bbox

    pad_x, pad_y = username_padding

    shadow_layer = Image.new("RGBA", banner.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_draw.rounded_rectangle(
        (
            x0 - pad_x + username_shadow_offset[0],
            y0 - pad_y + username_shadow_offset[1],
            x1 + pad_x + username_shadow_offset[0],
            y1 + pad_y + username_shadow_offset[1],
        ),
        radius=100,
        fill=glow_color
    )

    shadow_layer = shadow_layer.filter(
        ImageFilter.GaussianBlur(radius=username_shadow_radius)
    )

    banner = Image.alpha_composite(banner, shadow_layer)
    draw = ImageDraw.Draw(banner)

    username_text_shadow_offset = 2
    draw_text_with_shadow_3(draw, username_pos, username, font_name, 
                            fill=(255,255,255,255), 
                            shadowcolor=glow_color, 
                            shadow_offset=username_text_shadow_offset)
    


    bbox = draw.textbbox(username_pos, username, font=font_name)
    text_width = bbox[2] - bbox[0]

    flag_ratio = flag_ico_img.width / flag_ico_img.height
    flag_height = 48
    flag_width = int(flag_height * flag_ratio)
    flag_ico_img = flag_ico_img.resize((flag_width, flag_height))

    mask = Image.new("L", (flag_width, flag_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (0, 0, flag_width, flag_height),
        radius=12,
        fill=255
    )

    flag_x = username_pos[0] + text_width + 15 + username_shadow_offset[0]
    flag_y = username_pos[1] + 40

    banner.paste(flag_ico_img, (flag_x, flag_y), mask)

    stats = user_data["statistics"]
    country_rank = stats.get("rank", {}).get("country", None)    

    def draw_text_with_shadow_2(draw, pos, text, font, fill, shadowcolor, shadow_offset = 2):
        x, y = pos

        for dx, dy in [(-shadow_offset,0), (shadow_offset,0), (0,-shadow_offset), (0,shadow_offset)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)

        draw.text((x, y), text, font=font, fill=fill)

    def draw_text_with_shadow(draw, pos, text, font, fill, shadowcolor, shadow_offset = 1):
        x, y = pos

        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadowcolor)
        draw.text((x, y), text, font=font, fill=fill)

    def draw_stat_line(draw, pos, key_text, value_text, font_key, font_value,
                    key_fill, key_shadow, value_fill, value_shadow, gap=8):
        x, y = pos

        offset = 2

        draw_text_with_shadow(draw, (x, y), key_text, font_key, fill=key_fill, shadowcolor=key_shadow, shadow_offset=offset)

        bbox = draw.textbbox((x, y), key_text, font=font_key)
        key_w = bbox[2] - bbox[0]

        if value_text.strip().replace('.', '').replace('%', '').replace('#', '').replace('h', '').replace(',', '').replace('x', '').isdigit():
            draw_text_with_bg(draw, (x + key_w + gap, y), 
                              value_text, font_value, 
                              fill=value_fill, 
                              shadowcolor=value_shadow, 
                              bg_fill=(255, 255, 255, 100), 
                              shadow_offset=offset)
        else:
            draw_text_with_shadow(draw, (x + key_w + gap, y), 
                                  value_text, font_value, 
                                  fill=value_fill, 
                                  shadowcolor=value_shadow, 
                                  shadow_offset=offset)



        
    def draw_text_with_bg(draw, pos, text, font, fill, shadowcolor,
                      bg_fill, bg_radius=corner_radius, padding=(8, 4), shadow_offset=2):
        x, y = pos
        pad_x, pad_y = padding

        bbox = draw.textbbox((x, y), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        br_rect_extra_x, br_rect_extra_y = 8, 14
        bg_rect = (
            x - pad_x + br_rect_extra_x,
            y - pad_y + br_rect_extra_y,
            x + w + pad_x + br_rect_extra_x - 2,
            y + h + pad_y + br_rect_extra_y
        )

        bg_w = bg_rect[2] - bg_rect[0]
        bg_h = bg_rect[3] - bg_rect[1]

        bg_layer = Image.new("RGBA", (bg_w, bg_h), (255, 255, 255, 255))

        mask = Image.new("L", (bg_w, bg_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            (0, 0, bg_w, bg_h),
            radius=bg_radius,
            fill=(255)
        )

        banner.paste(
            bg_layer,
            (bg_rect[0], bg_rect[1]),
            mask
        )

        # shadow_offset_override = 1
        # shadow_offset = shadow_offset_override

        # draw.text(
        #     (x + shadow_offset, y + shadow_offset),
        #     text,
        #     font=font,
        #     fill=shadowcolor
        # )

        draw.text((x, y), text, font=font, fill=fill)




    extra_gap = " "
    stat_lines = [
        f"PP: {extra_gap}{round(stats.get('pp', 0), 2)}",
        f"{T.get('Country Rank')[l]}: {extra_gap}#{country_rank}" if country_rank else f"{T.get('Country Rank')[l]}: {extra_gap}N/A",
        f"{T.get('Accuracy')[l]}: {extra_gap}{round(stats.get('hit_accuracy', 0), 2)}%",
        f"{T.get('Playcount')[l]}: {extra_gap}{stats.get('play_count', 0):,}",
        f"{T.get('Max Combo')[l]}: {extra_gap}{stats.get('maximum_combo', 0):,}x",
        f"{T.get('Playtime')[l]}: {extra_gap}{stats.get('play_time', 0) // 3600}h",
        f"{T.get('Hits/Play')[l]}: {extra_gap}{round(stats.get('total_hits', 0) / max(stats.get('play_count', 1), 1), 2)}",
        f" ",
        f" ",
        f"{T.get('Replays Watched')[l]}: {extra_gap}{stats.get('replays_watched_by_others', 0):,}", 
        f"{T.get('Max PP')[l]}: {extra_gap}{round(float(best_pp), 2)}",       
        f" ",
        f"{T.get('Medals')[l]}: {extra_gap}{medals}", 
        f" ",
        f"{T.get('Joined')[l]}: {extra_gap}{joined}", 
        
    ]

    overlay_x, overlay_y = 380, 150
    overlay_w, overlay_h = 1060, 440
    overlay = Image.new("RGBA", (overlay_w, overlay_h), (0, 0, 0, blocks_transparency))

    overlay_mask = Image.new("L", (overlay_w, overlay_h), 0)
    mask_draw = ImageDraw.Draw(overlay_mask)
    mask_draw.rounded_rectangle(
        (0, 0, overlay_w, overlay_h),
        radius=corner_radius,
        fill=blocks_transparency
    )

    banner.paste(overlay, (overlay_x, overlay_y), overlay_mask)


    col_gap = 460
    padding_x, padding_y = 30, 15
    left_x, right_x = overlay_x + padding_x, overlay_x + padding_x + col_gap
    y_start = overlay_y + padding_y

    for i, line in enumerate(stat_lines):
        col = i % 2
        row = i // 2
        x_pos = left_x if col == 0 else right_x
        y_pos = y_start + row * 50

        if ": " in line:
            key_text, value_text = line.split(": ", 1)
            key_text += ":"
        else:
            key_text, value_text = line, ""

        draw_stat_line(
            draw, (x_pos, y_pos),
            key_text, value_text,
            font_stats, font_stats,
            key_fill=(255, 255, 255, 240), key_shadow=(0, 0, 0, 200),
            value_fill=glow_color, value_shadow=(0, 0, 0, 200),
            gap=8
        )

    lvl_current = stats.get("level", {}).get("current", 0)
    lvl_progress = stats.get("level", {}).get("progress", 0)
    bar_x, bar_y = overlay_x, final_h - 110
    bar_width, bar_height = 640, 30

    lvl_text_extra_y = 8    
    lvl_text_shadow_offset = 3
    
    shadow_offset = (10, 10)
    shadow_color = (0, 0, 0, 200)
    shadow_radius = 35  

    shadow_layer = Image.new("RGBA", banner.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    shadow_draw.rounded_rectangle(
        [bar_x + shadow_offset[0], bar_y + shadow_offset[1], bar_x + bar_width + shadow_offset[0], bar_y + bar_height + shadow_offset[1]],
        radius=corner_radius,
        fill=shadow_color
    )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_radius))

    banner = Image.alpha_composite(banner, shadow_layer)

    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                        radius=corner_radius, fill=(60, 60, 60, 200))
    fill_width = int(bar_width * (lvl_progress / 100))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height],
                        radius=corner_radius, fill=(glow_color))
    
    text = f"{T.get('Level')[l]} {lvl_current} ({lvl_progress}%)"
    bbox = draw.textbbox((0, 0), text, font=font_small)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    text_x = bar_x + bar_width + 30 
    text_y = bar_y + (bar_height - text_h) // 2

    draw_text_with_shadow_2(draw, (text_x, text_y - lvl_text_extra_y), 
                            text, 
                            font_small, 
                            fill=(255, 255, 255, 230), 
                            shadowcolor=(0,0,0,150), 
                            shadow_offset=lvl_text_shadow_offset)

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

    extra_height = 280
    new_banner = Image.new("RGBA", (banner.width, banner.height + extra_height), (30, 30, 30, 0))
    new_banner.paste(banner, (0, 0))
    banner = new_banner
    draw = ImageDraw.Draw(banner)

    background_img = Image.open(GRAPH_PNG).convert("RGBA")

    alpha = background_img.split()[3]  # берём только альфа-канал
    banner.paste(background_img, (0, 720), alpha)


    rank_history = user_data.get("rank_history", {}).get("data")
    if rank_history:
        graph_x = 0
        graph_y = banner.height - extra_height + 24
        graph_width = banner.width - 354
        graph_height = extra_height - 84

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
        draw_gradient_line(draw, points, start_color, end_color, width=8)

    points = []
    for i, rank in enumerate(rank_history):
        x = graph_x + (i / (len(rank_history) - 1)) * graph_width
        y = graph_y + graph_height - ((rank - min_rank) / rank_range) * graph_height
        points.append((x, y))

    # ...
    
    rank_text = (
        f"#{stats.get('global_rank'):,}" 
        if stats.get("global_rank") 
        else f"{T.get('Rank')[l]}: {T.get('N/A')[l]}"
    )

    text_area_x = graph_x + graph_width + 20
    text_area_width = banner.width - text_area_x - 20

    def fit_text_font(draw, text, font_path, max_width, start_size):
        size = start_size
        while size > 10:
            font = ImageFont.truetype(font_path, size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            if text_w <= max_width:
                return font
            size -= 1
        return ImageFont.truetype(font_path, 10)

    font_rank = fit_text_font(
        draw,
        rank_text,
        font_name.path,
        text_area_width,
        start_size=font_name.size
    )

    text_x = text_area_x
    text_y = graph_y  # верх текста по верхней границе графика

    draw_text_with_shadow(
        draw,
        (text_x, text_y),
        rank_text,
        font=font_rank,
        fill=(255, 255, 255, 220),
        shadowcolor=(0, 0, 0, 180),
        shadow_offset=2
    )

    tmp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    banner.save(tmp_file.name, "PNG")
    tmp_file.close()
    # banner.convert("RGB").save("card.png") 
    return tmp_file.name



if __name__ == "__main__":   
    import asyncio    

    test_data = {'avatar_url': 'https://a.ppy.sh/11596989?1752685709.png', 'country_code': 'RU', 'default_group': 'default', 'id': 11596989, 'is_active': True, 'is_bot': False, 'is_deleted': False, 'is_online': False, 'is_supporter': True, 'last_visit': None, 'pm_friends_only': False, 'profile_colour': None, 'username': 'Fujiya', 'cover_url': 'https://assets.ppy.sh/user-profile-covers/11596989/a7db9837872a1828665ab0c92803df78ac5c8d43cc1b67304087320d59b7d439.png', 'discord': 'fujiya_sama', 'has_supported': True, 'interests': 'Жалкий, скачивай мой скин', 'join_date': '2018-01-22T11:04:24+00:00', 'location': 'whaet..', 'max_blocks': 200, 'max_friends': 1000, 'occupation': 'Ссылка на следующей строке', 'playmode': 'osu', 'playstyle': ['keyboard'], 'post_count': 2366, 'profile_hue': 211, 'profile_order': ['me', 'top_ranks', 'historical', 'beatmaps', 'medals', 'recent_activity', 'kudosu'], 'title': None, 'title_url': None, 'twitter': None, 'website': 'https://t.me/fujiyaosu/37686/134008', 'country': {'code': 'RU', 'name': 'Russian Federation'}, 'cover': {'custom_url': 'https://assets.ppy.sh/user-profile-covers/11596989/a7db9837872a1828665ab0c92803df78ac5c8d43cc1b67304087320d59b7d439.png', 'url': 'https://assets.ppy.sh/user-profile-covers/11596989/a7db9837872a1828665ab0c92803df78ac5c8d43cc1b67304087320d59b7d439.png', 'id': None}, 'kudosu': {'available': 0, 'total': 0}, 'account_history': [], 'active_tournament_banner': None, 'active_tournament_banners': [], 'badges': [], 'beatmap_playcounts_count': 13325, 'comments_count': 78, 'current_season_stats': {'division': {'colour_tier': 'gold', 'id': 72, 'image_url': 'https://assets.ppy.sh/profile-badges/spotlights-2025/summer-2025-osu-gold-2.png', 'name': 'Gold I', 'threshold': 0.25}, 'rank': 290, 'season': {'end_date': None, 'id': 46, 'name': 'osu! Beatmap Spotlights: Summer 2025', 'room_count': 6, 'start_date': '2025-08-22T17:22:58.000000Z'}, 'total_score': 7077053}, 'daily_challenge_user_stats': {'daily_streak_best': 30, 'daily_streak_current': 0, 'last_update': '2025-07-28T00:00:00+00:00', 'last_weekly_streak': '2025-07-24T00:00:00+00:00', 'playcount': 91, 'top_10p_placements': 1, 'top_50p_placements': 59, 'user_id': 11596989, 'weekly_streak_best': 26, 'weekly_streak_current': 0}, 'favourite_beatmapset_count': 57, 'follower_count': 168, 'graveyard_beatmapset_count': 19, 'groups': [], 'guest_beatmapset_count': 0, 'loved_beatmapset_count': 0, 'mapping_follower_count': 13, 'matchmaking_stats': [{'first_placements': 3, 'is_rating_provisional': True, 'plays': 4, 'pool_id': 1, 'rank': 699, 'rating': 1871, 'total_points': 238, 'user_id': 11596989, 'pool': {'active': False, 'id': 1, 'name': 'osu!', 'ruleset_id': 0, 'variant_id': 0}}, {'first_placements': 2, 'is_rating_provisional': True, 'plays': 2, 'pool_id': 11, 'rank': 366, 'rating': 1811, 'total_points': 135, 'user_id': 11596989, 'pool': {'active': False, 'id': 11, 'name': '1v1 (Week 1)', 'ruleset_id': 0, 'variant_id': 0}}], 'monthly_playcounts': [{'start_date': '2018-01-01', 'count': 844}, {'start_date': '2018-02-01', 'count': 2327}, {'start_date': '2018-03-01', 'count': 3068}, {'start_date': '2018-04-01', 'count': 2877}, {'start_date': '2018-05-01', 'count': 2834}, {'start_date': '2018-06-01', 'count': 1834}, {'start_date': '2018-07-01', 'count': 141}, {'start_date': '2018-08-01', 'count': 437}, {'start_date': '2018-09-01', 'count': 2226}, {'start_date': '2018-10-01', 'count': 1042}, {'start_date': '2018-11-01', 'count': 949}, {'start_date': '2018-12-01', 'count': 110}, {'start_date': '2019-01-01', 'count': 514}, {'start_date': '2019-02-01', 'count': 684}, {'start_date': '2019-03-01', 'count': 24}, {'start_date': '2019-04-01', 'count': 364}, {'start_date': '2019-05-01', 'count': 1637}, {'start_date': '2019-06-01', 'count': 1227}, {'start_date': '2019-07-01', 'count': 90}, {'start_date': '2019-08-01', 'count': 173}, {'start_date': '2019-09-01', 'count': 263}, {'start_date': '2019-10-01', 'count': 54}, {'start_date': '2019-11-01', 'count': 2}, {'start_date': '2019-12-01', 'count': 3}, {'start_date': '2020-01-01', 'count': 313}, {'start_date': '2020-02-01', 'count': 1135}, {'start_date': '2020-03-01', 'count': 418}, {'start_date': '2020-10-01', 'count': 6}, {'start_date': '2020-11-01', 'count': 21}, {'start_date': '2020-12-01', 'count': 16}, {'start_date': '2021-01-01', 'count': 29}, {'start_date': '2021-03-01', 'count': 111}, {'start_date': '2021-04-01', 'count': 1}, {'start_date': '2021-05-01', 'count': 10}, {'start_date': '2021-06-01', 'count': 28}, {'start_date': '2021-12-01', 'count': 38}, {'start_date': '2022-01-01', 'count': 32}, {'start_date': '2022-02-01', 'count': 41}, {'start_date': '2022-03-01', 'count': 567}, {'start_date': '2022-04-01', 'count': 865}, {'start_date': '2022-05-01', 'count': 120}, {'start_date': '2023-09-01', 'count': 72}, {'start_date': '2023-10-01', 'count': 20}, {'start_date': '2023-11-01', 'count': 237}, {'start_date': '2023-12-01', 'count': 35}, {'start_date': '2024-01-01', 'count': 24}, {'start_date': '2024-02-01', 'count': 1105}, {'start_date': '2024-03-01', 'count': 1034}, {'start_date': '2024-04-01', 'count': 2028}, {'start_date': '2024-05-01', 'count': 1480}, {'start_date': '2024-06-01', 'count': 2267}, {'start_date': '2024-07-01', 'count': 3710}, {'start_date': '2024-08-01', 'count': 2697}, {'start_date': '2024-09-01', 'count': 3014}, {'start_date': '2024-10-01', 'count': 2722}, {'start_date': '2024-11-01', 'count': 3213}, {'start_date': '2024-12-01', 'count': 4161}, {'start_date': '2025-01-01', 'count': 3124}, {'start_date': '2025-02-01', 'count': 2356}, {'start_date': '2025-03-01', 'count': 2693}, {'start_date': '2025-04-01', 'count': 1603}, {'start_date': '2025-05-01', 'count': 2028}, {'start_date': '2025-06-01', 'count': 1606}, {'start_date': '2025-07-01', 'count': 1042}, {'start_date': '2025-08-01', 'count': 1358}, {'start_date': '2025-09-01', 'count': 1393}, {'start_date': '2025-10-01', 'count': 1005}, {'start_date': '2025-11-01', 'count': 705}, {'start_date': '2025-12-01', 'count': 491}, {'start_date': '2026-01-01', 'count': 117}], 'nominated_beatmapset_count': 0, 'page': {'html': '<div class=\'bbcode bbcode--profile-page\'><center><img alt="" src="https://i.ppy.sh/8476b37fb7d3472a95f404ae33cca5f452b6dbaa/68747470733a2f2f7361737564696f2e6769746875622e696f2f6d6f656d6f656d6f656161612e706e67" loading="lazy" style="aspect-ratio: 2.3561; width: 2521px;" class="js-gallery" data-width="2521" data-height="1070" data-index="0" data-gallery-id="247490233" data-src="https://i.ppy.sh/8476b37fb7d3472a95f404ae33cca5f452b6dbaa/68747470733a2f2f7361737564696f2e6769746875622e696f2f6d6f656d6f656d6f656161612e706e67" /></center><br /><center><img alt="" src="https://i.ppy.sh/2dd7e8c87bbcf0e7d61684741d2833b9fd3c758b/68747470733a2f2f7361737564696f2e6769746875622e696f2f6d6f656d6f656d6f656d6f652e706e67" loading="lazy" style="aspect-ratio: 2.3561; width: 2521px;" class="js-gallery" data-width="2521" data-height="1070" data-index="1" data-gallery-id="247490233" data-src="https://i.ppy.sh/2dd7e8c87bbcf0e7d61684741d2833b9fd3c758b/68747470733a2f2f7361737564696f2e6769746875622e696f2f6d6f656d6f656d6f656d6f652e706e67" /></center></div>', 'raw': '[centre][img]https://sasudio.github.io/moemoemoeaaa.png[/img][/centre]\n[centre][img]https://sasudio.github.io/moemoemoemoe.png[/img][/centre]'}, 'pending_beatmapset_count': 3, 'previous_usernames': [], 'rank_highest': {'rank': 26483, 'updated_at': '2025-11-11T13:01:29Z'}, 'ranked_beatmapset_count': 0, 'replays_watched_counts': [{'start_date': '2021-09-01', 'count': 1}, {'start_date': '2024-07-01', 'count': 1}, {'start_date': '2024-08-01', 'count': 2}, {'start_date': '2024-11-01', 'count': 3}, {'start_date': '2024-12-01', 'count': 1}, {'start_date': '2025-01-01', 'count': 5}, {'start_date': '2025-02-01', 'count': 5}, {'start_date': '2025-03-01', 'count': 3}, {'start_date': '2025-04-01', 'count': 3}, {'start_date': '2025-05-01', 'count': 6}, {'start_date': '2025-06-01', 'count': 5}, {'start_date': '2025-07-01', 'count': 17}, {'start_date': '2025-08-01', 'count': 1}, {'start_date': '2025-09-01', 'count': 1}, {'start_date': '2025-10-01', 'count': 1}, {'start_date': '2025-11-01', 'count': 3}, {'start_date': '2025-12-01', 'count': 4}], 'scores_best_count': 200, 'scores_first_count': 3, 'scores_pinned_count': 30, 'scores_recent_count': 16, 'statistics': {'count_100': 3601289, 'count_300': 20618482, 'count_50': 452541, 'count_miss': 1039727, 'level': {'current': 102, 'progress': 85}, 'global_rank': 27507, 'global_rank_percent': 0.009925000523185035, 'global_rank_exp': None, 'pp': 7376.3, 'pp_exp': 0, 'ranked_score': 75757399088, 'hit_accuracy': 98.4753, 'play_count': 70685, 'play_time': 5982889, 'total_score': 312550724968, 'total_hits': 24672312, 'maximum_combo': 3905, 'replays_watched_by_others': 59, 'is_ranked': True, 'grade_counts': {'ss': 140, 'ssh': 130, 's': 1566, 'sh': 248, 'a': 4042}, 'country_rank': 2544, 'rank': {'country': 2544}}, 'support_level': 2, 'team': {'flag_url': 'https://assets.ppy.sh/teams/flag/799/cf0494ab3851e712f8b39db1f62090a75997b79e29fa5edb13a97b050bb192a8.jpeg', 'id': 799, 'name': 'Neko Institute of Science', 'short_name': 'osu!'}, 'user_achievements': [{'achieved_at': '2025-03-11T16:06:24Z', 'achievement_id': 193}, {'achieved_at': '2025-03-10T17:48:00Z', 'achievement_id': 292}, {'achieved_at': '2025-03-10T13:45:04Z', 'achievement_id': 24}, {'achieved_at': '2025-03-10T12:30:26Z', 'achievement_id': 204}, {'achieved_at': '2025-03-10T12:22:12Z', 'achievement_id': 200}, {'achieved_at': '2025-03-10T12:17:14Z', 'achievement_id': 197}, {'achieved_at': '2025-03-10T12:14:00Z', 'achievement_id': 196}, {'achieved_at': '2025-03-10T11:55:07Z', 'achievement_id': 159}, {'achieved_at': '2025-03-09T18:43:00Z', 'achievement_id': 220}, {'achieved_at': '2025-03-09T18:26:37Z', 'achievement_id': 249}, {'achieved_at': '2025-03-09T18:09:09Z', 'achievement_id': 261}, {'achieved_at': '2025-03-09T17:29:31Z', 'achievement_id': 311}, {'achieved_at': '2025-03-09T17:16:09Z', 'achievement_id': 312}, {'achieved_at': '2025-03-09T17:04:59Z', 'achievement_id': 313}, {'achieved_at': '2025-03-09T16:53:57Z', 'achievement_id': 314}, {'achieved_at': '2025-03-09T16:43:01Z', 'achievement_id': 315}, {'achieved_at': '2025-03-09T16:35:17Z', 'achievement_id': 316}, {'achieved_at': '2025-03-09T16:27:58Z', 'achievement_id': 325}, {'achieved_at': '2025-03-03T16:22:14Z', 'achievement_id': 149}, {'achieved_at': '2025-03-02T15:08:36Z', 'achievement_id': 256}, {'achieved_at': '2025-03-01T13:31:50Z', 'achievement_id': 218}, {'achieved_at': '2025-02-28T19:40:05Z', 'achievement_id': 322}, {'achieved_at': '2025-02-27T15:29:44Z', 'achievement_id': 232}, {'achieved_at': '2025-02-26T13:16:44Z', 'achievement_id': 231}, {'achieved_at': '2025-02-25T19:49:35Z', 'achievement_id': 258}, {'achieved_at': '2025-02-24T14:08:59Z', 'achievement_id': 263}, {'achieved_at': '2025-02-23T16:16:29Z', 'achievement_id': 251}, {'achieved_at': '2025-02-23T15:22:24Z', 'achievement_id': 264}, {'achieved_at': '2025-02-21T20:20:37Z', 'achievement_id': 240}, {'achieved_at': '2025-02-20T21:48:39Z', 'achievement_id': 230}, {'achieved_at': '2025-02-19T20:27:39Z', 'achievement_id': 23}, {'achieved_at': '2025-02-18T20:28:24Z', 'achievement_id': 238}, {'achieved_at': '2025-02-17T19:59:35Z', 'achievement_id': 237}, {'achieved_at': '2025-02-16T16:56:45Z', 'achievement_id': 235}, {'achieved_at': '2025-02-16T15:56:45Z', 'achievement_id': 239}, {'achieved_at': '2025-02-15T17:33:13Z', 'achievement_id': 282}, {'achieved_at': '2025-02-14T18:25:03Z', 'achievement_id': 229}, {'achieved_at': '2025-02-12T20:53:22Z', 'achievement_id': 226}, {'achieved_at': '2025-02-11T09:56:25Z', 'achievement_id': 252}, {'achieved_at': '2025-02-10T18:33:38Z', 'achievement_id': 227}, {'achieved_at': '2025-02-09T12:46:07Z', 'achievement_id': 214}, {'achieved_at': '2025-02-08T10:39:19Z', 'achievement_id': 216}, {'achieved_at': '2025-02-07T15:17:45Z', 'achievement_id': 250}, {'achieved_at': '2025-02-06T11:28:54Z', 'achievement_id': 208}, {'achieved_at': '2025-02-05T12:52:07Z', 'achievement_id': 37}, {'achieved_at': '2025-02-04T15:45:10Z', 'achievement_id': 36}, {'achieved_at': '2025-02-03T16:05:33Z', 'achievement_id': 35}, {'achieved_at': '2025-02-02T13:06:05Z', 'achievement_id': 74}, {'achieved_at': '2025-01-31T09:22:55Z', 'achievement_id': 104}, {'achieved_at': '2025-01-30T16:50:03Z', 'achievement_id': 34}, {'achieved_at': '2025-01-29T18:03:27Z', 'achievement_id': 27}, {'achieved_at': '2025-01-26T20:22:07Z', 'achievement_id': 26}, {'achieved_at': '2025-01-23T15:12:47Z', 'achievement_id': 157}, {'achieved_at': '2025-01-23T15:00:03Z', 'achievement_id': 318}, {'achieved_at': '2025-01-23T14:51:44Z', 'achievement_id': 271}, {'achieved_at': '2025-01-23T14:11:47Z', 'achievement_id': 300}, {'achieved_at': '2025-01-23T10:45:16Z', 'achievement_id': 341}, {'achieved_at': '2025-01-22T13:51:01Z', 'achievement_id': 25}, {'achieved_at': '2025-01-21T10:09:24Z', 'achievement_id': 338}, {'achieved_at': '2025-01-20T12:45:59Z', 'achievement_id': 19}, {'achieved_at': '2025-01-20T12:07:52Z', 'achievement_id': 309}, {'achieved_at': '2025-01-18T16:11:10Z', 'achievement_id': 350}, {'achieved_at': '2025-01-18T12:46:45Z', 'achievement_id': 248}, {'achieved_at': '2025-01-17T14:17:06Z', 'achievement_id': 18}, {'achieved_at': '2025-01-15T15:10:12Z', 'achievement_id': 206}, {'achieved_at': '2025-01-13T21:16:35Z', 'achievement_id': 190}, {'achieved_at': '2025-01-11T17:12:45Z', 'achievement_id': 290}, {'achieved_at': '2025-01-10T13:35:50Z', 'achievement_id': 288}, {'achieved_at': '2025-01-09T10:00:14Z', 'achievement_id': 257}, {'achieved_at': '2025-01-07T21:23:17Z', 'achievement_id': 267}, {'achieved_at': '2025-01-06T11:21:17Z', 'achievement_id': 185}, {'achieved_at': '2025-01-04T17:42:06Z', 'achievement_id': 170}, {'achieved_at': '2025-01-04T17:20:26Z', 'achievement_id': 265}, {'achieved_at': '2025-01-04T16:25:58Z', 'achievement_id': 323}, {'achieved_at': '2025-01-04T15:49:11Z', 'achievement_id': 179}, {'achieved_at': '2025-01-04T14:28:59Z', 'achievement_id': 201}, {'achieved_at': '2025-01-04T11:50:18Z', 'achievement_id': 335}, {'achieved_at': '2025-01-03T21:50:45Z', 'achievement_id': 266}, {'achieved_at': '2025-01-03T14:55:49Z', 'achievement_id': 14}, {'achieved_at': '2025-01-02T19:49:10Z', 'achievement_id': 12}, {'achieved_at': '2025-01-02T10:03:50Z', 'achievement_id': 11}, {'achieved_at': '2025-01-01T15:33:07Z', 'achievement_id': 10}, {'achieved_at': '2024-12-31T14:22:05Z', 'achievement_id': 296}, {'achieved_at': '2024-12-31T12:40:59Z', 'achievement_id': 255}, {'achieved_at': '2024-12-29T15:07:12Z', 'achievement_id': 155}, {'achieved_at': '2024-12-29T14:48:08Z', 'achievement_id': 189}, {'achieved_at': '2024-12-29T14:18:17Z', 'achievement_id': 9}, {'achieved_at': '2024-12-29T13:58:37Z', 'achievement_id': 8}, {'achieved_at': '2024-12-29T13:25:56Z', 'achievement_id': 260}, {'achieved_at': '2024-12-28T22:07:59Z', 'achievement_id': 228}, {'achieved_at': '2024-12-28T21:49:51Z', 'achievement_id': 215}, {'achieved_at': '2024-12-28T21:36:02Z', 'achievement_id': 209}, {'achieved_at': '2024-12-28T21:21:34Z', 'achievement_id': 207}, {'achieved_at': '2024-12-28T20:58:23Z', 'achievement_id': 210}, {'achieved_at': '2024-12-28T19:04:55Z', 'achievement_id': 306}, {'achieved_at': '2024-12-28T18:36:01Z', 'achievement_id': 304}, {'achieved_at': '2024-12-27T14:03:20Z', 'achievement_id': 205}, {'achieved_at': '2024-12-26T19:35:59Z', 'achievement_id': 283}, {'achieved_at': '2024-12-26T19:26:27Z', 'achievement_id': 289}, {'achieved_at': '2024-12-26T19:18:46Z', 'achievement_id': 262}, {'achieved_at': '2024-12-26T19:10:22Z', 'achievement_id': 253}, {'achieved_at': '2024-12-26T16:36:08Z', 'achievement_id': 348}, {'achieved_at': '2024-12-26T13:16:55Z', 'achievement_id': 161}, {'achieved_at': '2024-12-26T13:05:02Z', 'achievement_id': 172}, {'achieved_at': '2024-12-26T13:01:09Z', 'achievement_id': 174}, {'achieved_at': '2024-12-26T12:48:16Z', 'achievement_id': 188}, {'achieved_at': '2024-12-26T12:39:14Z', 'achievement_id': 187}, {'achieved_at': '2024-12-26T12:31:55Z', 'achievement_id': 186}, {'achieved_at': '2024-12-26T12:28:05Z', 'achievement_id': 184}, {'achieved_at': '2024-12-26T12:20:14Z', 'achievement_id': 183}, {'achieved_at': '2024-12-26T12:06:36Z', 'achievement_id': 182}, {'achieved_at': '2024-12-26T11:57:06Z', 'achievement_id': 181}, {'achieved_at': '2024-12-26T11:47:19Z', 'achievement_id': 180}, {'achieved_at': '2024-12-26T11:28:45Z', 'achievement_id': 169}, {'achieved_at': '2024-12-26T11:11:59Z', 'achievement_id': 167}, {'achieved_at': '2024-12-26T10:47:24Z', 'achievement_id': 166}, {'achieved_at': '2024-12-26T10:20:18Z', 'achievement_id': 349}, {'achieved_at': '2024-12-26T10:17:30Z', 'achievement_id': 346}, {'achieved_at': '2024-12-25T21:39:04Z', 'achievement_id': 142}, {'achieved_at': '2024-12-25T15:48:46Z', 'achievement_id': 84}, {'achieved_at': '2024-12-25T15:45:29Z', 'achievement_id': 83}, {'achieved_at': '2024-12-25T15:40:58Z', 'achievement_id': 82}, {'achieved_at': '2024-12-25T15:12:09Z', 'achievement_id': 234}, {'achieved_at': '2024-12-25T15:01:44Z', 'achievement_id': 310}, {'achieved_at': '2024-12-25T14:31:28Z', 'achievement_id': 340}, {'achieved_at': '2024-12-25T14:31:28Z', 'achievement_id': 339}, {'achieved_at': '2024-12-25T09:49:23Z', 'achievement_id': 233}, {'achieved_at': '2024-12-25T09:14:53Z', 'achievement_id': 337}, {'achieved_at': '2024-12-25T09:14:53Z', 'achievement_id': 336}, {'achieved_at': '2024-12-24T14:49:16Z', 'achievement_id': 145}, {'achieved_at': '2024-12-19T16:33:35Z', 'achievement_id': 326}, {'achieved_at': '2024-12-15T12:55:30Z', 'achievement_id': 28}, {'achieved_at': '2024-12-02T12:43:02Z', 'achievement_id': 160}, {'achieved_at': '2024-12-01T17:25:19Z', 'achievement_id': 297}, {'achieved_at': '2024-11-14T14:17:39Z', 'achievement_id': 328}, {'achieved_at': '2024-10-24T13:38:16Z', 'achievement_id': 244}, {'achieved_at': '2024-09-21T17:25:15Z', 'achievement_id': 301}, {'achieved_at': '2024-09-21T17:25:15Z', 'achievement_id': 173}, {'achieved_at': '2024-09-15T20:51:40Z', 'achievement_id': 213}, {'achieved_at': '2024-09-15T19:09:29Z', 'achievement_id': 158}, {'achieved_at': '2024-09-14T21:54:57Z', 'achievement_id': 268}, {'achieved_at': '2024-09-14T21:52:20Z', 'achievement_id': 17}, {'achieved_at': '2024-09-12T10:52:53Z', 'achievement_id': 287}, {'achieved_at': '2024-09-10T19:42:29Z', 'achievement_id': 191}, {'achieved_at': '2024-09-10T19:13:41Z', 'achievement_id': 7}, {'achieved_at': '2024-09-10T18:35:35Z', 'achievement_id': 154}, {'achieved_at': '2024-09-10T18:32:05Z', 'achievement_id': 153}, {'achieved_at': '2024-09-10T18:24:39Z', 'achievement_id': 151}, {'achieved_at': '2024-09-10T18:10:48Z', 'achievement_id': 150}, {'achieved_at': '2024-09-09T13:35:31Z', 'achievement_id': 81}, {'achieved_at': '2024-09-09T13:05:37Z', 'achievement_id': 329}, {'achieved_at': '2024-09-09T12:54:33Z', 'achievement_id': 13}, {'achieved_at': '2024-09-05T12:16:10Z', 'achievement_id': 279}, {'achieved_at': '2024-09-05T12:03:45Z', 'achievement_id': 275}, {'achieved_at': '2024-09-05T11:57:07Z', 'achievement_id': 274}, {'achieved_at': '2024-08-30T14:17:14Z', 'achievement_id': 272}, {'achieved_at': '2024-08-30T14:17:14Z', 'achievement_id': 43}, {'achieved_at': '2024-08-10T18:42:56Z', 'achievement_id': 41}, {'achieved_at': '2024-08-10T17:59:48Z', 'achievement_id': 276}, {'achieved_at': '2024-08-10T16:43:53Z', 'achievement_id': 135}, {'achieved_at': '2024-08-10T16:18:33Z', 'achievement_id': 16}, {'achieved_at': '2024-08-09T20:15:50Z', 'achievement_id': 42}, {'achieved_at': '2024-08-07T11:26:38Z', 'achievement_id': 178}, {'achieved_at': '2024-08-07T11:22:27Z', 'achievement_id': 171}, {'achieved_at': '2024-08-07T11:10:42Z', 'achievement_id': 156}, {'achieved_at': '2024-08-07T11:01:20Z', 'achievement_id': 143}, {'achieved_at': '2024-08-06T19:48:18Z', 'achievement_id': 221}, {'achieved_at': '2024-08-03T20:38:07Z', 'achievement_id': 334}, {'achieved_at': '2024-07-14T14:56:11Z', 'achievement_id': 144}, {'achieved_at': '2024-07-09T18:31:44Z', 'achievement_id': 254}, {'achieved_at': '2024-07-08T16:21:09Z', 'achievement_id': 242}, {'achieved_at': '2024-06-28T13:31:50Z', 'achievement_id': 50}, {'achieved_at': '2024-06-28T13:15:14Z', 'achievement_id': 31}, {'achieved_at': '2024-06-27T21:52:48Z', 'achievement_id': 73}, {'achieved_at': '2024-06-26T16:30:02Z', 'achievement_id': 133}, {'achieved_at': '2024-06-26T16:30:01Z', 'achievement_id': 44}, {'achieved_at': '2024-06-13T14:04:54Z', 'achievement_id': 236}, {'achieved_at': '2024-06-11T19:00:29Z', 'achievement_id': 273}, {'achieved_at': '2024-06-11T18:07:12Z', 'achievement_id': 270}, {'achieved_at': '2024-06-11T17:56:50Z', 'achievement_id': 225}, {'achieved_at': '2024-06-11T17:30:52Z', 'achievement_id': 147}, {'achieved_at': '2024-06-11T17:27:05Z', 'achievement_id': 303}, {'achieved_at': '2024-06-11T17:03:30Z', 'achievement_id': 134}, {'achieved_at': '2024-06-11T16:41:42Z', 'achievement_id': 136}, {'achieved_at': '2024-06-11T16:35:42Z', 'achievement_id': 284}, {'achieved_at': '2024-06-10T20:43:15Z', 'achievement_id': 295}, {'achieved_at': '2024-06-04T20:40:23Z', 'achievement_id': 246}, {'achieved_at': '2024-06-01T20:34:21Z', 'achievement_id': 294}, {'achieved_at': '2024-05-26T18:37:44Z', 'achievement_id': 331}, {'achieved_at': '2024-05-25T21:05:58Z', 'achievement_id': 302}, {'achieved_at': '2024-05-25T20:58:41Z', 'achievement_id': 140}, {'achieved_at': '2024-05-23T15:47:32Z', 'achievement_id': 269}, {'achieved_at': '2024-05-23T15:34:34Z', 'achievement_id': 223}, {'achieved_at': '2024-05-23T15:19:28Z', 'achievement_id': 103}, {'achieved_at': '2024-05-22T16:19:12Z', 'achievement_id': 319}, {'achieved_at': '2024-05-21T20:33:57Z', 'achievement_id': 321}, {'achieved_at': '2024-05-21T19:43:36Z', 'achievement_id': 177}, {'achieved_at': '2024-05-11T20:18:24Z', 'achievement_id': 38}, {'achieved_at': '2024-05-08T16:00:22Z', 'achievement_id': 247}, {'achieved_at': '2024-04-19T20:52:28Z', 'achievement_id': 68}, {'achieved_at': '2024-04-04T18:40:16Z', 'achievement_id': 165}, {'achieved_at': '2024-04-03T21:08:47Z', 'achievement_id': 317}, {'achieved_at': '2024-04-02T19:42:17Z', 'achievement_id': 202}, {'achieved_at': '2024-04-01T19:31:14Z', 'achievement_id': 241}, {'achieved_at': '2024-03-19T19:25:07Z', 'achievement_id': 62}, {'achieved_at': '2024-03-18T20:47:45Z', 'achievement_id': 308}, {'achieved_at': '2024-03-12T21:07:08Z', 'achievement_id': 259}, {'achieved_at': '2023-09-12T08:57:01Z', 'achievement_id': 22}, {'achieved_at': '2022-04-14T18:33:21Z', 'achievement_id': 5}, {'achieved_at': '2022-03-26T19:01:25Z', 'achievement_id': 164}, {'achieved_at': '2022-03-26T18:37:33Z', 'achievement_id': 163}, {'achieved_at': '2022-03-26T18:17:58Z', 'achievement_id': 194}, {'achieved_at': '2022-03-26T12:53:16Z', 'achievement_id': 162}, {'achieved_at': '2022-03-26T11:05:43Z', 'achievement_id': 6}, {'achieved_at': '2020-02-03T19:50:04Z', 'achievement_id': 222}, {'achieved_at': '2020-02-01T09:16:34Z', 'achievement_id': 141}, {'achieved_at': '2019-05-12T09:50:02Z', 'achievement_id': 168}, {'achieved_at': '2019-05-11T09:53:33Z', 'achievement_id': 61}, {'achieved_at': '2019-04-27T15:32:04Z', 'achievement_id': 91}, {'achieved_at': '2019-02-24T16:02:05Z', 'achievement_id': 90}, {'achieved_at': '2019-02-11T15:07:35Z', 'achievement_id': 47}, {'achieved_at': '2019-01-26T09:29:37Z', 'achievement_id': 89}, {'achieved_at': '2019-01-17T19:13:51Z', 'achievement_id': 96}, {'achieved_at': '2019-01-04T14:39:30Z', 'achievement_id': 95}, {'achieved_at': '2019-01-02T18:00:19Z', 'achievement_id': 112}, {'achieved_at': '2018-11-27T17:35:24Z', 'achievement_id': 80}, {'achieved_at': '2018-11-09T18:59:39Z', 'achievement_id': 72}, {'achieved_at': '2018-11-09T18:51:03Z', 'achievement_id': 71}, {'achieved_at': '2018-09-15T18:31:18Z', 'achievement_id': 46}, {'achieved_at': '2018-09-11T18:35:01Z', 'achievement_id': 21}, {'achieved_at': '2018-09-09T12:53:44Z', 'achievement_id': 88}, {'achieved_at': '2018-09-09T12:40:00Z', 'achievement_id': 111}, {'achieved_at': '2018-09-06T14:48:37Z', 'achievement_id': 54}, {'achieved_at': '2018-09-06T11:24:45Z', 'achievement_id': 79}, {'achieved_at': '2018-09-06T11:07:49Z', 'achievement_id': 87}, {'achieved_at': '2018-09-04T18:03:49Z', 'achievement_id': 67}, {'achieved_at': '2018-05-25T15:19:05Z', 'achievement_id': 60}, {'achieved_at': '2018-05-24T16:15:35Z', 'achievement_id': 152}, {'achieved_at': '2018-04-16T13:37:15Z', 'achievement_id': 66}, {'achieved_at': '2018-03-21T18:11:37Z', 'achievement_id': 59}, {'achieved_at': '2018-03-18T19:43:27Z', 'achievement_id': 20}, {'achieved_at': '2018-03-17T09:54:29Z', 'achievement_id': 4}, {'achieved_at': '2018-03-15T15:11:05Z', 'achievement_id': 139}, {'achieved_at': '2018-03-15T15:06:20Z', 'achievement_id': 40}, {'achieved_at': '2018-03-15T15:03:13Z', 'achievement_id': 148}, {'achieved_at': '2018-03-03T15:17:32Z', 'achievement_id': 126}, {'achieved_at': '2018-03-03T15:12:17Z', 'achievement_id': 125}, {'achieved_at': '2018-03-03T15:11:07Z', 'achievement_id': 131}, {'achieved_at': '2018-03-03T15:06:10Z', 'achievement_id': 124}, {'achieved_at': '2018-02-27T18:15:23Z', 'achievement_id': 132}, {'achieved_at': '2018-02-26T14:15:42Z', 'achievement_id': 58}, {'achieved_at': '2018-02-25T12:49:44Z', 'achievement_id': 65}, {'achieved_at': '2018-02-09T18:12:21Z', 'achievement_id': 3}, {'achieved_at': '2018-02-04T14:58:04Z', 'achievement_id': 138}, {'achieved_at': '2018-02-03T17:49:19Z', 'achievement_id': 39}, {'achieved_at': '2018-02-03T16:00:01Z', 'achievement_id': 57}, {'achieved_at': '2018-02-01T11:07:24Z', 'achievement_id': 119}, {'achieved_at': '2018-02-01T10:39:21Z', 'achievement_id': 64}, {'achieved_at': '2018-01-30T14:36:43Z', 'achievement_id': 137}, {'achieved_at': '2018-01-29T15:02:20Z', 'achievement_id': 120}, {'achieved_at': '2018-01-29T14:30:28Z', 'achievement_id': 176}, {'achieved_at': '2018-01-28T13:18:56Z', 'achievement_id': 1}, {'achieved_at': '2018-01-26T17:56:54Z', 'achievement_id': 175}, {'achieved_at': '2018-01-26T17:20:41Z', 'achievement_id': 128}, {'achieved_at': '2018-01-24T17:44:22Z', 'achievement_id': 15}, {'achieved_at': '2018-01-24T16:49:38Z', 'achievement_id': 122}, {'achieved_at': '2018-01-24T16:46:32Z', 'achievement_id': 63}, {'achieved_at': '2018-01-24T15:13:36Z', 'achievement_id': 123}, {'achieved_at': '2018-01-24T15:13:36Z', 'achievement_id': 56}, {'achieved_at': '2018-01-23T18:52:25Z', 'achievement_id': 121}, {'achieved_at': '2018-01-23T16:36:47Z', 'achievement_id': 127}, {'achieved_at': '2018-01-23T16:31:51Z', 'achievement_id': 55}], 'rank_history': {'mode': 'osu', 'data': [27444, 27456, 27472, 27486, 27499, 27509, 27524, 27539, 27554, 27558, 27573, 27593, 27603, 27610, 27624, 27640, 27661, 27673, 27696, 27722, 27738, 27755, 27766, 27781, 27796, 27817, 27827, 27838, 27857, 27875, 26365, 26398, 26479, 26503, 26520, 26540, 26563, 26597, 26609, 26624, 26639, 26656, 26672, 26679, 26699, 26717, 26729, 26752, 26777, 26796, 26814, 26844, 26859, 26867, 26886, 26904, 26915, 26942, 26970, 26982, 27003, 27022, 27043, 27050, 27069, 27084, 27099, 27120, 27131, 27151, 27175, 27187, 27216, 27235, 27255, 27268, 27279, 27294, 27308, 27328, 27346, 27374, 27393, 27411, 27426, 27442, 27460, 27479, 27498, 27507]}, 'rankHistory': {'mode': 'osu', 'data': [27444, 27456, 27472, 27486, 27499, 27509, 27524, 27539, 27554, 27558, 27573, 27593, 27603, 27610, 27624, 27640, 27661, 27673, 27696, 27722, 27738, 27755, 27766, 27781, 27796, 27817, 27827, 27838, 27857, 27875, 26365, 26398, 26479, 26503, 26520, 26540, 26563, 26597, 26609, 26624, 26639, 26656, 26672, 26679, 26699, 26717, 26729, 26752, 26777, 26796, 26814, 26844, 26859, 26867, 26886, 26904, 26915, 26942, 26970, 26982, 27003, 27022, 27043, 27050, 27069, 27084, 27099, 27120, 27131, 27151, 27175, 27187, 27216, 27235, 27255, 27268, 27279, 27294, 27308, 27328, 27346, 27374, 27393, 27411, 27426, 27442, 27460, 27479, 27498, 27507]}, 'ranked_and_approved_beatmapset_count': 0, 'unranked_beatmapset_count': 3}

    print(asyncio.run(create_profile_image(test_data, 9999)))