


from PIL import Image, ImageDraw



def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    big_size = (img.size[0]*2, img.size[1]*2)
    mask = Image.new("L", big_size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, big_size[0], big_size[1]), radius*2, fill=255)
    
    mask = mask.resize(img.size, Image.LANCZOS)
    
    img.putalpha(mask)
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
                            btn_min_w=152,
                            btn_h=60,
                            pad_y=40,
                            btn_text_color=(255,255,255,255),
                            btn_text_shadow_color=(80,80,80,255),
                            btn_text_shadow_offset=3):
    # Считаем размер текста
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

    btn_x = x_left
    img.paste(btn, (btn_x, btn_y_pos), btn_mask)

    text1_x = btn_x + (btn_w - bbox1[2]) / 2
    text1_y = btn_y_pos + 0

    text2_x = btn_x + (btn_w - bbox2[2]) / 2
    text2_y = btn_y_pos + 60

    draw_text_with_shadow(draw, (text1_x, text1_y), text, font_text,
                          btn_text_color, btn_text_shadow_color, btn_text_shadow_offset)
    draw_text_with_shadow(draw, (text2_x, text2_y), prop, font_prop,
                          btn_text_color, btn_text_shadow_color, btn_text_shadow_offset)

    return btn_x + btn_w