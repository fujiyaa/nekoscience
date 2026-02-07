


from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

from .image_utils import create_stat_button_left, draw_text_with_shadow, add_rounded_corners, draw_multiline_text_with_shadow, create_stat_button_right
from .utils import iso_to_DaysMonthYear
from .fetch import fetch_cover
from ....utils.calculate import calculate_beatmap_attr
from ....external.localapi import get_map_stats_neko_api

from ....systems.translations import CARD_GUESS as T
from config import BOT_DIR, BG_SCORE_COMPARE_DIR



async def create_score_compare_image(scores: list[dict], hide_values = None, language = 'ru'):
    l = language
    row_height = 500
    img_w = 1000
    img_h = row_height * len(scores)
    corner_radius = 40

    img = Image.new("RGBA", (img_w, img_h), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)

    f1 = "cards/assets/fonts/PlaypenSans"
    s1, s2, _, _, _, _, _, _ = "ExtraBold", "Bold", "SemiBold", "Medium", "Regular", "Light", "ExtraLight", "Thin"

    font_extra_big = ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 50)
    font_big = ImageFont.truetype(f"{BOT_DIR}/{f1}-{s2}.ttf", 30)
    font_small = ImageFont.truetype(f"{BOT_DIR}/{f1}-{s1}.ttf", 20)

    darkness_amount = 0.8
    bg_blur_amount = 20
    line_color = (80, 80, 80)

    gap = 25
    left_offset = 20

    for i, data in enumerate(scores):
        y_base = i * row_height        

        map_data = data["map"]
        osu_score = data["osu_score"]
        osu_api_data = data["osu_api_data"]
        lazer_data = data["lazer_data"]
        user = data["user"]
        state = data["state"]

        lazer = state.get('lazer')
        beatmap_id = map_data["beatmap_id"]
        uid = osu_score["user_id"]

        try:
            values = await calculate_beatmap_attr(data)
            values = {'hp': values[3], 'cs': values[1], 'od': values[2], 'ar': values[0]}
        except:
            values = {'hp': 10.33, 'cs': 10.33, 'od': 10.33, 'ar': 10.33}
        
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
            # _choke = pp_data.get("no_choke_pp")
            # _max_pp = pp_data.get("perfect_pp")

            stars = pp_data.get("star_rating")
            # _max_combo = pp_data.get("perfect_combo")
            # _expected_bpm = pp_data.get("expected_bpm")

            # _n300 = pp_data.get("n300")
            # _n100 = pp_data.get("n100") 
            # _n50 = pp_data.get("n50")
            # _expected_miss = pp_data.get("misses")

            # _aim = pp_data.get("aim")
            # _acc = pp_data.get("acc")
            # _speed = pp_data.get("speed")
        
        except Exception as e:
            print(f"neko API failed: {e}")

            pp_data = {
                'pp': 10.0, 
                'no_choke_pp': 0.0, 
                'perfect_pp': 0.0, 
                'star_rating': 10.10, 
                'perfect_combo': 0, 
                'expected_bpm': 0.0, 
                'n300': 0, 'n100': 0, 'n50': 0, 'misses': 0, 
                'aim': 0.0, 'acc': 0.0, 'speed': 0.0
            }

            pp = pp_data.get("pp")
            # _choke = pp_data.get("no_choke_pp")
            # _max_pp = pp_data.get("perfect_pp")

            stars = pp_data.get("star_rating")
            # _max_combo = pp_data.get("perfect_combo")
            # _expected_bpm = pp_data.get("expected_bpm")

            # _n300 = pp_data.get("n300")
            # _n100 = pp_data.get("n100") 
            # _n50 = pp_data.get("n50")
            # _expected_miss = pp_data.get("misses")

            # _aim = pp_data.get("aim")
            # _acc = pp_data.get("acc")
            # _speed = pp_data.get("speed")

        #temp pp fix
        pp = pp if not isinstance(osu_score.get("pp"), (int, float)) or osu_score.get("pp") <= 0 else osu_score.get("pp")
    

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


        target_size = (img_w, row_height)
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
        img.paste(ava, (gap + left_offset, y_base + gap), ava)

        x_left = 300
        base_y = y_base + 90
        row_step = 90
        stat_gap = 10
        alpha1, alpha2 = 200, 100

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
            font_big,
            (255, 255, 255), 
            (10, 10, 10), 2)        
        
        bbox1 = draw.textbbox((0, 0), username_text, font=font_big)        
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
            max_width=img_w - int(mods_width) - gap*6,
            max_lines=2,
            font_big=font_big
        )

        x_right = img_w + gap - gap *3 + 10
        y_top = y_base + 344
        gap_map = -32

        cs, hp = f"{T.get('CS')[l]}", f"{T.get('HP')[l]}"
        od, ar = f"{T.get('OD')[l]}", f"{T.get('AR')[l]}"

        # stars_text = f"{T.get('stars')[l]}"
        # drain_text = f"{T.get('drain')[l]}"
        # bpm_text = f"{T.get('bpm')[l]}"
        
        map_args = {
            "btn_h":70, 
            "btn_min_w":10, 
            "letter_fisrst_pad_y":0,
            "letter_second_pad_y":40,
            "overlay_transparency":0,
            "font_text":font_big, 
            "font_prop":font_small,
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
        
        _x_left5_map = create_stat_button_right(
            img, draw, x_left4_map - gap_map, y_top,                                
            text=str(values.get("cs")), prop=cs,
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
        pp_text = 'PP'
        great_text = '300'
        ok_text = '100'
        meh_text = '50'
        miss_text = 'X'

        pp = f"{pp:.2f}"

        if hide_values is not None:
            if 'pp' in hide_values:
                pp = '?'
                

        rows = [
            [   
                (f"{lazer_data.get('rank', '?')}", rank_text, (255, 255, 255, 1), alpha1),             
                (f"{osu_score.get('accuracy', 0)*100:.2f}%", accuracy_text, (201, 201, 201, 1), alpha1),
                (f"{osu_score.get('max_combo', 0)}x", combo_text, (201, 201, 201, 1), alpha1),
                (pp, pp_text, (201, 201, 201, 1), alpha1),
            ],
            [
                (osu_score.get("count_300", 0), great_text, (83, 179, 255, 1), alpha2),
                (osu_score.get("count_100", 0), ok_text, (84, 255, 105, 1), alpha2),
                (osu_score.get("count_50", 0), meh_text, (245, 255, 84, 1), alpha2),
                (osu_score.get("count_miss", 0), miss_text, (255, 84, 84, 1), alpha2),
            ],            
        ]

        for row_index, row in enumerate(rows):
            y = base_y + row_index * row_step
            x = x_left

            for value, label, color, alpha in row:
                x = create_stat_button_left(
                    img, draw, x, y,
                    text=str(value),
                    prop=label,
                    letter_pad=32,
                    overlay_transparency=alpha,
                    overlay_color=color,
                    font_text=font_big,
                    font_prop=font_small
                ) + stat_gap
    
    for i, data in enumerate(scores):
        y_base = i * row_height

        if i+1 != len(scores):
            create_stat_button_left(
                img, draw, int(img_w/2) - 42, y_base + int(img_h/len(scores)) - 23,
                text='VS',
                prop='',
                overlay_transparency=255,
                overlay_color=line_color,
                font_text=font_big,
                font_prop=font_small
            ) + stat_gap


    img_path = f"{BOT_DIR}/cache/compare_{len(scores)}{beatmap_id}{uid}.png"
    img.convert("RGB").save(img_path)

    return img_path
