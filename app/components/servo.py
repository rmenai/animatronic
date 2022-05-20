import math
from typing import Tuple

import pygame
from pygame import Rect, Surface
from pygame.font import Font

from app.core import constants
from app.state import state
from app.utils.ui import draw_pie, draw_triangle


class Handle:
    """Represents the handle of the servo."""

    def __init__(self, pos: Tuple[int, int]):
        self.image = pygame.image.load(constants.images.handle)
        self.width, self.height = self.image.get_size()

        # Define the coordinates of required points.
        self.pos = pos
        self.pivot = (self.pos[0] + self.width * constants.handle.pivot_multiplier, self.pos[1])
        self.origin = (constants.handle.origin_start, self.image.get_height() // 2)

        # Geometry properties.
        self.rotated_image, self.rect = self.image, self.image.get_rect()

        # Point properties.
        self.last_angle_clicked = False
        self.last_point_angle = 0
        self.last_point_rect = Rect(0, 0, 0, 0)
        self.new_angle = False

        # Angle properties.
        self.last_range_surface: str = ""
        self.new_angle = False

    def update(self, angle: int) -> None:
        """Rotates the handle around the pivot point by the given angle."""
        # Convert to arduino rotations.
        angle -= 90

        handle_rect = self.image.get_rect(topleft=(self.pivot[0] - self.origin[0], self.pivot[1] - self.origin[1]))
        offset_center_to_pivot = pygame.math.Vector2(self.pivot) - handle_rect.center

        # Rotated offset from pivot to center.
        rotated_offset = offset_center_to_pivot.rotate(-angle)
        rotated_image_center = (self.pivot[0] - rotated_offset.x, self.pivot[1] - rotated_offset.y)

        # Get a rotated image.
        self.rotated_image = pygame.transform.rotate(self.image, angle)
        self.rect = self.rotated_image.get_rect(center=rotated_image_center)

    def render(self, surface: Surface) -> None:
        """Renders the handle on the given surface."""
        surface.blit(self.rotated_image, self.rect)

        if pygame.mixer.music.get_busy():
            # Create a center square of size 200x200 around the handle.
            rect = Rect(
                self.pos[0] - self.image.get_width() // 2, self.pos[1] - constants.handle.hitbox[1] // 2,
                constants.handle.hitbox[0] * 2, constants.handle.hitbox[1]
            )

            if not rect.collidepoint(state.mouse_pos):
                return

        # Geometry values.
        pivot = self.pivot[0] - self.origin[0], self.pivot[1]
        radius, draw_width = self.width + 2, (self.width + 2) / constants.handle.draw_width_multiplier

        # Draw a pie from the pivot point using the rotation range.
        surf = draw_pie(radius, constants.handle.pie_color, *state.rotations_range)
        surface.blit(surf, (pivot[0] - radius, pivot[1] - radius))

        # Draw the pie's border.
        surf = draw_pie(
            radius, constants.handle.pie_border_color,
            *state.rotations_range, width=constants.handle.pie_border_width
        )
        surface.blit(surf, (pivot[0] - radius, pivot[1] - radius))

        # Calculate the coordinates of the rotation range start and end
        pos_up: Tuple[int, int] = (
            int(pivot[0] + math.cos(math.radians(state.rotations_range[1] - 90)) * radius),
            int(pivot[1] - math.sin(math.radians(state.rotations_range[1] - 90)) * radius)
        )

        pos_down: Tuple[int, int] = (
            int(pivot[0] + math.cos(math.radians(state.rotations_range[0] - 90)) * radius),
            int(pivot[1] - math.sin(math.radians(state.rotations_range[0] - 90)) * radius)
        )

        # Draw triangles to fill the gap between the pie and the border.
        surf = draw_triangle(constants.handle.triangle_color, pivot, (pivot[0], pivot[1] + self.origin[1]), pos_down)
        surface.blit(surf, (0, 0))

        surf = draw_triangle(constants.handle.triangle_color, pivot, (pivot[0], pivot[1] - self.origin[1]), pos_up)
        surface.blit(surf, (0, 0))

        # Draw the rotation range selectors.
        range_surfaces = (
            draw_pie(
                draw_width, constants.handle.range_surfaces_color,
                95 + state.rotations_range[0], 180 + state.rotations_range[0]
            ),
            draw_pie(
                draw_width, constants.handle.range_surfaces_color,
                0 - (180 - state.rotations_range[1]), 85 - (180 - state.rotations_range[1])
            )
        )

        # Draw the allowed angles onto the surface.
        for angle in state.allowed_rotations:
            if state.rotations_range[0] <= angle <= state.rotations_range[1]:
                # Calculate the coordinates of the angles on the circle.
                pos = (
                    pivot[0] + math.cos(math.radians(angle - 90)) * radius,
                    pivot[1] - math.sin(math.radians(angle - 90)) * radius
                )
                pygame.draw.circle(surface, constants.handle.point_color, pos, 3)

        # Change the rotation ranges if the mouse is pressed.
        if state.holding_mouse:
            if self.last_range_surface == "up":
                # Get angle from mouse position to pivot point.
                angle = math.degrees(math.atan2(state.mouse_pos[1] - pivot[1], state.mouse_pos[0] - pivot[0])) + 90
                # Round the angle to the nearest point on the circle.
                if state.rotations_range[0] + constants.handle.range_gap < 180 - angle < 180:
                    if int(180 - angle) > 176:
                        state.rotations_range = (state.rotations_range[0], 180)
                    else:
                        for allowed_angle in state.allowed_rotations:
                            if abs(int(180 - angle) - allowed_angle) <= 5:
                                state.rotations_range = (state.rotations_range[0], allowed_angle)
                                break
                        else:
                            state.rotations_range = (state.rotations_range[0], int(180 - angle))

            elif self.last_range_surface == "down":
                # Get angle from mouse position to pivot point.
                angle = math.degrees(math.atan2(state.mouse_pos[1] - pivot[1], state.mouse_pos[0] - pivot[0])) + 90
                # Round the angle to the nearest point on the circle.
                if 0 < 180 - angle < state.rotations_range[1] - constants.handle.range_gap:
                    if int(180 - angle) < 4:
                        state.rotations_range = (0, state.rotations_range[1])
                    else:
                        for allowed_angle in state.allowed_rotations:
                            if abs(int(180 - angle) - allowed_angle) <= 5:
                                state.rotations_range = (allowed_angle, state.rotations_range[1])
                                break
                        else:
                            state.rotations_range = (int(180 - angle), state.rotations_range[1])

            # Add or remove allowed rotation if mouse is clicked.
            elif self.last_point_rect.collidepoint(state.mouse_pos) and not self.last_angle_clicked:
                self.last_angle_clicked = True  # Prevent adding the same angle twice.
                self.new_angle = False  # Reset the new angle flag.

                if self.last_point_angle in state.allowed_rotations:
                    state.allowed_rotations.remove(self.last_point_angle)
                else:
                    state.allowed_rotations.append(self.last_point_angle)
        else:
            # Check if the mouse is in the rotation range surfaces.
            if range_surfaces[1].get_rect(
                    topleft=(pos_up[0] - draw_width, pos_up[1] - draw_width)
            ).collidepoint(state.mouse_pos):
                range_surfaces[1].set_alpha(constants.handle.range_alpha)
                self.last_range_surface = "up"

            elif range_surfaces[0].get_rect(
                    topleft=(pos_down[0] - draw_width, pos_down[1] - draw_width)
            ).collidepoint(state.mouse_pos):
                range_surfaces[0].set_alpha(constants.handle.range_alpha)
                self.last_range_surface = "down"
            else:
                # Show the closest point on the circle to the mouse.
                self.last_range_surface = ""
                self.last_angle_clicked = False
                # Get the closest point in circle to mouse position.
                angle = -math.degrees(math.atan2(state.mouse_pos[1] - pivot[1], state.mouse_pos[0] - pivot[0])) + 90

                # Make angle multiple of 5.
                angle = int((angle // constants.handle.angle_multiple) * constants.handle.angle_multiple)
                if state.rotations_range[0] <= angle <= state.rotations_range[1]:
                    # Calculate the coordinates of the point on the circle.
                    pos = (
                        pivot[0] + math.cos(math.radians(angle - 90)) * radius,
                        pivot[1] - math.sin(math.radians(angle - 90)) * radius
                    )

                    # Draw circle at pos.
                    rect = Rect(
                        pos[0] - constants.handle.point_hitbox / 2, pos[1] - constants.handle.point_hitbox / 2,
                        constants.handle.point_hitbox, constants.handle.point_hitbox)
                    if rect.collidepoint(state.mouse_pos):
                        surf = Surface((constants.handle.point_radius * 2, constants.handle.point_radius * 2))
                        surf.set_colorkey((255, 255, 255))

                        if angle != self.last_point_angle:
                            self.new_angle = True

                        if angle in state.allowed_rotations and self.new_angle:
                            surf.set_colorkey((0, 0, 0))
                            pygame.draw.circle(
                                surf, constants.handle.delete_point_color,
                                (constants.handle.point_radius, constants.handle.point_radius),
                                constants.handle.point_radius
                            )
                        else:
                            pygame.draw.circle(
                                surf, (255, 255, 255),
                                (constants.handle.point_radius, constants.handle.point_radius),
                                constants.handle.point_radius
                            )

                        surface.blit(
                            surf, (pos[0] - constants.handle.point_radius, pos[1] - constants.handle.point_radius)
                        )

                        # Render angle text.
                        font = Font(constants.handle.font, constants.handle.font_size)
                        text = font.render(str(angle), True, constants.handle.font_color)
                        text_rect = text.get_rect()
                        text_rect.center = (pos[0], pos[1] + constants.handle.font_size)
                        surface.blit(text, text_rect)

                        self.last_point_angle = angle
                        self.last_point_rect = rect

                    else:
                        self.new_angle = False

                    self.last_point_rect = Rect(
                        pos[0] - constants.handle.point_hitbox / 2, pos[1] - constants.handle.point_hitbox / 2,
                        constants.handle.point_hitbox, constants.handle.point_hitbox
                    )
                    self.last_point_angle = angle

        # Draw the rotation range surfaces.
        surface.blit(range_surfaces[0], (pos_down[0] - draw_width, pos_down[1] - draw_width))
        surface.blit(range_surfaces[1], (pos_up[0] - draw_width, pos_up[1] - draw_width))


class Servo:
    """Represents the servo on the window containing 2 separate images, one for the servo and one for the handle."""

    def __init__(self, pos: Tuple[int, int]):
        self.image = pygame.image.load(constants.images.servo)

        # Define the coordinates of required points.
        self.pos = (pos[0], pos[1] - self.image.get_height() // 2)

        # Initialize the handle.
        self.handle = Handle((
            self.pos[0] + self.image.get_width() * constants.handle.servo_multiplier,
            self.pos[1] + self.image.get_height() // 2
        ))

    def update(self, angle: int) -> None:
        """Updates the handle's angle."""
        self.handle.update(angle)

    def render(self, screen: Surface) -> None:
        """Renders the handle to the given surface."""
        screen.blit(self.image, self.pos)
        self.handle.render(screen)
