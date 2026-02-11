


# from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# from ....external.osu_http import beatmap
# from ....external.localapi import get_map_stats_neko_api
# from .image_utils import create_stat_button_left, create_stat_button_right, draw_text_with_shadow
# from .utils import format_length, iso_to_DaysMonthYear, stars_to_prop, trim_text
# from .fetch import fetch_cover

# from ....systems.translations import CARD_BEATMAP as T
# from config import BOT_DIR, BG_LIST_DIR, BG_CARD_DIR

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

# from ....external.osu_http import beatmap
# from ....external.localapi import get_map_stats_neko_api
from image_utils import create_stat_button_left, draw_text_with_shadow, add_rounded_corners, draw_multiline_text_with_shadow, create_stat_button_right
from utils import iso_to_DaysMonthYear
from fetch import fetch_cover

from translations import CARD_GUESS as T
BOT_DIR = "E:/fa/nekoscience/bot/src"

BG_SCORE_COMPARE_DIR = f"{BOT_DIR}/cache/card_score_compare"

async def create_score_compare_image(scores: list[dict], hide_values = None, language = 'ru'):
    l = language
    row_height = 500
    img_w = 1000
    img_h = row_height * len(scores)
    corner_radius = 30
    default_key = 50
    default_btn_color = (default_key, default_key, default_key, 1)

    img = Image.new("RGBA", (img_w, img_h), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)

    f1 = "cards/assets/fonts/PlaypenSans"
    s1, s2, _, _, _, _, _, _ = "ExtraBold", "Bold", "SemiBold", "Medium", "Regular", "Light", "ExtraLight", "Thin"

    font_extra_big = ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 50)
    font_medium_big = ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 42)
    font_big = ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 30)
    font_small = ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 20)

    darkness_amount = 0.8
    bg_blur_amount = 20
    line_color = (80, 80, 80)

    gap = 25

    for i, cached_entry in enumerate(scores):
        y_base = i * row_height        

        map_data = cached_entry["map"]
        osu_score = cached_entry["osu_score"]
        osu_api_data = cached_entry["osu_api_data"]
        lazer_data = cached_entry["lazer_data"]
        user = cached_entry["user"]
        state = cached_entry["state"]

        if not cached_entry['state']['calculated']:
            await caclulte_cached_entry(cached_entry)
            
        neko_api_calc = cached_entry['neko_api_calc']
        state =         cached_entry['state']

        lazer = state.get('lazer')
        beatmap_id = map_data["beatmap_id"]
        uid = osu_score["user_id"]

        try:
            values = await calculate_beatmap_attr(cached_entry)            

            bpm = (map_data.get("bpm", 0.0))
            length = (map_data.get("hit_length", 0))                    
            mods_str = osu_score.get("mods", "")
            speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)                    
            length = int(round(float(length) / speed_multiplier))
            
            bpm, values0, values2, values1, values3 = apply_mods_to_stats(
                bpm, values[0], values[2], values[1], values[3],
                speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
            )

            values = {'hp': values3, 'cs': values1, 'od': values2, 'ar': values0}
        except:
            values = {'hp': 10.33, 'cs': 10.33, 'od': 10.33, 'ar': 10.33}
            bpm = 333.001
                              
        
        #temp pp fix
        pp = neko_api_calc.get('pp') 
        pp = pp if not isinstance(osu_score.get("pp"), (int, float)) or osu_score.get("pp") <= 0 else osu_score.get("pp")
        stars = neko_api_calc.get('star_rating', 0)

        user_avatar = await fetch_cover(
            user["avatar_url"],
            f"{uid}a",
            BG_SCORE_COMPARE_DIR,
            thumb_size=(250, 250),
            radius=corner_radius
        )

        user_cover = await fetch_cover(
            user["cover_url"],
            f"{uid}c",
            BG_SCORE_COMPARE_DIR,
            thumb_size=(img_w, row_height),
            radius=0
        )

        map_cover = await fetch_cover(
            map_data["card2x_url"],
            f"{beatmap_id}c",
            BG_SCORE_COMPARE_DIR,
            thumb_size=(800, 280),
            radius=0
        )


        target_size = (img_w, row_height + 0)
        asset = Image.open(user_cover).convert("RGBA")
        asset = ImageOps.fit(asset, target_size, Image.LANCZOS)
        asset = asset.filter(ImageFilter.GaussianBlur(bg_blur_amount))
        asset = ImageEnhance.Brightness(asset).enhance(darkness_amount)

        img.paste(asset, (0, y_base), asset)      


        target_size = (int(img_w*0.9), int(row_height / 3))
        asset = Image.open(map_cover).convert("RGBA")
        asset = ImageOps.fit(asset, target_size, Image.LANCZOS)
        asset = asset.filter(ImageFilter.GaussianBlur(bg_blur_amount))
        asset = ImageEnhance.Brightness(asset).enhance(darkness_amount)
        asset = add_rounded_corners(asset, corner_radius)

        img.paste(asset, (0 + gap*2, y_base + 280), asset)


        target_size = (int(img_w*0.25), int(row_height / 6))
        asset = Image.open(map_cover).convert("RGBA")
        asset = ImageOps.fit(asset, target_size, Image.LANCZOS)
        asset = ImageEnhance.Brightness(asset).enhance(darkness_amount)
        asset = add_rounded_corners(asset, corner_radius, skip_corners=["tl", "br"])

        img.paste(asset, (gap*2, y_base + 280 + int(row_height / 6)), asset)


        if i != 0:
            draw.line((0, y_base, img_w, y_base), (line_color), 4)

        resize = int(row_height * 0.55 - gap * 2)
        ava = Image.open(user_avatar).convert("RGBA").resize((resize, resize))
        img.paste(ava, (gap*2, y_base + gap), ava)

        x_left = 300        

        lazer = state.get('lazer')
        username_text = user.get('username', f'Unnamed player {i+1}')        
        timestamp_text = iso_to_DaysMonthYear(osu_api_data.get('date', f'???'), l)
        map_text = map_data.get('beatmap_full', f'Unnamed map {i+1}')
        if lazer: 
            is_stable_client = ""
        else:
            is_stable_client = "(Stable)"   
        mods_text = f"+{osu_score.get('mods', 'NM')}{is_stable_client}"
               
        draw_text_with_shadow(draw, 
            (x_left, y_base + 26), 
            username_text, 
            font_medium_big,
            (255, 255, 255), 
            (10, 10, 10), 2)        
        
        bbox1 = draw.textbbox((0, 0), username_text, font=font_medium_big)        
        draw_text_with_shadow(draw, 
            (x_left + 16 + (bbox1[2] - bbox1[0]), y_base + 36), 
            timestamp_text, 
            font_small,
            (200, 200, 200), 
            (10, 10, 10), 1)  
        
        mods_width, _height = draw_multiline_text_with_shadow(
            draw,
            pos=(img_w - gap*3, y_base + 290),
            text=mods_text,
            font=font_big,
            fill=(255,255,255),
            shadowcolor=(0,0,0),
            align='right',
            max_width=500,            
            max_lines=1
        )
        
        draw_multiline_text_with_shadow(
            draw,
            pos=(gap*3, y_base + 290),
            text=map_text,
            font=font_small,
            fill=(255,255,255),
            shadowcolor=(0,0,0),
            shadow_offset=0,
            max_width=img_w - int(mods_width) - gap*6,
            max_lines=2,
            font_big=font_big
        )

        x_right = img_w + gap - gap *3 + 10
        y_top = y_base + 344
        gap_map = -46

        cs, hp = f"{T.get('CS')[l]}", f"{T.get('HP')[l]}"
        od, ar = f"{T.get('OD')[l]}", f"{T.get('AR')[l]}"
        bpm_prop =  f"{T.get('BPM')[l]}"
        
        map_args = {
            "btn_h":70, 
            "btn_min_w":10, 
            "letter_fisrst_pad_y":0,
            "letter_second_pad_y":40,
            "overlay_transparency":0,
            "font_text":font_big, 
            "font_prop":font_small,
            "btn_text_shadow_offset":0
        }
        x_left_map = create_stat_button_right(
            img, draw, x_right, y_top,
            btn_h=60, btn_min_w=0,
            text=f"{stars:0.2f}*",                                    
            letter_fisrst_pad_y = -25,
            prop='', overlay_transparency=0,
            font_text=font_extra_big, font_prop=font_big)

        x_left2_map = create_stat_button_right(
            img, draw, x_left_map - gap_map, y_top,           
            text=str(values.get("ar")), prop=ar,
            **map_args
        )
        
        x_left3_map = create_stat_button_right(
            img, draw, x_left2_map - gap_map, y_top,            
            text=str(values.get("od")), prop=od,
            **map_args
        )
        
        x_left4_map = create_stat_button_right(
            img, draw, x_left3_map - gap_map, y_top,                                 
            text=str(values.get("hp")), prop=hp,
            **map_args
        )
        
        x_left5_map = create_stat_button_right(
            img, draw, x_left4_map - gap_map, y_top,                                
            text=str(values.get("cs")), prop=cs,
            **map_args
        )

        _x_left6_map = create_stat_button_right(
            img, draw, x_left5_map - gap_map, y_top,                                
            text=f"{bpm:.1f}", prop=bpm_prop,
            **map_args
        )

        status = map_data['status']
        try:
            status_text = f"{T.get(str(status))[l]}"    
            status_color = f"{T.get(str(status))['color']}"
        except:
            status_text = f"{T.get('unknown')[l]}"    
            status_color = f"{T.get('unknown')['color']}"
        status_color = tuple(map(int, status_color.strip("()").split(",")))

        base_y = y_base + 90

        overlay_x, overlay_y = img_w - gap, base_y + 380
        asset_transparency = 185

        bbox = draw.textbbox((0, 0), status_text, font_small)

        letter_pad = 40
        btn_w, btn_h = letter_pad + (bbox[2] - bbox[0]), 50 

        btn_x, btn_y = overlay_x - btn_w, overlay_y - btn_h
        btn = Image.new("RGBA", (btn_w, btn_h), (status_color[0],status_color[1],status_color[2], asset_transparency))

        btn_mask = Image.new("L", (btn_w, btn_h), 0)
        mask_draw = ImageDraw.Draw(btn_mask)
        mask_draw.rounded_rectangle(
            (0, 0, btn_w, btn_h),
            radius=btn_h/2,
            fill=asset_transparency
        )
            
        img.paste(btn, (btn_x, btn_y), btn_mask)

        btn_text_pos = (btn_x + letter_pad/2, btn_y + 8)

        btn_text_color = (255, 255, 255, 255)
        btn_text_shadow_color = (100, 100, 100, 255)
        btn_text_shadow_offset = 2

        draw_text_with_shadow(draw, btn_text_pos, status_text, font_small, 
            btn_text_color, 
            btn_text_shadow_color, 
            btn_text_shadow_offset)  
        


        rank_text = f"{T.get('Rank')[l]}"
        accuracy_text = f"{T.get('Accuracy')[l]}"
        combo_text = f"{T.get('Combo')[l]}"

        miss = str(osu_score.get("count_miss") or 0)
        sb = str(osu_score.get("count_miss") or 0)
        sb_text = ''
        
        # if sb != 0:
        #     sb_text = f" +{sb}sb"    

        miss_count = f"{miss}{sb_text}"

        pp_text = 'PP'
        great_text = '300'
        ok_text = '100'
        meh_text = '50'
        miss_text = 'X'
        great_text = ''
        ok_text = ''
        meh_text = ''
        miss_text = ''

        count_miss = osu_score.get("count_miss") or 0
        count_300 = osu_score.get("count_300") or 0
        count_100 = osu_score.get("count_100") or 0
        count_50 = osu_score.get("count_50") or 0

        inactive = default_btn_color

        def pick(key, color):
            # return color if (osu_score.get(key) or 0) > 0 else inactive
            return color if (osu_score.get(key) or 0) > 0 else color

        count_300_color  = pick("count_300",  (55, 120, 255, 1))
        count_100_color  = pick("count_100",  (50, 255, 50, 1))
        count_50_color   = pick("count_50",   (255, 255, 50, 1))
        count_miss_color = pick("count_miss", (255, 50, 50, 1))

        pp = f"{pp:.2f}"

        if hide_values is not None:
            if 'pp' in hide_values:
                pp = '?'

        btn_h1, btn_h2 = 50, 46
        fisrst_pad1, second_pad1 = -10, 50
        fisrst_pad2, second_pad2 = 0, 46
        
        base_y += 20
        row_step = 90
        stat_gap = 8
        alpha1, alpha2 = 100, 100

        rows = [
            [   
                (
                    f"{lazer_data.get('rank', '?')}", 
                    rank_text, 
                    default_btn_color, 
                    alpha1, 
                    font_medium_big,
                    btn_h1,
                    fisrst_pad1, second_pad1,
                ),             
                (
                    f"{(osu_score.get('accuracy') or 0)*100:.2f}%",
                    accuracy_text, 
                    default_btn_color, 
                    alpha1, 
                    font_medium_big,
                    btn_h1,
                    fisrst_pad1, second_pad1,
                ),
                (
                    f"{osu_score.get('max_combo') or 0}x", 
                    combo_text, 
                    default_btn_color, 
                    alpha1, 
                    font_medium_big,
                    btn_h1,
                    fisrst_pad1, second_pad1,
                ),
                (
                    pp, 
                    pp_text, 
                    default_btn_color, 
                    alpha1, 
                    font_medium_big,
                    btn_h1,
                    fisrst_pad1, second_pad1,
                ),
            ],
            [
                (
                    count_300, 
                    great_text, 
                    count_300_color, 
                    alpha2, 
                    font_big,
                    btn_h2,
                    fisrst_pad2, second_pad2,
                ),
                (
                    count_100, 
                    ok_text, 
                    count_100_color, 
                    alpha2, 
                    font_big,
                    btn_h2,
                    fisrst_pad2, second_pad2,
                ),
                (
                    count_50, 
                    meh_text, 
                    count_50_color, 
                    alpha2, 
                    font_big,
                    btn_h2,
                    fisrst_pad2, second_pad2,
                ),
                (
                    miss_count, 
                    miss_text, 
                    count_miss_color, 
                    alpha2, 
                    font_big,
                    btn_h2,
                    fisrst_pad2, second_pad2,
                ),
            ],            
        ]

        for row_index, row in enumerate(rows):
            y = base_y + row_index * row_step
            x = x_left

            for value, label, color, alpha, font1, btn_h, fisrst_pad, second_pad in row:
                x = create_stat_button_left(
                    img, draw, x, y,
                    text=str(value),
                    prop=label,
                    letter_pad=38,
                    overlay_transparency=alpha,
                    overlay_color=color,
                    font_text=font1,
                    font_prop=font_small,
                    btn_text_shadow_offset=2,
                    btn_h=btn_h,                    
                    letter_fisrst_pad_y=fisrst_pad,
                    letter_second_pad_y=second_pad,
                ) + stat_gap
    
    for i, cached_entry in enumerate(scores):
        y_base = i * row_height

        if i+1 != len(scores):
            create_stat_button_left(
                img, draw, int(img_w/2) - 42, y_base + int(img_h/len(scores)) - 23,
                text='VS',
                prop='',
                overlay_transparency=255,
                overlay_color=line_color,
                font_text=font_big,
                font_prop=font_small,
            ) + stat_gap


    img_path = f"{BOT_DIR}/cache/compare_1.png"
    img.convert("RGB").save(img_path)

    return img_path
import asyncio

score1_data={
    "user": {
        "username": "Fujiya",
        "total_pp": 7376.3,
        "country_rank": 2556,
        "global_rank": 27670,
        "country_code": "RU",
        "total_pp_cache": None,
        "avatar_url": "https://a.ppy.sh/11596989?1752685709.png",
        "cover_url": "https://assets.ppy.sh/user-profile-covers/11596989/a7db9837872a1828665ab0c92803df78ac5c8d43cc1b67304087320d59b7d439.png"
    },
    "map": {
        "card2x_url": "https://assets.ppy.sh/beatmaps/1143817/covers/card@2x.jpg?1641124856",
        "beatmap_full": "Zekk - Duplication [Parallelism]",
        "mapper": "Molang",
        "beatmap_id": 2395150,
        "status": "graveyard",
        "bpm": 202,
        "url": "https://osu.ppy.sh/beatmaps/2395150",
        "hit_length": 135,
        "cs": 4,
        "ar": 9.6,
        "od": 9,
        "hp": 4.4
    },
    "osu_api_data": {
        "rank_legacy": "A",
        "date": "2026-01-17T17:17:46Z",
        "id": 6072717533,
        "best_id": None
    },
    "osu_score": {
        "user_id": 11596989,
        "score_legacy": 0,
        "mods": "DT(1.1x)",
        "accuracy": 0.9318365695792881,
        "max_combo": 246,
        "pp": 0,
        "count_300": 758,
        "count_100": 29,
        "count_50": 1,
        "count_miss": 36,
        "ignore_hit": 410,
        "ignore_miss": 125,
        "small_bonus": 4,
        "large_tick_hit": 52,
        "large_tick_miss": 1,
        "slider_tail_hit": 339,
        "failed": False,
        "try_count": 1
    },
    "neko_api_calc": {
        "pp": 93.79572634180653,
        "no_choke_pp": 162.32436597042934,
        "perfect_pp": 440.146357333443,
        "star_rating": 6.695425159091508,
        "perfect_combo": 1313,
        "expected_bpm": 201.99979800020202
    },
    "lazer_data": {
        "ranked": False,
        "total_score": 41772,
        "rank": "B",
        "speed_multiplier": 1.1,
        "DA_values": {}
    },
    "state": {
        "lazer": True,
        "mode": "osu",
        "calculated": True,
        "ready": True,
        "error": False
    } 
}
score2_data={
  "user": {
    "username": "Fujiya",
    "total_pp": 7376.63,
    "country_rank": 2611,
    "global_rank": 28075,
    "country_code": "RU",
    "total_pp_cache": None,
    "avatar_url": "https://a.ppy.sh/11596989?1752685709.png",
    "cover_url": "https://assets.ppy.sh/user-profile-covers/11596989/a7db9837872a1828665ab0c92803df78ac5c8d43cc1b67304087320d59b7d439.png"
  },
  "map": {
    "card2x_url": "https://assets.ppy.sh/beatmaps/117269/covers/card@2x.jpg?1650619047",
    "beatmap_full": "Jeff Williams - This Will Be the Day (feat. Casey Lee Williams) [Insane]",
    "mapper": "ampzz",
    "beatmap_id": 302238,
    "status": "ranked",
    "bpm": 190,
    "url": "https://osu.ppy.sh/beatmaps/302238",
    "hit_length": 177,
    "cs": 4,
    "ar": 9,
    "od": 9,
    "hp": 9
  },
  "osu_api_data": {
    "rank_legacy": "A",
    "date": "2026-02-10T16:05:20Z",
    "id": 6198487683,
    "best_id": None
  },
  "osu_score": {
    "user_id": 11596989,
    "score_legacy": 0,
    "score_lazer": 0,
    "mods": "DT+RX",
    "accuracy": 0.974265,
    "max_combo": 508,
    "pp": 0,
    "count_300": 660,
    "count_100": 28,
    "count_50": None,
    "count_miss": 3,
    "ignore_hit": 293,
    "ignore_miss": 10,
    "small_bonus": 17,
    "large_tick_hit": 120,
    "large_tick_miss": 2,
    "slider_tail_hit": 293,
    "failed": False,
    "try_count": 7
  },
  "neko_api_calc": {
    "pp": 89.3278745594294,
    "no_choke_pp": 100.53410503020208,
    "perfect_pp": 167.29830362580375,
    "star_rating": 5.512670785590803,
    "perfect_combo": 1106,
    "expected_bpm": 190.0002850004275
  },
  "lazer_data": {
    "ranked": None,
    "total_score": 0,
    "rank": "A",
    "speed_multiplier": None,
    "DA_values": {}
  },
  "osu_statistics_max": {
    "great": 691,
    "ignore_hit": 293,
    "large_tick_hit": 122,
    "slider_tail_hit": 293
  },
  "state": {
    "lazer": True,
    "mode": "osu",
    "calculated": True,
    "ready": True,
    "error": False
  },
  "meta": {
    "created_at": "2026-02-11T00:48:18.251835",
    "calculated_at": "2026-02-11T00:48:19.505198",
    "version": "03022026"
  }
}
score3_data={
  "user": {
    "username": "lironick",
    "total_pp": 5754.8,
    "country_rank": 6439,
    "global_rank": 67224,
    "country_code": "RU",
    "total_pp_cache": None,
    "avatar_url": "https://a.ppy.sh/26197609?1770299156.jpeg",
    "cover_url": "https://assets.ppy.sh/user-profile-covers/26197609/49ffde9a3e986da938d11bd29e2a7ab7a2c8705cf14a9c158ae5a1c5cfb55f90.png"
  },
  "map": {
    "card2x_url": "https://assets.ppy.sh/beatmaps/384772/covers/card@2x.jpg?1650716263",
    "beatmap_full": "Yuaru - Asu no Yozora Shoukaihan [Insane]",
    "mapper": "Akitoshi",
    "beatmap_id": 853926,
    "status": "ranked",
    "bpm": 185,
    "url": "https://osu.ppy.sh/beatmaps/853926",
    "hit_length": 159,
    "cs": 4,
    "ar": 9,
    "od": 7,
    "hp": 6
  },
  "osu_api_data": {
    "rank_legacy": "A",
    "date": "2025-11-03T09:41:52Z",
    "id": 5693830786,
    "best_id": None
  },
  "osu_score": {
    "user_id": 26197609,
    "score_legacy": 8809241,
    "score_lazer": 0,
    "mods": "DT+CL",
    "accuracy": 0.960072,
    "max_combo": 392,
    "pp": 228.583,
    "count_300": 609,
    "count_100": 36,
    "count_50": 1,
    "count_miss": 1,
    "ignore_hit": None,
    "ignore_miss": None,
    "small_bonus": None,
    "large_tick_hit": None,
    "large_tick_miss": None,
    "slider_tail_hit": None,
    "failed": False,
    "try_count": 1
  },
  "neko_api_calc": {
    "pp": 262.9123379655913,
    "no_choke_pp": 336.1798530481123,
    "perfect_pp": 457.72381997069016,
    "star_rating": 7.147648706194119,
    "perfect_combo": 1133,
    "expected_bpm": 185.00018500018498
  },
  "lazer_data": {
    "ranked": None,
    "total_score": 641414,
    "rank": "A",
    "speed_multiplier": None,
    "DA_values": {}
  },
  "osu_statistics_max": {
    "great": 647,
    "ignore_hit": 0,
    "large_tick_hit": 0,
    "slider_tail_hit": 0
  },
  "state": {
    "lazer": False,
    "mode": "osu",
    "calculated": True,
    "ready": True,
    "error": False
  },
  "meta": {
    "created_at": "2026-02-11T14:46:01.978155",
    "calculated_at": "2026-02-11T14:46:04.054638",
    "version": "03022026"
  }
}

scores = []
# scores.append(score1_data)
scores.append(score2_data)
scores.append(score3_data)

print(asyncio.run(create_score_compare_image(
    scores, 
    hide_values=('pp'),
    language='en'
)))
