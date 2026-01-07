


from datetime import date
from PIL import Image, ImageDraw, ImageFont

from config import BOT_DIR



def make_card(title, bg, username, country_code, avatar_path, accuracy, aim, speed,
              global_rank, country_rank, level, medals, mode, output="card.png", acc_total=None, aim_total=None, speed_total=None):

    bg_name = "novice" 
    if bg is not None:
        bg_name = bg  

    card = Image.open(f"{BOT_DIR}/cards/assets/backgrounds/{bg_name}.png").convert("RGBA")
    draw = ImageDraw.Draw(card)

    asset = Image.open(f"{BOT_DIR}/cards/assets/branding/outline.png").convert("RGBA")
    card.paste(asset, (0, 0), mask=asset.split()[3])

    asset = Image.open(f"{BOT_DIR}/cards/assets/gamemodes/{mode}.png").convert("RGBA")
    card.paste(asset, (808, 53), asset)

    asset = Image.open(f"{BOT_DIR}/cards/assets/branding/icon.png").convert("RGBA")
    card.paste(asset, (0, 1260-184), asset)
   

    # дем
    font_black_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 70)
    font_black_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Black.ttf", 48)
    font_bold_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 68)
    font_bold_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 50)
    font_bold_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 42)
    font_bold_small_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 35)
    font_bold_nano = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 26)       
    font_bold_italic_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-BoldItalic.ttf", 50)
    font_bold_italic_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-BoldItalic.ttf", 34)
    font_light_italic_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 48)
    font_light_italic_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 42)
    font_light_italic_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 32)
    font_light_italic_small_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-LightItalic.ttf", 34)
    font_medium_italic_med = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-MediumItalic.ttf", 32)
    font_regular_big = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Regular.ttf", 68)
    font_regular_nano = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Regular.ttf", 26)
    font_thin_small = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Thin.ttf", 48)
    font_bold_nano_2 = ImageFont.truetype(f"{BOT_DIR}/cards/assets/fonts/Roboto-Bold.ttf", 26)     

    # # Верхний заголовок
    # draw.text((52, 35),title,font=font_bold_italic_med, fill=(200, 200, 200))

    flag_path = f"{BOT_DIR}/cards/assets/flags/{country_code}.png"    
    flag_img = Image.open(flag_path).convert("RGBA")


    block_left = 52
    block_right = 980 - 250
    max_width = block_right - block_left

    words = title.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        line_width = draw.textlength(test_line, font=font_bold_italic_med)
        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    lines = lines[:2]
    title_multiline = "\n".join(lines)

    if len(lines) == 1:
        title_y = 55
        username_y = 110
        flag_y = 126
    else:
        title_y = 25
        username_y = 145
        flag_y = 162

    draw.text((block_left, title_y), title_multiline, font=font_bold_italic_med, fill=(200, 200, 200), spacing=14)

    draw.text((block_left, username_y), username, font=font_black_big, fill="white")
    bbox = draw.textbbox((block_left, username_y), username, font=font_black_big)
    text_width = bbox[2] - bbox[0]

    flag_ratio = flag_img.width / flag_img.height
    flag_height = 50 
    flag_width = int(flag_height * flag_ratio)
    flag_img = flag_img.resize((flag_width, flag_height))

    mask = Image.new("L", (flag_width, flag_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = 12 
    mask_draw.rounded_rectangle((0, 0, flag_width, flag_height), radius=radius, fill=255)

    card.paste(flag_img, (block_left + text_width + 15, flag_y), mask)

    size = 444
    avatar = Image.open(avatar_path).convert("RGBA").resize((size, size))
    card.paste(avatar, (52, 302), avatar)

    x0, y0 = 535, 337

    block_spacing = 60
    line_spacing = 120
    skill_offset = 20
    total_ox = 80
    total_oy = 35

    # ACCURACY
    draw.text((x0, y0), "|", font=font_bold_med, fill="white")
    draw.text((x0 + skill_offset, y0 + 8), "ACCURACY", font=font_light_italic_med, fill="white")
    accuracy_value = f"{accuracy:.2f}" 
    int_part, frac_part = accuracy_value.split(".") 
    draw.text((x0 + 6, y0 + 52), f"{int_part}.", font=font_bold_big, fill="white")
    bbox = draw.textbbox((x0 + 6, y0 + 52), f"{int_part}.", font=font_bold_big)
    width_int = bbox[2] - bbox[0]
    draw.text((x0 + 6 + width_int, y0 + 52), frac_part, font=font_regular_big, fill="white")
    draw.text((x0 + 6 + width_int + total_ox, y0 + 52 + total_oy), f" ~ {acc_total:.2f}" , font=font_bold_nano_2, fill=(200, 200, 200))

    # AIM
    draw.text((x0, y0 + line_spacing + block_spacing), "|", font=font_bold_med, fill="white")
    draw.text((x0 + skill_offset, y0 + 8 + line_spacing + block_spacing), "AIM", font=font_light_italic_med, fill="white")
    aim_value = f"{aim:.2f}"
    int_part, frac_part = aim_value.split(".")
    draw.text((x0 + 6, y0 + 52 + line_spacing + block_spacing), f"{int_part}.", font=font_bold_big, fill="white")
    bbox = draw.textbbox((x0 + 6, y0 + 52 + line_spacing), f"{int_part}.", font=font_bold_big)
    width_int = bbox[2] - bbox[0]
    draw.text((x0 + 6 + width_int, y0 + 52 + line_spacing + block_spacing), frac_part, font=font_regular_big, fill="white")
    draw.text((x0 + 6 + width_int + total_ox, y0 + 52 + line_spacing + block_spacing + total_oy), f" ~ {aim_total:.2f}" , font=font_bold_nano_2, fill=(200, 200, 200))

    # SPEED
    draw.text((x0, y0 + 2 * line_spacing+ block_spacing * 2), "|", font=font_bold_med, fill="white")
    draw.text((x0 + skill_offset, y0 + 8 + 2 * line_spacing+ block_spacing * 2), "SPEED", font=font_light_italic_med, fill="white")
    speed_value = f"{speed:.2f}"
    int_part, frac_part = speed_value.split(".")
    draw.text((x0 + 6, y0 + 52 + 2 * line_spacing+ block_spacing * 2), f"{int_part}.", font=font_bold_big, fill="white")
    bbox = draw.textbbox((x0 + 6, y0 + 52 + 2 * line_spacing), f"{int_part}.", font=font_bold_big)
    width_int = bbox[2] - bbox[0]
    draw.text((x0 + 6 + width_int, y0 + 52 + 2 * line_spacing+ block_spacing * 2), frac_part, font=font_regular_big, fill="white")
    draw.text((x0 + 6 + width_int + total_ox, y0 + 52 + 2 * line_spacing+ block_spacing * 2 + total_oy), f" ~ {speed_total:.2f}" , font=font_bold_nano_2, fill=(200, 200, 200))

    x0, y0 = 73, 770
    x_block = x0 + 300
    block_width = 122

    draw.text((x0, y0), "Global", font=font_medium_italic_med, fill="white")
    draw.text((x0, y0 + 33), f"#{global_rank}", font=font_bold_small, fill="white")
    
    country_text = f"#{country_rank}"

    bbox = draw.textbbox((0, 0), country_text, font=font_bold_small)
    text_width = bbox[2] - bbox[0]

    x_text = x_block + block_width - text_width

    draw.text((x_block, y0), "Country", font=font_light_italic_small, fill="white")
    draw.text((x_text, y0 + 34), country_text, font=font_bold_small_2, fill="white")

    x0, y0 = 87, 915
    level_value = level
    level_int = int(level_value)           
    level_frac = level_value - level_int   

    draw.text((x0, y0), "Level", font=font_light_italic_small_2, fill="white")
    bbox = draw.textbbox((x0, y0), "Level", font=font_light_italic_small_2)
    width_text = bbox[2] - bbox[0]

    draw.text((x0 + width_text + 12, y0), f"{level_int}", 
            font=font_bold_italic_small, fill="white")
    bbox_num = draw.textbbox((x0 + width_text + 12, y0), f"{level_int}", font=font_bold_italic_small)
    width_num = bbox_num[2] - bbox_num[0]

    bar_left = x0 + width_text + width_num + 30   
    bar_right = x0 + 806                         
    bar_width = bar_right - bar_left

    bar_y0 = y0 + 15
    bar_height = 8
    bar_y1 = bar_y0 + bar_height
    radius = bar_height // 1

    draw.line(
        (bar_left, bar_y0 + bar_height // 2, bar_right, bar_y0 + bar_height // 2),
        fill="white", width=2
    )

    fill_len = int(bar_width * level_frac)

    if fill_len > 0:
        draw.rounded_rectangle(
            [bar_left, bar_y0, bar_left + fill_len, bar_y1],
            radius=radius,
            fill="white"
        )

    x0, y0 = 87, 894
    medals_max = 339
    medals_value = medals
    medals_percent = medals_value / medals_max
    medals_progress = int(medals_percent * 100)
       
    color_0 = (161, 190, 206)
    color_40 = (255, 140, 104)
    color_60 = (236, 85, 110)
    color_80 = (182, 106, 237)
    color_90 = (106, 237, 255)
    color_95 = (93, 89, 249)

    progress_color = color_0
   
    if medals_progress < 40:
        progress_color = color_0 
    elif medals_progress < 60:
        progress_color = color_40 
    elif medals_progress < 80:
        progress_color = color_60
    elif medals_progress < 90:
        progress_color = color_80
    elif medals_progress < 95:
        progress_color = color_90
    else: progress_color = color_95

    block_right = x0 + 808  

    text_label = "Medals"
    draw.text((x0, y0 + 60), text_label, font=font_light_italic_small_2, fill="white")

    bbox_label = draw.textbbox((x0, y0 + 60), text_label, font=font_light_italic_small_2)
    width_label = bbox_label[2] - bbox_label[0]

    draw.text((x0 + width_label + 12, y0 + 60), f"{medals_progress}%", 
            font=font_bold_italic_small, fill=progress_color)

    bbox_num = draw.textbbox((x0 + width_label + 12, y0 + 60), 
                            f"{medals_progress}%", 
                            font=font_bold_italic_small)
    width_num = bbox_num[2] - bbox_num[0]

    bar_left = x0 + width_label + width_num + 30 

    current_text = str(medals_value)
    max_text = str(medals_max)
    right_text = f"{current_text}/{max_text}"

    bbox_right = draw.textbbox((0, 0), right_text, font=font_regular_nano)
    width_right = bbox_right[2] - bbox_right[0]

    text_x = block_right - width_right
    text_y = y0 + 65

    draw.text((text_x, text_y), current_text, font=font_bold_nano, fill="white")
    bbox_cur = draw.textbbox((text_x, text_y), current_text, font=font_bold_nano)
    cur_width = bbox_cur[2] - bbox_cur[0]

    draw.text((text_x + cur_width, text_y), f"/{max_text}", 
            font=font_regular_nano, fill="white")

    bar_right = text_x - 15
    bar_width = bar_right - bar_left

    bar_y0 = y0 + 75
    bar_height = 8
    bar_y1 = bar_y0 + bar_height
    radius = bar_height // 1
    
    line_y = bar_y0 + bar_height // 2

    zone1_end = bar_left + round(bar_width * 0.39)
    zone2_end = bar_left + round(bar_width * 0.59)
    zone3_end = bar_left + round(bar_width * 0.79)
    zone4_end = bar_left + round(bar_width * 0.89)
    zone5_end = bar_left + round(bar_width * 0.94)
    zone6_end = bar_right

    draw.line((bar_left, line_y, zone1_end, line_y),    fill=color_0, width=2)
    draw.line((zone1_end, line_y, zone2_end, line_y), fill=color_40, width=2)
    draw.line((zone2_end, line_y, zone3_end, line_y), fill=color_60, width=2)
    draw.line((zone3_end, line_y, zone4_end, line_y), fill=color_80, width=2)
    draw.line((zone4_end, line_y, zone5_end, line_y), fill=color_90, width=2)
    draw.line((zone5_end, line_y, zone6_end, line_y), fill=color_95, width=2)

    fill_len = int(bar_width * medals_percent)
    if fill_len > 0:
        draw.rounded_rectangle(
            [bar_left, bar_y0, bar_left + fill_len, bar_y1],
            radius=radius,
            fill=progress_color
        )

    bot_first, bot_second = "Fujiyaosu", "Bot"
    today = date.today().isoformat()
    draw.text((220, 1140), bot_first, font=font_black_small, fill="white")
    bbox = draw.textbbox((0, 0), bot_first, font=font_black_small)
    text_width = bbox[2] - bbox[0]
    draw.text((222+text_width, 1140), bot_second, font=font_thin_small, fill="white")

    draw.text((700, 1140), today, font=font_light_italic_big, fill="white")

    card.convert("RGB").save(output) 
    print(f"Saved {output}")
    return output
