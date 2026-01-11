


from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from ....external.osu_http import beatmap
from ....external.localapi import get_map_stats_neko_api
from .image_utils import create_stat_button_left, create_stat_button_right, draw_text_with_shadow
from .utils import format_length, iso_to_DaysMonthYear, stars_to_prop, trim_text
from .fetch import fetch_cover

from ....systems.translations import CARD_BEATMAP as T
from config import BOT_DIR, BG_LIST_DIR, BG_CARD_DIR



async def create_beatmap_image(map_data, beatmap_id):   
    l = map_data['lang']

    img_w, img_h = 1500, 1040
    corner_radius = 40

    bpm_map = map_data['bpm']
    mode = map_data['mode_int']
    if mode != 0: return
    length = format_length(map_data['total_length'])
    
    
    circles, sliders = map_data['count_circles'], map_data['count_sliders']
    
    plays = f"{map_data['playcount']:,}"
    psc = map_data['passcount']
    max_combo_map = f" (x{map_data['max_combo']:,})"
    version = trim_text(map_data['version'],                38  )
    guest = trim_text(map_data['owners'][0]['username'],    30  ) 
    artist = trim_text(map_data['beatmapset']['artist'],    50  ) 
    creator = trim_text(map_data['beatmapset']['creator'],  28  )
    title1 = trim_text(map_data['beatmapset']['title'],     32  ) 
    title2 = trim_text(map_data['beatmapset']['title'],     42  )            
    favs =  f"{map_data['beatmapset']['favourite_count']:,}"

    submitted = map_data['beatmapset']['submitted_date']
    updated = map_data['last_updated']

    submitted = iso_to_DaysMonthYear(submitted, l)
    updated = iso_to_DaysMonthYear(updated, l)

    submitted = f"{T.get('submitted')[l]} ", submitted
    updated = f"{T.get('updated')[l]} ", updated
    mapper = f"{T.get('mapset by')[l]} ", creator    
    guest_mapper = f"{T.get('mapped by')[l]} {guest}"

    cs, hp = f"{T.get('CS')[l]}", f"{T.get('HP')[l]}"
    od, ar = f"{T.get('OD')[l]}", f"{T.get('AR')[l]}"

    stars_text = f"{T.get('stars')[l]}"
    drain_text = f"{T.get('drain')[l]}"
    bpm_text = f"{T.get('bpm')[l]}"

    combo_text = f"{T.get('combo')[l]}"
    max_pp_text = f"{T.get('max pp')[l]}"

    acc_text = f"{T.get('acc')[l]}"
    aim_text = f"{T.get('aim')[l]}"
    speed_text = f"{T.get('speed')[l]}"

    status = map_data['status']

    try:
        status_text = f"{T.get(str(status))[l]}"    
        status_color = f"{T.get(str(status))['color']}"
    except:
        status_text = f"{T.get('unknown')[l]}"    
        status_color = f"{T.get('unknown')['color']}"
    status_color = tuple(map(int, status_color.strip("()").split(",")))

    bg_card_url = map_data['beatmapset']['covers']['card@2x']
    bg_list_url = map_data['beatmapset']['covers']['list@2x']

    
        
    bg_card_crop_h = 280

    scale = bg_card_crop_h / img_h
    new_w = int(img_w * scale)

    bg_card_thumb_size = (new_w, bg_card_crop_h)

    bg_list_path = await fetch_cover(bg_list_url, beatmap_id, BG_LIST_DIR, radius = corner_radius)
    bg_card_path = await fetch_cover(bg_card_url, beatmap_id, BG_CARD_DIR, thumb_size = bg_card_thumb_size, radius = 0)


    try:
        _path, values = await beatmap(beatmap_id)
    except:
        values = {'hp': 0.0, 'cs': 0.0, 'od': 0.0, 'ar': 0.0}
    
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

        _pp = pp_data.get("pp")
        _choke = pp_data.get("no_choke_pp")
        max_pp = pp_data.get("perfect_pp")

        stars = pp_data.get("star_rating")
        max_combo = pp_data.get("perfect_combo")
        expected_bpm = pp_data.get("expected_bpm")

        _n300 = pp_data.get("n300")
        _n100 = pp_data.get("n100") 
        _n50 = pp_data.get("n50")
        _expected_miss = pp_data.get("misses")

        aim = pp_data.get("aim")
        acc = pp_data.get("acc")
        speed = pp_data.get("speed")
    
    except Exception as e:
        print(f"neko API failed: {e}")

        pp_data = {
            'pp': 0.0, 
            'no_choke_pp': 0.0, 
            'perfect_pp': 0.0, 
            'star_rating': 0.0, 
            'perfect_combo': 0, 
            'expected_bpm': 0.0, 
            'n300': 0, 'n100': 0, 'n50': 0, 'misses': 0, 
            'aim': 0.0, 'acc': 0.0, 'speed': 0.0
        }

        _pp = pp_data.get("pp")
        _choke = pp_data.get("no_choke_pp")
        max_pp = pp_data.get("perfect_pp")

        stars = pp_data.get("star_rating")
        max_combo = pp_data.get("perfect_combo")
        expected_bpm = pp_data.get("expected_bpm")

        _n300 = pp_data.get("n300")
        _n100 = pp_data.get("n100") 
        _n50 = pp_data.get("n50")
        _expected_miss = pp_data.get("misses")

        aim = pp_data.get("aim")
        acc = pp_data.get("acc")
        speed = pp_data.get("speed")

    try:
        f1 = "cards/assets/fonts/PlaypenSans"
        s1, s2, s3, s4, _s5, s6, _s7, _s8 = "ExtraBold", "Bold", "SemiBold", "Medium", "Regular", "Light", "ExtraLight", "Thin"        

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
    main_y_offset = 20     
    padding_to_border = 80

    list_x, list_y, = padding_to_border, main_y_offset + padding_to_border + 120
    list_h = 300 # const

    darkness_amount = 0.6
    bg_blur_amount = 70   



    # подвал
    asset = Image.open(bg_card_path).convert("RGBA").resize((img_w, img_h))
    draw = ImageDraw.Draw(img)   

    asset = asset.filter(ImageFilter.GaussianBlur(bg_blur_amount))
    
    enhancer = ImageEnhance.Brightness(asset)    
    asset = enhancer.enhance(darkness_amount)    

    img.paste(asset, (0, 0), asset)


    # тайтл & guest diff
    title_pos = (padding_to_border, main_y_offset + 10)    
    guest_mapper_pos = (padding_to_border, main_y_offset + 100)

    title_shadow_offset = (0, 0)
    title_shadow_radius = 20
    title_padding = (30, 6)

    bbox = draw.textbbox(title_pos, title1, font_title)
    x0, y0, x1, y1 = bbox

    pad_x, pad_y = title_padding

    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    glow_color = (255, 255, 255, 80)
    border_color = (155, 155, 155, 255)
    title_color = (255, 255, 255, 255)
    guest_mapper_color = (220, 220, 220, 255)
    guest_mapper_shadow_color = (20, 20, 20, 255)

    title_text_shadow_offset = 2  
    guest_mapper_shadow_offset = 1   


    shadow_draw.rounded_rectangle(
        (
            x0 - pad_x + title_shadow_offset[0],
            y0 - pad_y + title_shadow_offset[1],
            x1 + pad_x + title_shadow_offset[0],
            y1 + pad_y + title_shadow_offset[1],
        ),
        radius=100,
        fill=glow_color
    )

    shadow_layer = shadow_layer.filter(
        ImageFilter.GaussianBlur(radius=title_shadow_radius)
    )

    img = Image.alpha_composite(img, shadow_layer)
    draw = ImageDraw.Draw(img)
     
    draw_text_with_shadow(draw, title_pos, title1, font_title, 
        title_color, 
        border_color, 
        title_text_shadow_offset)
    
    draw_text_with_shadow(draw, guest_mapper_pos, guest_mapper, font_guest_mapper, 
        guest_mapper_color, 
        guest_mapper_shadow_color, 
        guest_mapper_shadow_offset)


    # режим
    selected = "Standard"

    modes = ["Standard", "Taiko", "Catch", "Mania"]

    asset_size = 50    
    gap = 20    
    
    start_x, start_y = list_x + 20, list_y + list_h + 40
    icon_size = asset_size, asset_size

    for i, mode in enumerate(modes):
        asset = Image.open(f"{BOT_DIR}/cards/assets/gamemodes/{mode}.png").convert("RGBA")
        asset = asset.resize(icon_size)
        
        x = start_x + i * (icon_size[0] + gap)

        if mode != selected:
            enhancer = ImageEnhance.Brightness(asset)
            asset = enhancer.enhance(0.2)

        img.paste(asset, (x, start_y), asset)


    # аватарка карты
    asset_transparency = 80
    asset_gap = 20
    avatar_pad = 4

    overlay_x, overlay_y = list_x + avatar_pad, list_y + avatar_pad
    overlay_w, overlay_h = list_h, list_h
    overlay = Image.new("RGBA", (overlay_w, overlay_h), (0, 0, 0, asset_transparency))

    overlay_mask = Image.new("L", (overlay_w, overlay_h), 0)
    mask_draw = ImageDraw.Draw(overlay_mask)
    mask_draw.rounded_rectangle(
        (0, 0, overlay_w, overlay_h),
        radius=corner_radius,
        fill=asset_transparency
    )

    img.paste(overlay, (overlay_x, overlay_y), overlay_mask)
    
    asset_pos = list_x, list_y
    asset = Image.open(bg_list_path).convert("RGBA")
    
    img.paste(asset, asset_pos, asset)

    asset_transparency = 80
    asset_gap = 20


    # оверлей главных свойств
    
    overlay_transparency = 80
    asset_gap = 20

    overlay_x, overlay_y = list_x + list_h + asset_gap, list_y
    overlay_w, overlay_h = img_w - list_h - padding_to_border*2 - asset_gap, list_h + 120
    overlay = Image.new("RGBA", (overlay_w, overlay_h), (0, 0, 0, overlay_transparency))

    overlay_mask = Image.new("L", (overlay_w, overlay_h), 0)
    mask_draw = ImageDraw.Draw(overlay_mask)
    mask_draw.rounded_rectangle(
        (0, 0, overlay_w, overlay_h),
        radius=corner_radius,
        fill=overlay_transparency
    )

    img.paste(overlay, (overlay_x, overlay_y), overlay_mask)

    draw = ImageDraw.Draw(img)
    
    line_color_key = 120
    line_width = 2
    line_color = (line_color_key, line_color_key, line_color_key)
    line_pad = 40    
    line_y = overlay_y + 86

    draw.line((overlay_x + line_pad, line_y, overlay_x + overlay_w - line_pad, line_y), line_color, line_width) 


    # в оверлее
    pad_x = 40
    pad_tuple_text = 0

    pad_iter = 56
    info_base1 = 90
    info_base2 = 100
    version_y =     10
    title_y =       info_base1
    artist_y =      info_base1 + pad_iter*1 
    mapper_y =      info_base2 + pad_iter*2
    submitted_y =   info_base2 + pad_iter*3
    updated_y =     info_base2 + pad_iter*4

    # версия
    version_pos = (overlay_x + pad_x, overlay_y + version_y)

    version_color = (255, 255, 255, 255)
    version_shadow_color = (100, 100, 100, 255)
    version_shadow_offset = 2

    draw_text_with_shadow(draw, version_pos, version, font_version, 
        version_color, 
        version_shadow_color, 
        version_shadow_offset)

    # тайтл
    title_pos = (overlay_x + pad_x, overlay_y + title_y)

    title_color = (255, 255, 255, 255)
    title_shadow_color = (20, 20, 20, 255)
    title_shadow_offset = 2

    draw_text_with_shadow(draw, title_pos, title2, font_title_overlay, 
        title_color, 
        title_shadow_color, 
        title_shadow_offset)    
    
    # артист
    artist_pos = (overlay_x + pad_x, overlay_y + artist_y)

    artist_color = (220, 220, 220, 220)
    artist_shadow_color = (20, 20, 20, 255)
    artist_shadow_offset = 2

    draw_text_with_shadow(draw, artist_pos, artist, font_artist, 
        artist_color, 
        artist_shadow_color, 
        artist_shadow_offset)    

    # маппер
    submitted_pos = (overlay_x + pad_x, overlay_y + submitted_y)

    submitted_color = (255, 255, 255, 255)
    submitted_shadow_color = (100, 100, 100, 255)
    submitted_shadow_offset = 2

    draw_text_with_shadow(draw, submitted_pos, submitted[0], font_submitted1, 
        submitted_color, 
        submitted_shadow_color, 
        submitted_shadow_offset)
    
    bbox = draw.textbbox(submitted_pos, submitted[0], font_submitted1)
    submitted_pos = (submitted_pos[0] + (bbox[2] - bbox[0]) + pad_tuple_text, submitted_pos[1])

    draw_text_with_shadow(draw, submitted_pos, submitted[1], font_submitted2, 
        submitted_color, 
        submitted_shadow_color, 
        submitted_shadow_offset)
    


    # сабмиттед
    mapper_pos = (overlay_x + pad_x, overlay_y + mapper_y)

    mapper_color = (255, 255, 255, 255)
    mapper_shadow_color = (100, 100, 100, 255)
    mapper_shadow_offset = 2

    draw_text_with_shadow(draw, mapper_pos, mapper[0], font_mapper1, 
        mapper_color, 
        mapper_shadow_color, 
        mapper_shadow_offset) 

    bbox = draw.textbbox(mapper_pos, mapper[0], font_mapper1)
    mapper_pos = (mapper_pos[0] + (bbox[2] - bbox[0]) + pad_tuple_text,mapper_pos[1]) 

    draw_text_with_shadow(draw, mapper_pos, mapper[1], font_mapper2, 
        mapper_color, 
        mapper_shadow_color, 
        mapper_shadow_offset)     


    # статус
    updated_pos = (overlay_x + pad_x, overlay_y + updated_y)

    updated_color = (255, 255, 255, 255)
    updated_shadow_color = (100, 100, 100, 255)
    updated_shadow_offset = 2

    draw_text_with_shadow(draw, updated_pos, updated[0], font_updated1, 
        updated_color, 
        updated_shadow_color, 
        updated_shadow_offset)  

    bbox = draw.textbbox(updated_pos, updated[0], font_updated1)
    updated_pos = (updated_pos[0] + (bbox[2] - bbox[0]) + pad_tuple_text, updated_pos[1])

    draw_text_with_shadow(draw, updated_pos, updated[1], font_updated2, 
        updated_color, 
        updated_shadow_color, 
        updated_shadow_offset)
    

    # кнопка статуса      
    asset_transparency = 150

    bbox = draw.textbbox((0, 0), status_text, font_status_btn)

    letter_pad = 80
    btn_w, btn_h = letter_pad + (bbox[2] - bbox[0]), 100
    pad_x_inv, pad_y_inv = 20, 40    

    btn_x, btn_y = overlay_x + overlay_w - pad_x_inv - btn_w, overlay_y + overlay_h - pad_y_inv - btn_h
    btn = Image.new("RGBA", (btn_w, btn_h), (status_color[0],status_color[1],status_color[2], asset_transparency))

    btn_mask = Image.new("L", (btn_w, btn_h), 0)
    mask_draw = ImageDraw.Draw(btn_mask)
    mask_draw.rounded_rectangle(
        (0, 0, btn_w, btn_h),
        radius=btn_h/2,
        fill=asset_transparency
    )

    img.paste(btn, (btn_x, btn_y), btn_mask)

    btn_text_pos = (btn_x + letter_pad/2, btn_y + 15)

    btn_text_color = (255, 255, 255, 255)
    btn_text_shadow_color = (100, 100, 100, 255)
    btn_text_shadow_offset = 2

    draw_text_with_shadow(draw, btn_text_pos, status_text, font_status_btn, 
        btn_text_color, 
        btn_text_shadow_color, 
        btn_text_shadow_offset)  
        

    # после оверлея
    main_y = overlay_y + overlay_h + 0


    # ar, hp ...   
    x_right = overlay_x + overlay_w
    y_top = main_y + 30
    gap = 20

    x_left = create_stat_button_right(img, draw, x_right, y_top,
                                text=f"{stars_text} {stars:0.2f}", 
                                letter_fisrst_pad_y = 20, letter_second_pad_y = 78,
                                prop=stars_to_prop(stars), overlay_transparency=80,
                                font_text=font_prop3, font_prop=font_prop4)

    x_left2 = create_stat_button_right(img, draw, x_left - gap, y_top,
                                 text=str(values.get("ar")), prop=ar,
                                font_text=font_prop1, font_prop=font_prop2)
    
    x_left3 = create_stat_button_right(img, draw, x_left2 - gap, y_top,                                 
                                text=str(values.get("od")), prop=od,
                                font_text=font_prop1, font_prop=font_prop2)
    
    x_left4 = create_stat_button_right(img, draw, x_left3 - gap, y_top,                                 
                                text=str(values.get("hp")), prop=hp,
                                font_text=font_prop1, font_prop=font_prop2)
    
    _x_left5 = create_stat_button_right(img, draw, x_left4 - gap, y_top,                                
                                text=str(values.get("cs")), prop=cs,
                                font_text=font_prop1, font_prop=font_prop2)

      
    # skills 
    x_left = padding_to_border
    y_top = main_y + 152 + 60
    gap = 10

    x_right1 = create_stat_button_left(img, draw, x_left, y_top,
                                    text=str(length), prop=drain_text, overlay_transparency=200,
                                    font_text=font_skill1, font_prop=font_skill2)
    
    x_right2 = create_stat_button_left(img, draw, x_right1 + gap, y_top,
                                    text=f"{expected_bpm:0.0f}", prop=bpm_text, overlay_transparency=200,
                                    font_text=font_skill1, font_prop=font_skill2)
    
    x_right3 = create_stat_button_left(img, draw, x_right2 + gap, y_top,
                                    text=f"{max_combo}x", prop=combo_text, overlay_transparency=200,
                                    font_text=font_skill1, font_prop=font_skill2)
    
    x_right4 = create_stat_button_left(img, draw, x_right3 + gap, y_top,
                                    text=f"{max_pp:0.2f}pp", prop=max_pp_text, overlay_transparency=200,
                                    font_text=font_skill1, font_prop=font_skill2)

    x_right5 = create_stat_button_left(img, draw, x_right4 + gap + 30, y_top,
                                    text=f"{acc:0.0f}", prop=acc_text,
                                    font_text=font_skill1, font_prop=font_skill2)

    x_right6 = create_stat_button_left(img, draw, x_right5 + gap, y_top,
                                    text=f"{aim:0.0f}", prop=aim_text,
                                    font_text=font_skill1, font_prop=font_skill2)

    _x_right7 = create_stat_button_left(img, draw, x_right6 + gap, y_top,
                                    text=f"{speed:0.0f}", prop=speed_text,
                                    font_text=font_skill1, font_prop=font_skill2)
    
    
    
    # !!!
    bg = Image.open(f"{BOT_DIR}/cards/assets/top5/botname.png").convert("RGBA").resize((380, 106))
    img.paste(bg, (img_w - 400, 60), bg)  

    img_path = f'{BOT_DIR}/cache/{beatmap_id}.png'
    img.convert("RGB").save(img_path)

    return img_path