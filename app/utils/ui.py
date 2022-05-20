import math
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askopenfilename
from typing import Tuple

import pygame
from pygame import Surface

from app.core import constants, settings


def draw_pie(radius: int, color: tuple, start_angle: int, end_angle: int, width: int = 0) -> Surface:
    """Draw a pie shape."""
    start_angle_raw = start_angle
    end_angle_raw = end_angle

    # Convert angles to arduino angles.
    end_angle = (180 - start_angle_raw) - 90
    start_angle = (180 - end_angle_raw) - 90

    # Calculate the points of the pie.
    start_angle = start_angle * 2 * math.pi / 360
    end_angle = end_angle * 2 * math.pi / 360
    points = [(radius, radius)]

    for i in range(0, 101):
        angle = end_angle + (start_angle - end_angle) * i / 100
        points.append((radius + radius * math.cos(angle), radius + radius * math.sin(angle)))

    # Fill the pie with alpha color in a new surface.
    surf = Surface((radius * 2 + width, radius * 2 + width))
    surf.set_colorkey((0, 0, 0))
    if len(color) == 4:
        surf.set_alpha(color[3])

    # Draw the pie.
    pygame.draw.polygon(surf, color, points, width=width)
    return surf


def draw_triangle(color: tuple, a: Tuple[int, int], b: Tuple[int, int], c: Tuple[int, int]) -> Surface:
    """Draw a triangle."""
    # Fill the triangle with alpha color in a new surface.
    surf = Surface(constants.window.size)
    surf.set_colorkey((0, 0, 0))
    if len(color) == 4:
        surf.set_alpha(color[3])

    # Draw the triangle and return the surface.
    pygame.draw.polygon(surf, color, [a, b, c])
    return surf


def prompt_file() -> Path:
    """Create a TK file dialog."""
    root = tk.Tk()
    root.withdraw()

    # Get a string of supported extensions in the following format: "*.ext1 *.ext2"
    supported_extensions = " ".join(["*." + ext for ext in constants.audio.supported_formats])

    # Create a file dialog and destroy it after the user selects a file.
    filename = askopenfilename(
        filetypes=[("Music files", supported_extensions), ("All Files", "*.*")],
        initialdir=f"{settings.cache_path}/recent",
    )
    root.destroy()

    if filename:
        return Path(filename)

    return Path("")
