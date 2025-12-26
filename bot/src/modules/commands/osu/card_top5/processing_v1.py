


from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

from .utils import format_mods, time_ago

from config import BOT_DIR, TOP5_CARDS_DIR



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

    return trimmed + "..."

from PIL import Image

def draw_single_card(img, draw, y_offset, card_data,
                     height=120, line_spacing=8,
                     path_begin='', position=0):
    rank = card_data.get("rank", "A").lower()
    acc = card_data.get("acc", "93.12%")    
    lazer = card_data.get("lazer", False)
    pp = card_data.get("pp", "220")
    title = trim_text(card_data.get("title", "Songs Compilation"), 24)
    artist = trim_text(card_data.get("artist", "V.A."), 24)
    version = trim_text(card_data.get("version", "Extra"), 32)
    country_code = card_data.get("country_code", "RU")
    username = card_data.get("username", "Hecker")
    timestamp = card_data.get("time", datetime.utcnow().strftime("%y.%m.%d %H:%M"))
    
    mods = card_data.get("mods", ["DT", "RX"])
    if not lazer: mods.append("CL")

    padding_left = 80
    text_color = (255, 255, 255)
    version_color = (255, 220, 50)
    time_color = (155, 155, 155)
    mod_color = (100, 200, 255)
    acc_color = (225, 225, 225)
    
    PP_COLORS = {
        0: (255, 215, 0),
        1: (192, 192, 192),
        2: (205, 127, 50),
    }
    pp_color = PP_COLORS.get(position, (255, 255, 255))

    rank_path = f"{path_begin}/cards/assets/ranks/ranking-{rank}-small@2x.png"        

    font_title = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans-Bold.ttf", size=30)  
    font_artist = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans.ttf", size=20)  
    font_version = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans.ttf", size=30)  
    font_time = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans-Bold.ttf", size=30)  
    font_acc = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans.ttf", size=30)  
    font_mods = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans-ExtraBold.ttf", size=30)  
    font_pp = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans-Bold.ttf", size=36)

    font_acc_big = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans.ttf", size=36)  
    font_mods_big = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/DMSans-ExtraBold.ttf", size=36)  
    
    font_black_big = ImageFont.truetype(f"{path_begin}/cards/assets/fonts/Roboto-Black.ttf", 50)

    flag_path = f"{path_begin}/cards/assets/flags/{country_code}.png"    
    flag_img = Image.open(flag_path).convert("RGBA")

    block_left = 260

    username_y = 10
    flag_y = username_y + 8

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

    img.paste(flag_img, (block_left + text_width + 15, flag_y), mask)

    try:
        rank_img = Image.open(rank_path).convert("RGBA")
    except Exception as e:
        print(e)
        rank_img = None

    if rank_img:
        target_height = height * 0.6
        w, h = rank_img.size
        ratio = target_height / h
        rank_img = rank_img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        rank_y = y_offset + (height - rank_img.height) / 2 + 8
        img.paste(rank_img, (padding_left, int(rank_y)), rank_img)  # <-- вставляем напрямую в img

    rank_width = rank_img.width if rank_img else 36
    x = padding_left + rank_width + 20

    map_block_y_size = font_title.getbbox("Hg")[3] - font_title.getbbox("Hg")[1]
    info_block_height = 2 * map_block_y_size + line_spacing
    info_y_top = y_offset + (height - info_block_height) / 2

   # title artist
    title_text = title
    artist_text = f" by {artist}"

    draw.text((x, info_y_top), title_text, fill=text_color, font=font_title)

    title_ascent, title_descent = font_title.getmetrics()
    artist_ascent, artist_descent = font_artist.getmetrics()

    title_height = title_ascent + title_descent
    artist_height = artist_ascent + artist_descent

    y_offset_artist = info_y_top + (title_height - artist_height) / 2

    title_text = title
    artist_text = f" by {artist}"
    draw.text((x, info_y_top), title_text, fill=text_color, font=font_title)

    title_width = font_title.getbbox(title_text)[2] - font_title.getbbox(title_text)[0]
    draw.text((x + title_width + 5, y_offset_artist + 2), artist_text, fill=text_color, font=font_artist)


    # версия время
    version_text = version
    time_text = timestamp

    version_width = font_version.getbbox(version_text)[2] - font_version.getbbox(version_text)[0]

    draw.text((x, info_y_top + map_block_y_size + line_spacing), version_text, fill=version_color, font=font_version)

    time_color = (180, 180, 180)
    draw.text((x + version_width + 30, info_y_top + map_block_y_size + line_spacing),
            time_text, fill=time_color, font=font_time)

    # acc pp 
    pp_block_x = 1376
    mods_acc_block_x = 1160 

    line_height = font_mods.getbbox("Hg")[3] - font_mods.getbbox("Hg")[1]

    block_height = 2 * line_height + line_spacing
    block_y_top = y_offset + (height - block_height) / 2

    if mods:
        mods_text = " ".join(mods)
        mods_len = len(mods_text.replace(" ", ""))

        mods_bbox = font_mods.getbbox(mods_text)
        mods_width = mods_bbox[2] - mods_bbox[0]

        acc_bbox = font_acc.getbbox(acc)
        acc_width = acc_bbox[2] - acc_bbox[0]

        if mods_len < 8:
            gap = 35

            right_x = mods_acc_block_x

            acc_x = right_x - acc_width
            draw.text(
                (acc_x, y_offset + (height - line_height) / 2),
                acc,
                fill=acc_color,
                font=font_acc_big
            )

            mods_x = acc_x - gap - mods_width
            draw.text(
                (mods_x, y_offset + (height - line_height) / 2),
                mods_text,
                fill=mod_color,
                font=font_mods_big
            )

        else:
            wtf_offset = 20

            block_width = max(mods_width, acc_width)
            left_x = mods_acc_block_x - block_width + wtf_offset

            draw.text(
                (left_x + block_width - mods_width, block_y_top),
                mods_text,
                fill=mod_color,
                font=font_mods
            )

            draw.text(
                (left_x + block_width - acc_width, block_y_top + line_height + line_spacing),
                acc,
                fill=acc_color,
                font=font_acc
            )

    else:
        # модов нет
        acc_bbox = font_acc.getbbox(acc)
        acc_width = acc_bbox[2] - acc_bbox[0]
        
        right_x = mods_acc_block_x

        acc_x = right_x - acc_width
        draw.text(
            (acc_x, y_offset + (height - line_height) / 2),
            acc,
            fill=acc_color,
            font=font_acc_big
        )
    


    # PP 
    pp_color = PP_COLORS.get(position, (255, 255, 255))

    pp_text = f"{pp}pp"

    pp_block_width = 120
    pp_x_center = pp_block_x - pp_block_width // 2
    pp_width = font_pp.getbbox(pp_text)[2] - font_pp.getbbox(pp_text)[0]

    
    pp_draw_x = pp_x_center - pp_width // 2
    draw.text(
        (pp_draw_x, y_offset + (height - line_height) / 2 + 1),
        pp_text,
        fill=(0, 0, 0),
        font=font_pp
    )

    pp_draw_x = pp_x_center - pp_width // 2
    draw.text(
        (pp_draw_x, y_offset + (height - line_height) / 2),
        pp_text,
        fill=pp_color,
        font=font_pp
    )



def create_top5_image(cards_data, output="score_cards.png"):
    card_height = 120
    width = 1480
    main_offset_y = 25
    add_to_y = 50
    height = card_height * len(cards_data) + add_to_y *2 + 10

    path_begin = f"{BOT_DIR}"  # "E:/fa/nekoscience/bot"
    rank_path = f"{path_begin}/cards/assets/top5/top5card.png"      

    try:
        img = Image.open(rank_path).convert("RGBA")
    except Exception as e:
        print(e)
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)

    for i, card in enumerate(cards_data):
        y_offset = i * card_height + add_to_y
        draw_single_card(
            img,
            draw,
            y_offset + main_offset_y,
            card,
            height=card_height,
            line_spacing=12,
            path_begin=path_begin,
            position=i
        )

    img.save(output)
    print(f"Saved to {output}")
    return output

async def create_image(user_data, top_5):    
    cards = build_cards_from_top5(user_data, top_5)    

    return create_top5_image(cards, output=f"{TOP5_CARDS_DIR}/{user_data['id']}.png",)

def build_cards_from_top5(user_data ,top_5: list[dict]) -> list[dict]:
    cards = []

    for score in top_5:
        cards.append({
            "rank": score.get("rank", "N/A"),

            "title": score.get("title", "Unknown"),
            "artist": score.get("artist", "Unknown"),
            "version": score.get("version", "Unknown"),
            "mapper": score.get("mapper", score.get("creator", "Unknown")),

            "mods": format_mods(score.get("mods")),
            "lazer": score.get("lazer", False),

            "acc": f"{score.get('accuracy', 0) * 100:.2f}%",
            "pp": str(int(score.get("pp", 0))),

            "username": user_data.get('username'),
            "country_code": user_data.get('country_code'),
            "time": time_ago(score.get('time', ''))
        })

    return cards
