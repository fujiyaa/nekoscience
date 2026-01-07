


import colorsys



def hue_to_rgba(hue, saturation=1.0, lightness=0.5, alpha=255,
                min_luminance=120):
    if hue is None:
        hue = 349

    h = (hue % 360) / 360.0
    r, g, b = colorsys.hls_to_rgb(h, lightness, saturation)

    r, g, b = int(r * 255), int(g * 255), int(b * 255)

    lum = 0.2126*r + 0.7152*g + 0.0722*b

    if lum > min_luminance:
        factor = min_luminance / lum
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)

    return (r, g, b, alpha)
