


from PIL import Image, ImageDraw



def add_rounded_corners(img: Image.Image, radius: int, alpha: int = 255, skip_corners=None) -> Image.Image:
    if skip_corners is None:
        skip_corners = []

    big_size = (img.size[0]*2, img.size[1]*2)
    mask = Image.new("L", big_size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)

    w, h = big_size
    r = radius*2

    if "tl" in skip_corners:
        draw_mask.rectangle((0, 0, r, r), fill=255)
    if "tr" in skip_corners:
        draw_mask.rectangle((w - r, 0, w, r), fill=255)
    if "bl" in skip_corners:
        draw_mask.rectangle((0, h - r, r, h), fill=255)
    if "br" in skip_corners:
        draw_mask.rectangle((w - r, h - r, w, h), fill=255)

    mask = mask.resize(img.size, Image.LANCZOS)

    alpha_channel = mask.point(lambda i: i * (alpha / 255))
    img.putalpha(alpha_channel)
    return img

def draw_text_with_shadow(draw, pos, text, font, fill, shadowcolor, shadow_offset = 2):
        x, y = pos

        for dx, dy in [(-shadow_offset,0), (shadow_offset,0), (0,-shadow_offset), (0,shadow_offset)]:
            draw.text((x+dx, y+dy), text, font=font, fill=shadowcolor)

        draw.text((x, y), text, font=font, fill=fill)

def create_stat_button_right(img, draw, x_right, y_top, text, prop,
                       font_text, font_prop,
                       overlay_transparency=130,
                       letter_pad=60,
                       letter_fisrst_pad_y=10,
                       letter_second_pad_y=90,
                       btn_min_w=152,
                       btn_h=152,
                       pad_y=20,
                       btn_text_color=(255,255,255,255),
                       btn_text_shadow_color=(120,120,120,255),
                       btn_text_shadow_offset=2):

    bbox1 = draw.textbbox((0,0), text, font=font_text)
    bbox2 = draw.textbbox((0,0), prop, font=font_prop)

    btn_w = max(btn_min_w, letter_pad + bbox1[2])
    btn_y_pos = y_top + pad_y

    btn = Image.new("RGBA", (btn_w, btn_h), (20, 20, 20, overlay_transparency))

    btn_mask = Image.new("L", (btn_w, btn_h), 0)
    mask_draw = ImageDraw.Draw(btn_mask)
    mask_draw.rounded_rectangle(
        (0, 0, btn_w, btn_h),
        radius=btn_h/2,
        fill=overlay_transparency
    )

    btn_x = x_right - btn_w
    img.paste(btn, (btn_x, btn_y_pos), btn_mask)

    text1_x = btn_x + (btn_w - bbox1[2]) / 2
    text1_y = btn_y_pos + letter_fisrst_pad_y

    text2_x = btn_x + (btn_w - bbox2[2]) / 2
    text2_y = btn_y_pos + letter_second_pad_y

    draw_text_with_shadow(draw, (text1_x, text1_y), text, font_text,
                          btn_text_color, btn_text_shadow_color, btn_text_shadow_offset)
    draw_text_with_shadow(draw, (text2_x, text2_y), prop, font_prop,
                          btn_text_color, btn_text_shadow_color, btn_text_shadow_offset)

    return btn_x

def create_stat_button_left(img, draw, x_left, y_top, text, prop,
                            font_text, font_prop,
                            overlay_transparency=80,
                            letter_pad=60,
                            btn_min_w=60,
                            btn_h=46,
                            pad_y=0,
                            overlay_color=(20, 20, 20),
                            btn_text_color=(255,255,255,255),
                            btn_text_shadow_color=(80,80,80,255),
                            btn_text_shadow_offset=2,
                            letter_fisrst_pad_y=0,
                            letter_second_pad_y=46):
    # Считаем размер текста
    bbox1 = draw.textbbox((0,0), text, font=font_text)
    bbox2 = draw.textbbox((0,0), prop, font=font_prop)

    btn_w = max(btn_min_w, letter_pad + bbox1[2])
    btn_y_pos = y_top + pad_y
    
    btn = Image.new("RGBA", (btn_w, btn_h), (overlay_color))

    btn_mask = Image.new("L", (btn_w, btn_h), 0)
    mask_draw = ImageDraw.Draw(btn_mask)
    mask_draw.rounded_rectangle(
        (0, 0, btn_w, btn_h),
        radius=btn_h/2,
        fill=overlay_transparency
    )

    btn_x = x_left
    img.paste(btn, (btn_x, btn_y_pos), btn_mask)

    text1_x = btn_x + (btn_w - bbox1[2]) / 2
    text1_y = btn_y_pos + letter_fisrst_pad_y

    text2_x = btn_x + (btn_w - bbox2[2]) / 2
    text2_y = btn_y_pos + letter_second_pad_y

    draw_text_with_shadow(draw, (text1_x, text1_y), text, font_text,
                          btn_text_color, btn_text_shadow_color, btn_text_shadow_offset)
    draw_text_with_shadow(draw, (text2_x, text2_y), prop, font_prop,
                          btn_text_color, btn_text_shadow_color, btn_text_shadow_offset)

    return btn_x + btn_w

def draw_multiline_text_with_shadow(
    draw,
    pos,
    text,
    font,
    fill,
    shadowcolor,
    max_width,
    max_lines,
    align="left",
    shadow_offset=2,
    line_spacing=4,
    font_big=None
):
    x, y = pos

    def text_width(t, f):
        bbox = draw.textbbox((0, 0), t, font=f)
        return bbox[2] - bbox[0]

    def get_line_height(f):
        ascent, descent = f.getmetrics()
        return ascent + descent + line_spacing

    if font_big:
        w_big = text_width(text, font_big)

        if "\n" not in text and w_big <= max_width:
            line_height = get_line_height(font_big)

            if align == "right":
                xx = x - w_big
            else:
                xx = x

            for dx, dy in [
                (-shadow_offset, 0),
                (shadow_offset, 0),
                (0, -shadow_offset),
                (0, shadow_offset)
            ]:
                draw.text((xx + dx, y + dy), text, font=font_big, fill=shadowcolor)

            draw.text((xx, y), text, font=font_big, fill=fill)

            return w_big, line_height

    font_used = font

    def split_long_word(word):
        parts = []
        current = ""

        for ch in word:
            test = current + ch
            if text_width(test, font_used) <= max_width:
                current = test
            else:
                if current:
                    parts.append(current)
                current = ch

        if current:
            parts.append(current)

        return parts

    words = text.split()
    lines = []
    current = ""

    for word in words:
        pieces = split_long_word(word) if text_width(word, font_used) > max_width else [word]

        for piece in pieces:
            test = piece if not current else f"{current} {piece}"

            if text_width(test, font_used) <= max_width:
                current = test
            else:
                lines.append(current)
                current = piece

    if current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]

        while text_width(last + "...", font_used) > max_width and last:
            last = last[:-1]

        lines[-1] = last + "..."

    line_height = get_line_height(font_used)

    max_line_width = 0

    for i, line in enumerate(lines):
        yy = y + i * line_height
        w = text_width(line, font_used)

        max_line_width = max(max_line_width, w)

        if align == "right":
            xx = x - w
        else:
            xx = x

        for dx, dy in [
            (-shadow_offset, 0),
            (shadow_offset, 0),
            (0, -shadow_offset),
            (0, shadow_offset)
        ]:
            draw.text((xx + dx, yy + dy), line, font=font_used, fill=shadowcolor)

        draw.text((xx, yy), line, font=font_used, fill=fill)

    used_height = len(lines) * line_height

    return max_line_width, used_height
