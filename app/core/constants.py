from itertools import cycle
from pathlib import Path

from app.core.config import settings


class Animations:
    """The animations used in the app."""

    loading = cycle(sorted(Path(f"{settings.resources_path}/images/loading").glob('*.gif'), key=lambda x: x.stem))


class Arduino:
    """The arduino board settings."""

    pos = (400, 25)


class Audio:
    """The audio settings."""

    supported_formats = ["mp3", "wav", "ogg"]

    baud_rate = 9600


class Colors:
    """The colors used in the app."""

    black = (0, 0, 0)
    light_black = (37, 48, 53)
    white = (255, 255, 255)

    green = (0, 255, 0)
    dark_green = (0, 128, 0)
    red = (255, 0, 0)


class Fonts:
    """The fonts used in the app."""

    roboto_bold = Path(f"{settings.resources_path}/fonts/Roboto-Bold.ttf")


class Handle:
    """The handle settings."""

    # Positions and multipliers.
    draw_width_multiplier = 6
    pivot_multiplier = 0.15
    servo_multiplier = 0.8
    origin_start = 16

    # Colors and width.
    pie_border_width = 3
    pie_border_color = (*Colors.green, 40)  # (r, g, b, a)
    pie_color = (*Colors.green, 40)

    triangle_color = (*Colors.red, 40)
    range_surfaces_color = (*Colors.green, 60)
    point_color = Colors.dark_green
    delete_point_color = Colors.red

    # Other settings.
    angle_multiple = 5
    range_gap = 30
    range_alpha = 100

    font = Fonts.roboto_bold
    font_color = Colors.light_black
    font_size = 16

    point_radius = 3
    point_hitbox = 100
    hitbox = (150, 350)


class Images:
    """The images used in the app."""

    drop = Path(f"{settings.resources_path}/images/drop.png")
    handle = Path(f"{settings.resources_path}/images/handle.png")
    servo = Path(f"{settings.resources_path}/images/servo.png")

    enter = Path(f"{settings.resources_path}/images/enter.png")
    cable = Path(f"{settings.resources_path}/images/cable.png")
    rob = Path(f"{settings.resources_path}/images/icon.ico")


class Window:
    """The window settings."""

    size = (940, 400)
    title = "Animatronic Control"
    fps = 60


class Visualizer:
    """The audio visualizer settings."""

    size = (480, 300)
    pos = (150, 50)

    # Analyzer settings.
    frequency_range = (100, 8100)  # 100 frequencies jump.

    # Colors.
    background_color = (67, 78, 83)
    border_color = (191, 200, 200)
    border_color_dark = (67, 78, 83)
    border_color_even_dark = (52, 63, 68)
    bar_color = (47, 58, 63)

    # Other settings.
    drop_alpha = 100
    default_db = -80

    # Animations.
    loading_animation = Animations.loading
    loading_animation_speed = 0.03

    # Fonts.
    font = Fonts.roboto_bold
    font_color = (27, 38, 43)
    font_color_light = (47, 58, 63)
    font_size = 24

    # Slider.
    slider_width = 8
    slider_height = 2
    slider_text_offset = 5


class Constants:
    """The app constants."""

    animations = Animations()
    arduino = Arduino()
    audio = Audio()
    colours = colors = Colors()
    fonts = Fonts()
    handle = Handle()
    images = Images()
    window = Window()
    visualizer = Visualizer()


constants = Constants()
