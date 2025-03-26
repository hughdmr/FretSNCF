""" Tools used to generates colors for the agenda """
import colorsys

def generate_colors(number_of_colors):
    """ Generates n colors spread across the visible spectrum """
    hue_spacing = 1.0 / number_of_colors
    colors = []

    for i in range(number_of_colors):
        hue = i * hue_spacing
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        _r,_g,_b = tuple(int(c * 255) for c in rgb)
        colors.append(f"#{_r:02x}{_g:02x}{_b:02x}")
    return colors

def create_color_scale(filling_level, max_level, _color1=(0, 0, 255), _color2=(255, 0, 0)):
    """
    Returns the color value for filling_level in the gradient [_color1, _color2].
    filling_level must be in [0, max_level].
    """
    ratio = max(0, min(1, filling_level / max_level))  # Clamp entre 0 et 1

    r1, g1, b1 = _color1
    r2, g2, b2 = _color2

    interpolated_r = int(max(0, min(255, r1 + ratio * (r2 - r1))))
    interpolated_g = int(max(0, min(255, g1 + ratio * (g2 - g1))))
    interpolated_b = int(max(0, min(255, b1 + ratio * (b2 - b1))))

    return f"#{interpolated_r:02x}{interpolated_g:02x}{interpolated_b:02x}"
