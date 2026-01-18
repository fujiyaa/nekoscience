


# from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# from ....external.osu_http import beatmap
# from ....external.localapi import get_map_stats_neko_api
# from .image_utils import create_stat_button_left, create_stat_button_right, draw_text_with_shadow
# from .utils import format_length, iso_to_DaysMonthYear, stars_to_prop, trim_text
# from .fetch import fetch_cover

# from ....systems.translations import CARD_BEATMAP as T
# from config import BOT_DIR, BG_LIST_DIR, BG_CARD_DIR

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# from ....external.osu_http import beatmap
# from ....external.localapi import get_map_stats_neko_api
from image_utils import create_stat_button_left, create_stat_button_right, draw_text_with_shadow
from utils import format_length, iso_to_DaysMonthYear, stars_to_prop, trim_text
from fetch import fetch_cover

from translations import CARD_BEATMAP as T
BOT_DIR = "E:/fa/nekoscience/bot/src"

BG_SCORE_COMPARE_DIR = f"{BOT_DIR}/cache/card_score_compare"

async def create_score_compare_image(score1_data: dict, score2_data: dict):   
    # l = map_data['lang']

    map = score1_data.get('map')
    osu_score1 = score1_data.get('osu_score')
    osu_score2 = score2_data.get('osu_score')
    user1 = score1_data.get('user')
    user2 = score2_data.get('user')

    beatmap_id = map.get('beatmap_id')

    img_w, img_h = 800, 300
    corner_radius = 40

    id1, id2 = osu_score1['user_id'], osu_score2['user_id']

    avatar_exact = (250, 250)
    cover_resize = (img_w/2, img_h/4)    

    user1_avatar = await fetch_cover(user1.get('avatar_url'), f"{beatmap_id}{id1}", BG_SCORE_COMPARE_DIR, thumb_size = avatar_exact, radius = corner_radius)    
    user2_avatar = await fetch_cover(user2.get('avatar_url'), f"{beatmap_id}{id2}", BG_SCORE_COMPARE_DIR, thumb_size = avatar_exact, radius = corner_radius)

    user1_cover = await fetch_cover(user1.get('cover_url'), f"{id1}{beatmap_id}", BG_SCORE_COMPARE_DIR, thumb_size = cover_resize, radius = 0)    
    user2_cover = await fetch_cover(user2.get('cover_url'), f"{id2}{beatmap_id}", BG_SCORE_COMPARE_DIR, thumb_size = cover_resize, radius = 0)




    try:
        f1 = "cards/assets/fonts/PlaypenSans"
        s1, s2, s3, s4, _s5, s6, _s7, _s8 = "ExtraBold", "Bold", "SemiBold", "Medium", "Regular", "Light", "ExtraLight", "Thin"        

        font_test1 =            ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 70)
        font_test2 =           ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 20)
        font_test3 =           ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 30)

        font_title =            ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 62)
        font_guest_mapper =     ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 36)

        font_version =          ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 46)
        font_title_overlay =    ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 42)
        font_artist =           ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 32)

        info_size = 32
        info_left, info_right = s6, s3

        font_submitted2 =       ImageFont.truetype(f"{BOT_DIR}/{f1}-{info_right}.ttf", info_size)        
        font_updated2 =         ImageFont.truetype(f"{BOT_DIR}/{f1}-{info_right}.ttf", info_size)
        font_mapper2 =          ImageFont.truetype(f"{BOT_DIR}/{f1}-{info_right}.ttf", info_size)

        font_submitted1 =       ImageFont.truetype(f"{BOT_DIR}/{f1}-{info_left}.ttf", info_size)        
        font_updated1 =         ImageFont.truetype(f"{BOT_DIR}/{f1}-{info_left}.ttf", info_size)                
        font_mapper1 =          ImageFont.truetype(f"{BOT_DIR}/{f1}-{info_left}.ttf", info_size)

        font_status_btn =       ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 42)
        font_prop1 =            ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 60)
        font_prop2 =            ImageFont.truetype(f"{BOT_DIR}/{f1}-{s6}.ttf", 36)
        font_prop3 =            ImageFont.truetype(f"{BOT_DIR}/{f1}-{s4}.ttf", 50)
        font_prop4 =            ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 42)
        font_skill1 =           ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 40)
        font_skill2 =           ImageFont.truetype(f"{BOT_DIR}/{f1}-{s6}.ttf", 30)

    except IOError:
        font_name = ImageFont.load_default()
        # font_stats = ImageFont.load_default()
        # font_small = ImageFont.load_default()

    img = Image.new("RGBA", (img_w, img_h), (40, 40, 40, 255))

    # ?
    # main_y_offset = 20     
    # padding_to_border = 80

    # list_x, list_y, = padding_to_border, main_y_offset + padding_to_border + 120
    # list_h = 300 # const

    darkness_amount = 0.8
    bg_blur_amount = 20   



    # бг 1
    asset = Image.open(user1_cover).convert("RGBA").resize((img_w, int(img_h/2)))
    draw = ImageDraw.Draw(img)   

    asset = asset.filter(ImageFilter.GaussianBlur(bg_blur_amount))
    
    enhancer = ImageEnhance.Brightness(asset)    
    asset = enhancer.enhance(darkness_amount)    

    img.paste(asset, (0, 0), asset)


    # бг 2
    asset = Image.open(user2_cover).convert("RGBA").resize((img_w, int(img_h/2)))
    draw = ImageDraw.Draw(img)   

    asset = asset.filter(ImageFilter.GaussianBlur(bg_blur_amount))
    
    enhancer = ImageEnhance.Brightness(asset)    
    asset = enhancer.enhance(darkness_amount)    

    img.paste(asset, (0, int(img_h/2)), asset)

      
    # бг линия
    line_color_key = 200
    line_width = 2
    line_color = (line_color_key, line_color_key, line_color_key) 
    line_y = int(img_h/2)

    draw.line((0, line_y, img_w, line_y), line_color, line_width) 



    # аватар 1
    left_offset = 10
    y_offset = 0
    gap = 25
    x, y = gap + left_offset, gap - y_offset
    resize = int(img_h/2 - gap*2)

    asset = Image.open(user1_avatar).convert("RGBA").resize((resize, resize))   
    img.paste(asset, (x, y), asset)

    # аватар 2
    x, y = gap + left_offset, int(img_h/2) + gap - y_offset
    resize = int(img_h/2 - gap*2)

    asset = Image.open(user2_avatar).convert("RGBA").resize((resize, resize))
    img.paste(asset, (x, y), asset)


    x_left = 160
    y_top = 70
    gap = 10
    color_better = (50, 255, 50, 0)
    color_even = (50, 50, 50, 0)
    color_worse = (255, 50, 50, 0)

    score = create_stat_button_left(img, draw, x_left, y_top - 50,
                                    text=str(417722), prop="", 
                                    overlay_transparency=0, overlay_color=(color_better),
                                    font_text=font_test3, font_prop=font_test2)

    x_right1 = create_stat_button_left(img, draw, x_left, y_top,
                                    text=str(osu_score1.get('count_300', 0)), prop="Great", 
                                    overlay_transparency=200, overlay_color=(color_better),
                                    font_text=font_test3, font_prop=font_test2)
    
    x_right2 = create_stat_button_left(img, draw, x_right1 + gap, y_top,
                                    text=str(osu_score1.get('count_100', 0)), prop="Good", 
                                    overlay_transparency=200, overlay_color=(color_better),
                                    font_text=font_test3, font_prop=font_test2)
    
    x_right3 = create_stat_button_left(img, draw, x_right2 + gap, y_top,
                                    text=str(osu_score1.get('count_50', 0)), prop="Meh", 
                                    overlay_transparency=200, overlay_color=(color_even),
                                    font_text=font_test3, font_prop=font_test2)
    
    x_right4 = create_stat_button_left(img, draw, x_right3 + gap, y_top,                                       
                                    text=str(osu_score1.get('count_miss', 0)), prop="Miss", 
                                    overlay_transparency=200, overlay_color=(color_even),
                                    font_text=font_test3, font_prop=font_test2)
    
    x_right5 = create_stat_button_left(img, draw, x_right4 + gap, y_top,
                                    text=str(osu_score1.get('max_combo', 0)), prop="Combo", 
                                    overlay_transparency=200, overlay_color=(color_worse),
                                    font_text=font_test3, font_prop=font_test2)
    
    







    # !!!
    # bg = Image.open(f"{BOT_DIR}/cards/assets/top5/botname.png").convert("RGBA").resize((380, 106))
    # img.paste(bg, (img_w - 400, 60), bg)  

    img_path = f'{BOT_DIR}/cache/{beatmap_id}.png'
    img.convert("RGB").save(img_path)

    return img_path

import asyncio
print(asyncio.run(create_score_compare_image(
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
            "beatmap_full": "Zekk - Duplication [Styxwater's Absolute Parallelism]",
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
            "mods": "DT+RX (1.1x)",
            "accuracy_legacy": 0.9318365695792881,
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
            "accuracy": 0.899965,
            "rank": "B",
            "speed_multiplier": 1.1,
            "DA_values": {}
        },
        "state": {
            "lazer": True,
            "mode": "osu",
            "calculated": True,
            "enriched": True,
            "ready": True,
            "error": False
        } 
    },
    score2_data={
        "user": {
            "username": "Fujiya",
            "total_pp": 7376.3,
            "country_rank": 2557,
            "global_rank": 27682,
            "country_code": "RU",
            "total_pp_cache": None,
            "avatar_url": "https://a.ppy.sh/11596989?1752685709.png",
            "cover_url": "https://assets.ppy.sh/user-profile-covers/11596989/a7db9837872a1828665ab0c92803df78ac5c8d43cc1b67304087320d59b7d439.png"
        },
        "map": {
            "card2x_url": "https://assets.ppy.sh/beatmaps/1143817/covers/card@2x.jpg?1641124856",
            "beatmap_full": "Zekk - Duplication [Styxwater's Absolute Parallelism]",
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
            "rank_legacy": "B",
            "date": "2026-01-17T17:17:46Z",
            "id": 6072717533,
            "best_id": None
        },
        "osu_score": {
            "user_id": 1189,
            "score_legacy": 0,
            "mods": "DT+RX (1.1x)",
            "accuracy_legacy": 0.899965,
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
            "accuracy": 0.899965,
            "rank": "B",
            "speed_multiplier": 1.1,
            "DA_values": {}
        },
        "state": {
            "lazer": True,
            "mode": "osu",
            "calculated": True,
            "enriched": True,
            "ready": True,
            "error": False
        },
    }
)))
