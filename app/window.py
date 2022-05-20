import logging
from typing import Tuple

import pygame

from app.components import Arduino, AudioVisualizer, Servo
from app.core import constants
from app.state import state

log = logging.getLogger(__name__)

pygame.init()


class Window:
    """Represents the main pygame window."""

    def __init__(self, size: Tuple[int, int], title: str):
        """Initializes the window."""
        self.width, self.height = size
        self.title = title

        # Variables needed to run the main loop.
        self.clock = pygame.time.Clock()
        self.running = True
        self.screen = None

        # Components initiation.
        self.audio_visualizer = None
        self.servo = None
        self.arduino = None
        self.drop_down = None

    def run(self) -> None:
        """Initializes the window."""
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        pygame.display.set_icon(pygame.image.load(constants.images.rob))

        # Run the main loop.
        self.main()

    def main(self) -> None:
        """Updates the window."""
        # Initialize the components.
        self.arduino = Arduino(constants.arduino.pos)
        self.audio_visualizer = AudioVisualizer(constants.visualizer.pos, constants.visualizer.size, self.arduino)
        self.servo = Servo((
            constants.visualizer.pos[0] + constants.visualizer.size[0],
            constants.visualizer.pos[1] + constants.visualizer.size[1] // 2
        ))

        log.debug("Initialized all components.")

        t = pygame.time.get_ticks()
        get_ticks_last_frame = t

        while self.running:
            # Update time
            self.clock.tick(constants.window.fps)

            # Get the time since the last frame.
            t = pygame.time.get_ticks()
            delta_time = (t - get_ticks_last_frame) / 1000.0
            get_ticks_last_frame = t

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    self.running = False

                # Get angle from pivot to mouse position using atan2.
                if event.type == pygame.MOUSEBUTTONDOWN:
                    state.holding_mouse = True
                    log.debug("Mouse button down")
                elif event.type == pygame.MOUSEBUTTONUP:
                    state.holding_mouse = False
                    log.debug("Mouse button up")

                # Check if the user is dropping a file.
                if event.type == pygame.DROPFILE:
                    if not self.audio_visualizer.audio_file.file_path:
                        filename = event.file
                        log.info(f"Dropped file: {filename}")

                        # Load the file.
                        self.audio_visualizer.load_file(filename)

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                        if not self.audio_visualizer.audio_file.loading:
                            if self.audio_visualizer.audio_file.started:
                                self.audio_visualizer.audio_file.paused = not self.audio_visualizer.audio_file.paused

                                if self.audio_visualizer.audio_file.paused:
                                    # Pause the audio file.
                                    log.info("Pausing audio file")
                                    pygame.mixer.music.pause()
                                else:
                                    # Pause the audio file.
                                    log.info("Resuming audio file")
                                    pygame.mixer.music.unpause()
                            else:
                                # Play the audio file.
                                log.info("Playing audio file")
                                pygame.mixer.music.play(0)
                                self.audio_visualizer.audio_file.started = True

                    elif event.key in (pygame.K_ESCAPE, pygame.K_END, pygame.K_x, pygame.K_q):
                        if not self.audio_visualizer.audio_file.loading:
                            self.audio_visualizer.stop()

            # Update game state attributes.
            state.mouse_pos = pygame.mouse.get_pos()

            # Fill the background with white and surfaces.
            self.screen.fill(constants.colors.white)

            # Draw the servo.
            self.servo.update(state.angle)
            self.servo.render(self.screen)

            # Draw the audio visualizer.
            self.audio_visualizer.update(delta_time)
            self.audio_visualizer.render(self.screen)

            # Render animations if any.
            if state.loading:
                img = pygame.image.load(state.loading_frame)
                width, height = img.get_width(), img.get_height()

                # Render the loading animation on the surface.
                self.screen.blit(img, (
                    (self.audio_visualizer.width + self.audio_visualizer.pos[0] * 2) // 2 - width // 2,
                    (self.audio_visualizer.height + self.audio_visualizer.pos[1] * 2) // 2 - height // 2
                ))

            # Update the screen.
            pygame.display.flip()

    @staticmethod
    def close() -> None:
        """Closes the window."""
        # Save settings.
        state.save()
        log.info("Window closed")
