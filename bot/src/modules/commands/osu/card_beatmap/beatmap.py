


import io
import os
import aiohttp
import asyncio
from datetime import datetime, timedelta, date
from PIL import Image, ImageDraw, ImageFont

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import delete_user_message, delete_message_after_delay
from ....external.osu_http import beatmap, fetch_txt_beatmaps
from ....external.osu_api import get_osu_token, get_beatmap
from ....external.localapi import get_map_stats_neko_api
from ....utils.osu_conversions import get_mods_info, apply_mods_to_stats
from ....utils.text_format import format_osu_date

from config import OSU_MAP_REGEX, COOLDOWN_CARD_COMMAND, BOT_DIR, COVERS_DIR



async def start_beatmap_card(update, context, user_request=True):
    if user_request: await log_all_update(update)
    asyncio.create_task(beatmap_card(update, context, user_request))

async def beatmap_card(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request=True):    
    try:
        message_text = update.message.text.strip()
        match = OSU_MAP_REGEX.search(message_text)
        message = update.message
        if user_request:
            if not match:        
                msg = await update.message.reply_text(
                    "❌ Нужна ссылка на карту"
                )
                asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
                asyncio.create_task(delete_user_message(update, context, delay=4))
                return
        
        if match is None: return
        beatmap_id = match.group(1) if match.group(1) else match.group(2)
    
        if user_request: warn_text = f"⏳ Подождите {COOLDOWN_CARD_COMMAND} секунд"
        else: warn_text = None
        can_run = await check_user_cooldown(
            command_name="render_score",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_CARD_COMMAND,           
            update=update,
            context=context,
            warn_text=warn_text
        )
        if not can_run:
            return
    
    except Exception as e:
        print(e)
        return
    
    

    max_attempts = 3
    if user_request:
        for _ in range(max_attempts):
            try:
                if update.message:
                    temp_message = await update.message.reply_text(
                        "`Загрузка...`",
                        parse_mode="Markdown"
                    )
                break
            except Exception as e: print(e)
    
    for _ in range(max_attempts):
        try:             
            maps_ids = []
            maps_ids.append(beatmap_id)

            results, failed = await fetch_txt_beatmaps(maps_ids)

            token = await get_osu_token()
            map_data = await get_beatmap(beatmap_id, token)

            def format_length(seconds: int) -> str:
                h, m = divmod(seconds, 3600)
                m, s = divmod(m, 60)
                if h > 0:
                    return f"{h}:{m:02}:{s:02}"
                return f"{m}:{s:02}"

            bpm_map = map_data['bpm']
            mode = map_data['mode_int']
            if mode != 0: return
            length = format_length(map_data['total_length'])
            version = map_data['version']
            status = map_data['status']
            circles, sliders = map_data['count_circles'], map_data['count_sliders']
            updated = map_data['last_updated']
            plays = f"{map_data['playcount']:,}"
            psc = map_data['passcount']
            max_combo_map = f" (x{map_data['max_combo']:,})"
            mapper = map_data['owners'][0]['username']
            artist = map_data['beatmapset']['artist']
            creator = map_data['beatmapset']['creator']
            title = map_data['beatmapset']['title'] +" - " + artist + ' [' + version +']'           
            favs =  f"{map_data['beatmapset']['favourite_count']:,}"

            bg_url = map_data['beatmapset']['covers']['cover']
            
            extra_img = None
            now = datetime.now()
            bg_file = None
            for f in os.listdir(COVERS_DIR):
                if f.startswith(f"{beatmap_id}_") and f.endswith(".png"):
                    path = os.path.join(COVERS_DIR, f)
                    mtime = datetime.fromtimestamp(os.path.getmtime(path))
                    if now - mtime < timedelta(hours=1):
                        bg_file = path
                        break
                
            if bg_file:
                extra_img = Image.open(bg_file).convert("RGBA")
                bg_path = bg_file
                print("using cached bg")
            else:
                bg_path = os.path.join(COVERS_DIR, "default.png")
                extra_img = None
                MAX_ATTEMPTS = 2
                for attempt_bg in range(1, MAX_ATTEMPTS + 1):
                    try:
                        timeout = aiohttp.ClientTimeout(total=3)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(bg_url) as resp:
                                if resp.status == 200:
                                    def add_rounded_corners(imge: Image.Image, radius: int) -> Image.Image:
                                        # создаем маску в два раза больше для сглаживания
                                        big_size = (imge.size[0]*2, imge.size[1]*2)
                                        mask = Image.new("L", big_size, 0)
                                        draw_mask = ImageDraw.Draw(mask)
                                        draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)
                                        
                                        # сжимаем маску обратно для сглаживания
                                        mask = mask.resize(imge.size, Image.LANCZOS)
                                        
                                        # применяем альфу
                                        imge.putalpha(mask)
                                        return imge
                                    extra_img_data = await resp.read()
                                    extra_img = Image.open(io.BytesIO(extra_img_data)).convert("RGBA")
                                    extra_img.thumbnail((512, 512))
                                    extra_img = add_rounded_corners(extra_img, radius=12)
                                    bg_filename = f"{beatmap_id}_{now.hour}{now.minute}.png"
                                    bg_path = os.path.join(COVERS_DIR, bg_filename)
                                    extra_img.save(bg_path, format="PNG")
                                    break
                    except Exception as e:
                        print(f"Ошибка при скачивании аватарки: {e}")
            path, values = await beatmap(beatmap_id)
           
            #neko API 
            payload = {
                "map_path": str(beatmap_id), 
                
                "n300": 0,
                "n100": 0,
                "n50": 0,
                "misses": 0,                   
                
                "mods": str(""), 
                "combo": int(0),      
                "accuracy": float(100),    
                
                "lazer": bool(True),          
                "clock_rate": float(1.0),  

                "custom_ar": values.get("ar"),
                "custom_cs": values.get("cs"),
                "custom_hp": values.get("hp"),
                "custom_od": values.get("od"),
            }

            try:
                pp_data = await get_map_stats_neko_api(payload)

                pp = pp_data.get("pp")
                choke = pp_data.get("no_choke_pp")
                max_pp = pp_data.get("perfect_pp")

                stars = pp_data.get("star_rating")
                max_combo = pp_data.get("perfect_combo")
                expected_bpm = pp_data.get("expected_bpm")

                n300 = pp_data.get("n300")
                n100 = pp_data.get("n100") 
                n50 = pp_data.get("n50")
                expected_miss = pp_data.get("misses")

                aim_raw = pp_data.get("aim")
                acc_raw = pp_data.get("acc")
                speed_raw = pp_data.get("speed")
            
            except Exception as e:
                print(f"neko API failed: {e}")
            
            mods_list = ["NM", "EZ", "HR", "DT", "HR+DT"]

            ar_values = []
            od_values = []
            cs_values = []
            hp_values = []

            for mods_str in mods_list:
                speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)

                bpm, ar, od, cs, hp = apply_mods_to_stats(
                    expected_bpm, values.get("ar"), values.get("od"), values.get("cs"), values.get("cs"),
                    speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
                )

                ar_values.append(round(ar, 2))
                od_values.append(round(od, 2))
                cs_values.append(round(cs, 2))
                hp_values.append(round(hp, 2))

            fill_colors = [(255,255,255), (98, 240, 124), (240, 223, 98), (240,128,98), (200,200,200)]
          

            values = {
                "speed": speed_raw,
                "acc": acc_raw,
                "aim": aim_raw
            }

            max_val = max(values.values())

            normalized = {k: v / max_val for k, v in values.items()}

            speed_data = normalized["speed"]
            acc_data   = normalized["acc"]
            aim_data   = normalized["aim"]

            width = 1400
            height = 800
            padding = 480

            img = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/bg.png").convert("RGBA")
            draw = ImageDraw.Draw(img)

            asset = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/mapcard.png").convert("RGBA")
            img.paste(asset, (0, 0), mask=asset.split()[3])


            font_italic_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 38)
            font_black_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 40)
            font_bold_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 22)
            font_noto = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/NotoEmoji.ttf", 46)
            font_regular_nano = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Regular.ttf", 26)
            font_bold_med_3 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 28)
            font_bold_med_4 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 34)
            font_black_small_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 28)
            font_thin_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Thin.ttf", 28)
            font_light_italic_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 30)
            font_black_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 44)
            font_black_big_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 30)
            font = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 32)


            offset_x_w = 380
            offset_y_w = 145
            x1, x2 = padding + offset_x_w, width - padding + offset_x_w
            unit1 = (x2 - x1) / (4 + 4*2 + 2*4)  
            # 1-5: 4 шагов по 1
            # 5-9: 4 шагов по 2 (2к1)
            # 9-11: 2 шагов по 4 (4к1)

            def value_to_x_custom(val):
                if val <= 5:
                    return x1 + (val - 1) * unit1
                elif val <= 9:
                    return x1 + 4*unit1 + (val - 5) * 2 * unit1
                else:  # 9-11
                    return x1 + 4*unit1 + 8*unit1 + (val - 9) * 4 * unit1

            scale_1_5 = [1, 2, 3, 4, 5]
            scale_5_9 = [5 + i*0.5 for i in range(1, 9)]  # 5.5,6,6.5 ...9
            scale_9_11 = [9 + i*0.25 for i in range(1, 9)]  # 9.25,9.5,...11
            all_scale = scale_1_5 + scale_5_9 + scale_9_11

            def draw_textbox_center(draw, x_center, y_top, text, font, fill_text=(255,255,255), fill_box=None, padding=2):
                bbox = draw.textbbox((0,0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = x_center - text_width/2
                y = y_top
                if fill_box:
                    draw.rectangle([x-padding, y-padding, x+text_width+padding, y+text_height+padding], fill=fill_box)
                draw.text((x, y), text, fill=fill_text, font=font)

            # y_positions = [120, 305, 405]
            # for y in y_positions:
            #     draw.line((x1 -10, y, x2 + 10, y), fill=(150,150,150), width=1)
            y_grid_top = 10 + offset_y_w
            y_grid_bottom = 150 + offset_y_w
            for val in all_scale:
                x = value_to_x_custom(val)
                if int(val) == val:
                    if val in(1, 0): continue
                    if val in (1, 2, 3, 4):
                        draw.line((x, y_grid_top + 5, x, y_grid_bottom - 10), fill=(200,200,200), width=2)
                    else:
                        draw.line((x, y_grid_top, x, y_grid_bottom), fill=(200,200,200), width=2)
                    if val not in (1, 2, 4, 3):
                        draw_textbox_center(draw, x, y_grid_bottom+5, str(int(val)), font)
                else:
                    if val not in (9.25, 9.75, 10.25, 10.75):
                        draw.line((x, y_grid_top + 10, x, y_grid_bottom - 15), fill=(180,180,180), width=1)

            y_grid_top = 195 + offset_y_w
            y_grid_bottom = 420 + offset_y_w
            for val in all_scale:
                x = value_to_x_custom(val)
                if int(val) == val:
                    if val in(1, 0): continue
                    if val in (1, 2, 3, 4):
                        draw.line((x, y_grid_top + 5, x, y_grid_bottom - 10), fill=(200,200,200), width=2)
                    else:
                        draw.line((x, y_grid_top, x, y_grid_bottom), fill=(200,200,200), width=2)
                    if val not in (1, 2, 4, 3):
                        draw_textbox_center(draw, x, y_grid_bottom+5, str(int(val)), font)
                else:
                    if val not in (9.25, 9.75, 10.25, 10.75):
                        draw.line((x, y_grid_top + 10, x, y_grid_bottom - 15), fill=(180,180,180), width=1)

            y_grid_top = 465 + offset_y_w
            y_grid_bottom = 600 + offset_y_w
            for val in all_scale:
                x = value_to_x_custom(val)
                if int(val) == val:
                    if val in(1, 0): continue
                    if val in (1, 2, 3, 4):
                        draw.line((x, y_grid_top + 5, x, y_grid_bottom - 10), fill=(200,200,200), width=2)
                    else:
                        draw.line((x, y_grid_top, x, y_grid_bottom), fill=(200,200,200), width=2)
                    # if val not in (1, 2, 4, 3):
                        # draw_textbox_center(draw, x, y_grid_bottom+5, str(int(val)), font)
                else:
                    if val not in (9.25, 9.75, 10.25, 10.75):
                        draw.line((x, y_grid_top + 10, x, y_grid_bottom - 15), fill=(180,180,180), width=1)


            bar_offset_y = 20 + offset_y_w
            val = cs_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = cs_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = cs_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = cs_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)

            bar_offset_y = 205 + offset_y_w
            val = ar_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = ar_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = ar_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = ar_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)

            bar_offset_y = 305 + offset_y_w
            val = od_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = od_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = od_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = od_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)

            bar_offset_y = 485 + offset_y_w
            val = hp_values[0]
            y = bar_offset_y + 20
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[0], width=20)

            val = hp_values[2]
            y = bar_offset_y + 40
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[2], width=20)

            val = hp_values[3]
            y = bar_offset_y + 60
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[3], width=20)

            val = hp_values[4]
            y = bar_offset_y + 80
            bar_len = value_to_x_custom(val) - x1
            draw.line((x1, y, x1 + bar_len, y), fill=fill_colors[4], width=20)


            text_x, text_y, text_b = 797, 172, 43
            draw_textbox_center(draw, text_x, text_y, "| CS", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{cs_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_y, text_b =  356, 43
            draw_textbox_center(draw, text_x, text_y, "| AR", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{ar_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_y, text_b =  458, 43
            draw_textbox_center(draw, text_x, text_y, "| OD", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{od_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_y, text_b =  637, 43
            draw_textbox_center(draw, text_x, text_y, "| HP", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{hp_values[0]:.1f}"), font_black_small, fill_text=fill_colors[0])

            text_x, text_y, text_b = 776, 295, 43
            draw_textbox_center(draw, text_x, text_y, "NM", font_bold_med)
            text_x, text_y, text_b = 820, 295, 43
            draw_textbox_center(draw, text_x, text_y, "HR", font_bold_med, fill_text=fill_colors[2])

            text_x, text_y, text_b = 769, 577, 43
            draw_textbox_center(draw, text_x, text_y, "DT", font_bold_med, fill_text=fill_colors[3])
            text_x, text_y, text_b = 820, 577, 43
            draw_textbox_center(draw, text_x, text_y, "DTHR", font_bold_med, fill_text=fill_colors[4])




            bars = [
                {"left": 100, "value": aim_data},
                {"left": 310, "value": acc_data},
                {"left": 520, "value": speed_data}
            ]

            bar_width = 160
            bar_y0 = 578
            bar_height = 14
            bar_y1 = bar_y0 + bar_height
            radius = bar_height  

            for bar in bars:
                bar_left = bar["left"]
                bar_right = bar_left + bar_width
                
                draw.line(
                    (bar_left, bar_y0 + bar_height // 2, bar_right, bar_y0 + bar_height // 2),
                    fill="white", width=2
                )

                fill_len = int(bar_width * bar["value"])
                if fill_len > 0:
                    draw.rounded_rectangle(
                        [bar_left, bar_y0, bar_left + fill_len, bar_y1],
                        radius=radius,
                        fill="white"
                    )


            text_x, text_y, text_b = 180, 525, 75
            draw_textbox_center(draw, text_x, text_y, "| AIM", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{aim_raw:.0f}"), font_black_small, fill_text=fill_colors[0])

            text_x = 390
            draw_textbox_center(draw, text_x, text_y, "| ACC", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{acc_raw:.0f}"), font_black_small, fill_text=fill_colors[0])

            text_x = 604
            draw_textbox_center(draw, text_x, text_y, "| SPEED", font_italic_small)
            draw_textbox_center(draw, text_x, text_y + text_b, str(f"{speed_raw:.0f}"), font_black_small, fill_text=fill_colors[0])


            spacing_y = 55
            base_x, base_y = 470, 136

            def draw_emoji_text(draw, x, y, emoji, text, emoji_font, text_font, text_fill):
                bbox = emoji_font.getbbox(emoji)
                emoji_width = bbox[2] - bbox[0]

                draw.text((x, y), emoji, font=emoji_font, fill="white", anchor="lm")  # anchor чтобы центрировать по Y
                draw.text((x + emoji_width + 8, y), text, font=text_font, fill=text_fill, anchor="lm")

            draw_emoji_text(draw, base_x, base_y + spacing_y, "▶️", str(plays), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, base_x, base_y + spacing_y*2, "💖", str(favs), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, base_x, base_y + spacing_y*3, "⏰", (str(length) + max_combo_map), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, base_x, base_y + spacing_y*4, "🥁", str(bpm_map), font_noto, font_regular_nano, fill_colors[0])

            draw.line((480, 395, 690, 395), fill=(200,200,200), width=2)

            asset = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/circle.png").convert("RGBA")

            base_width = 35
            block_right = 680

            w_percent = base_width / float(asset.size[0])
            new_height = int(float(asset.size[1]) * w_percent)

            asset = asset.resize((base_width, new_height), Image.LANCZOS)
            img.paste(asset, (497, 410), asset)

            text = str(circles)
            text_bbox = draw.textbbox((0,0), text, font=font_bold_med_3)
            text_width = text_bbox[2] - text_bbox[0]

            draw.text((block_right - text_width, 410), text, font=font_bold_med_3, fill="white")


            asset = Image.open(f"{BOT_DIR}/cards/assets/beatmaps/slider.png").convert("RGBA")

            base_width = 50
            w_percent = base_width / float(asset.size[0])
            new_height = int(float(asset.size[1]) * w_percent)

            asset = asset.resize((base_width, new_height), Image.LANCZOS)
            img.paste(asset, (490, 460), asset)

            text = str(sliders)
            text_bbox = draw.textbbox((0,0), text, font=font_bold_med_3)
            text_width = text_bbox[2] - text_bbox[0]

            draw.text((block_right - text_width, 460), text, font=font_bold_med_3, fill="white")

            
            line_y = 270
            draw.line((100, line_y, 412, line_y), fill=(150,150,150), width=2)

            draw.text((100, 280), f"last update: {format_osu_date(updated, False)}", font=font_regular_nano, fill=(150,150,150))
            # draw_emoji_text(draw, 100, 340, "👤", str(" "), font_noto, font_regular_nano, fill_colors[0])
            draw.text((100, 320), str(mapper), font=font_bold_med_4, fill="white")
            line_y = 370
            draw.line((100, line_y, 412, line_y), fill=(200,200,200), width=2)


            draw_emoji_text(draw, 100, 405, "⭐️", str(f"{stars:.2f}"), font_noto, font_regular_nano, fill_colors[0])
            draw_emoji_text(draw, 100, 465, "📊", status.capitalize(), font_noto, font_regular_nano, fill_colors[0])

            draw_emoji_text(draw, 250, 405, "💯", str(f"{max_pp:.1f}pp"), font_noto, font_regular_nano, fill_colors[0])
            

            # Подвал
            bot_first, bot_second = "Fujiyaosu", "Bot"
            today = date.today().isoformat()
            draw.text((128, 729), bot_first, font=font_black_small_2, fill="white")
            bbox = draw.textbbox((0, 0), bot_first, font=font_black_small_2)
            text_width = bbox[2] - bbox[0]
            draw.text((128+text_width, 729), bot_second, font=font_thin_small, fill="white")

            draw.text((428, 729), today, font=font_light_italic_big, fill="white")

            mode = "Standard"
            asset = Image.open(f"{BOT_DIR}/cards/assets/gamemodes/{mode}.png").convert("RGBA")
            asset = asset.resize((70,70))
            img.paste(asset, (1315, 15), asset)

            asset = Image.open(f"{BOT_DIR}/cards/assets/branding/icon.png").convert("RGBA")
            asset = asset.resize((110,110))
            img.paste(asset, (0, 690), asset)

            block_left = 32
            block_right = 1300 
            max_width = block_right - block_left


            words = title.split()

            def wrap_text(words, font, max_width, draw):
                lines = []
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    line_width = draw.textlength(test_line, font=font)
                    if line_width <= max_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                return lines

            lines = wrap_text(words, font_black_big, max_width, draw)

            if len(lines) == 1:
                title_y = 23
                font_text = font_black_big
            else:
                lines = wrap_text(words, font_black_big_2, max_width, draw)
                lines = lines[:2]
                title_y = 15
                font_text = font_black_big_2

            title_multiline = "\n".join(lines)
            draw.text((block_left, title_y), title_multiline, font=font_text, fill=(255, 255, 255), spacing=14)

            bg = Image.open(bg_path).convert("RGBA").resize((380, 106))
            img.paste(bg, (67, 148), bg)

            img_path = f'{BOT_DIR}/cache/{beatmap_id}.png'
            img.convert("RGB").save(img_path) 

            with open(img_path, "rb") as f:
                try:
                    await message.reply_photo(
                        InputFile(f),
                    )
                except:
                    await message.reply_photo(
                        InputFile(f),
                    )
                if user_request:
                    try:
                        
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
                    except:
                        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
                try:
                    os.remove(img_path)
                except: return 
                return
  
        except Exception as e: print(e)   

