import gzip
import hashlib
import json
import logging
import os
import pickle
import shutil
import time
from typing import Tuple

import librosa
import numpy as np
import pygame
from pygame import Surface
from pygame.font import Font

from app.core import constants, settings
from app.state import pool, state
from app.utils.arduino import get_rotation
from app.utils.maths import clamp
from app.utils.ui import prompt_file

log = logging.getLogger(__name__)


class AudioBar:
    """Represents an audio bar in the audio visualizer."""

    def __init__(
            self, x: int, y: int, freq: int, color: Tuple[int, int, int],
            width: int = 50, min_height: int = 10, max_height: int = 100,
            min_decibel: int = constants.visualizer.default_db, max_decibel: int = 0
    ):
        # Define the positions of the bar.
        self.x, self.y, self.freq = x, y, freq
        self.color = color

        # Define the geometry of the bar.
        self.width, self.min_height, self.max_height = width, min_height, max_height
        self.height = min_height

        # Define required decibel ratios.
        self.min_decibel, self.max_decibel = min_decibel, max_decibel
        self.decibel_height_ratio = (self.max_height - self.min_height) / (self.max_decibel - self.min_decibel)

    def update(self, dt: float, decibel: int) -> None:
        """Updates the bar's height based on the given decibel value."""
        desired_height = decibel * self.decibel_height_ratio + self.max_height
        speed = (desired_height - self.height) / 0.1

        # Update the bar's height.
        self.height += speed * dt
        self.height = clamp(self.min_height, self.max_height, self.height)

    def render(self, surface: Surface) -> None:
        """Renders the handle on the given surface."""
        pygame.draw.rect(surface, self.color, (self.x, self.y + self.max_height - self.height, self.width, self.height))


class AudioVisualizer:
    """Represents an audio visualizer."""

    def __init__(self, pos: Tuple[int, int], size: Tuple[int, int], arduino: None):
        self.width, self.height = size
        self.pos = pos
        self.rect = pygame.Rect(*pos, *size)

        # Initialize the audio visualizer surface.
        self.surface = Surface(size)
        self.slider_surface = Surface((75 - 16, self.height))
        self.slider_surface.set_colorkey((0, 0, 0))

        self.image = pygame.image.load(constants.images.drop)
        self.enter_image = pygame.image.load(constants.images.enter)
        self.cable_image = pygame.image.load(constants.images.cable)

        # Required analysis variables.
        self.audio_file = AudioFile("")
        self.bars = []
        self.frequencies = np.arange(*constants.visualizer.frequency_range, 100)

        # Mouse.
        self.clicked = False

        # Initialize the bars.
        r = len(self.frequencies)

        width = self.width // r
        x = (self.width - width * r) // 2

        # Initialize the bars.
        for c in self.frequencies:
            self.bars.append(AudioBar(x, 0, c, constants.visualizer.bar_color, max_height=self.height, width=width))
            x += width

        # Initialize arduino component.
        self.arduino = arduino

        # Sizes.
        self.h_start, self.h_end = 0, self.height
        self.update_min_max(reverse=True)

    def update_min_max(self, reverse: bool = False) -> None:
        """Updates the slider surface."""
        ratio = self.bars[0].decibel_height_ratio

        if reverse:
            self.h_start = int(self.height - (state.max_dbfs * ratio + self.bars[0].max_height))
            self.h_end = int(self.height - (state.min_dbfs * ratio + self.bars[0].max_height))
        else:
            # Reverse equation from height to decibel.
            state.max_dbfs = int((self.height - self.bars[0].max_height - self.h_start) / ratio)
            state.min_dbfs = int((self.height - self.bars[0].max_height - self.h_end) / ratio)

    def update(self, dela_time: float) -> None:
        """Updates the visualizer with the given data."""
        db_average = 0
        for b in self.bars:
            # Update all the bars with available db.
            db = self.audio_file.get_decibel(pygame.mixer.music.get_pos() / 1000.0, b.freq)
            b.update(dela_time, db)

            db_average += db

        if self.audio_file.started and not self.audio_file.paused:
            # Calculate rotation based on db.
            db_average /= len(self.bars)
            rotation = get_rotation(db_average)

            state.angle = rotation  # Rotate the UI handle.
            state.db = db_average
            self.arduino.send(rotation)  # Rotate the IRL handle.

            # When the music finishes reset the analysis.
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

                # Reset variables.
                self.audio_file.started = False
                self.audio_file.paused = False
                self.audio_file.loading = False

                log.info("Resetting analysis")

    def stop(self) -> None:
        """Stops the visualizer."""
        pygame.mixer.music.stop()
        self.audio_file = AudioFile("")

        # Reset cache dir to default.
        state.cache_dir = f"{settings.cache_path}/default"

    def render_slider(self, surface: Surface, h: int, font_size: int) -> None:
        """Renders the slider on the given surface."""
        # Render horizontal lines representing the min and max db.
        m = 19
        for y in range(0, self.height + 1 + m * 2, m):
            if y - (m * 2 + 2) < self.h_start or y - (m * 2 + 2) > self.h_end:
                continue

            offset = (m * 2 + 2)
            w = constants.visualizer.slider_width
            if not (y / (m * 2)) % 2:
                w *= 1.75

            pygame.draw.line(
                surface, constants.visualizer.font_color,
                (0, y - offset), (w, y - offset),
                h
            )  # decibel * self.__decibel_height_ratio + self.max_height

            if not (y / (m * 2)) % 2:
                # Draw db level next to the line.
                db = int(y / self.bars[0].decibel_height_ratio)

                # Convert db to multiple of -10.
                db = int(db / 10) * 10

                font = Font(constants.visualizer.font, font_size)
                text = font.render(str(db), True, constants.visualizer.font_color)

                surface.blit(
                    text, (w + constants.visualizer.slider_text_offset, (y - offset - text.get_height() // 2)
                           ))

    def render(self, surface: Surface) -> None:
        """Renders the visualizer to the given surface."""
        # Render the visualizer surface.
        surface.blit(self.surface, self.pos)

        # Draw the cable.
        surface.blit(
            self.cable_image, ((
                self.pos[0] - self.cable_image.get_width(),
                self.pos[1] + (self.h_start + self.h_end) // 2 - self.cable_image.get_height() // 2
            ))
        )

        # Fill a black rectangle of the size of the visualizer.
        pygame.draw.rect(self.surface, constants.visualizer.background_color, (0, 0, self.width, self.height))
        self.surface.fill(constants.visualizer.background_color)

        # Draw a border around the visualizer.
        pygame.draw.rect(
            surface, constants.visualizer.border_color,
            (self.pos[0] - 8, self.pos[1] - 8, self.width + 16, self.height + 16),
            8, 20
        )

        if not self.audio_file.file_path:
            # Check if mouse is hovering over the visualizer.
            if self.rect.collidepoint(state.mouse_pos):
                if state.holding_mouse:
                    # Prompt the user to select a file.
                    filename = str(prompt_file())
                    self.load_file(filename)

                self.image.set_alpha(255)
            else:
                # Render the drop image.
                self.image.set_alpha(constants.visualizer.drop_alpha)

            self.surface.blit(self.image, (
                self.width // 2 - self.image.get_width() // 2,
                self.height // 2 - self.image.get_height() // 2))
        else:
            # Render the bars if a file is loaded.
            for b in self.bars:
                b.render(self.surface)

            if not self.audio_file.loading and not self.audio_file.started:
                font = Font(constants.visualizer.font, constants.visualizer.font_size)
                text = font.render("Press Enter to start", True, constants.visualizer.font_color)

                rect = text.get_rect()
                rect.center = ((self.width + self.pos[0] * 2) // 2, (self.height + self.pos[1] * 2) // 2)

                # Render the text.
                pygame.draw.rect(
                    surface, constants.visualizer.font_color_light,
                    (rect.x - 20, rect.y - 20, rect.width + 40, rect.height + 40),
                    border_radius=13
                )
                surface.blit(text, rect)

        if self.audio_file.paused:
            font = Font(constants.visualizer.font, constants.visualizer.font_size)
            text = font.render("Press Enter to resume", True, constants.visualizer.font_color)

            rect = text.get_rect()
            rect.center = ((self.width + self.pos[0] * 2) // 2, (self.height + self.pos[1] * 2) // 2)

            # Render the text.
            pygame.draw.rect(
                surface, constants.visualizer.font_color_light,
                (rect.x - 20, rect.y - 20, rect.width + 40, rect.height + 40),
                border_radius=13
            )
            self.surface.set_alpha(220)
            surface.blit(text, rect)
        else:
            self.surface.set_alpha(255)

        self.slider_surface = Surface((75 - 16, self.height))
        self.slider_surface.set_colorkey((0, 0, 0))
        slider_rect = pygame.Rect(0, self.h_start, 75, self.h_end)

        # Fill the border.
        pygame.draw.rect(
            self.slider_surface, constants.visualizer.border_color_dark,
            (0, self.h_start, 75, self.h_end - self.h_start),
        )

        # Draw the average db value.
        desired_height = state.db * self.bars[0].decibel_height_ratio + self.bars[0].max_height
        pygame.draw.rect(
            self.slider_surface, constants.visualizer.bar_color, (
                0, self.h_start + max((self.height - desired_height) - self.h_start, 0),
                75, self.h_end - (self.h_start + max((self.height - desired_height) - self.h_start, 0))
            )
        )

        # Render the vertical lines.
        self.render_slider(
            self.slider_surface, constants.visualizer.slider_height,
            int(constants.visualizer.font_size * 0.75)
        )

        surface.blit(self.slider_surface, (self.pos[0] - slider_rect.width - 25, self.pos[1]))

        # Draw the border.
        pygame.draw.rect(
            surface, constants.visualizer.border_color, (
                self.pos[0] - slider_rect.width - 25 - 8, (self.pos[1] + self.h_start) - 8,
                slider_rect.width, (self.h_end - self.h_start) + 16
            ), 8, 20
        )

        # Get top border and bottom border rect.
        top_border_rect = pygame.Rect(0, 0, slider_rect.width, 64)
        top_border_rect.center = (
            (self.pos[0] - slider_rect.width - 25 - 8) + (slider_rect.width // 2),
            self.pos[1] + self.h_start
        )

        bottom_border_rect = pygame.Rect(0, 0, slider_rect.width, 64)
        bottom_border_rect.center = (
            (self.pos[0] - slider_rect.width - 25 - 8) + (slider_rect.width // 2),
            self.pos[1] + self.h_end
        )

        # Check if mouse is in top border.
        if top_border_rect.collidepoint(state.mouse_pos):
            if state.holding_mouse:
                current = self.pos[1] - 8 + self.h_start
                add_h = state.mouse_pos[1] - current

                if self.h_start + add_h < 0:
                    add_h = 0 - self.h_start

                if self.h_start + add_h + 70 <= self.h_end:
                    self.h_start += add_h
                    self.update_min_max()

        elif bottom_border_rect.collidepoint(state.mouse_pos):
            if state.holding_mouse:
                current = self.pos[1] - 8 + self.h_end
                add_h = state.mouse_pos[1] - current

                if self.h_end + add_h > self.height:
                    add_h = self.height - self.h_end

                if self.h_end + add_h - 70 >= self.h_start:
                    self.h_end += add_h
                    self.update_min_max()

        # Check if mouse is clicked in self.surface.
        if not state.holding_mouse:
            self.clicked = False

        if self.rect.collidepoint(state.mouse_pos):
            if state.holding_mouse and not self.clicked:
                if not self.audio_file.loading:
                    if self.audio_file.started:
                        self.audio_file.paused = not self.audio_file.paused

                        if self.audio_file.paused:
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
                        self.audio_file.started = True

                self.clicked = True

        if self.audio_file.cached:
            self.update_min_max(reverse=True)
            self.audio_file.cached = False

    def load_file(self, file_path: str) -> None:
        """Loads the given audio file."""
        # Check if the file is a valid audio file.
        if not file_path.rsplit(".", 1)[1] in constants.audio.supported_formats:
            return

        # Load the audio file.
        self.audio_file = AudioFile(file_path)
        pool.submit(self.audio_file.load)  # Load the audio file in a thread.
        pool.submit(self.loading_animation)  # Start the loading animation.

    def loading_animation(self) -> None:
        """Renders the loading animation."""
        # Define the loading animation.
        animation = constants.visualizer.loading_animation
        state.loading = True

        while self.audio_file.loading:
            # Set next animation frame.
            state.loading_frame = next(animation)
            time.sleep(constants.visualizer.loading_animation_speed)

        # Stop the loading animation.
        state.loading = False


class AudioFile:
    """Represents an audio file."""

    def __init__(self, file_path: str):
        """Initializes the audio file."""
        self.file_path = file_path
        self.started = False
        self.paused = False
        self.loading = True
        self.cached = False

        # Analytics settings.
        self.frequencies_index_ratio = 1
        self.time_index_ratio = 1
        self.spectrogram = []

    def get_decibel(self, target_time: float, freq: float) -> int:
        """Gets the decibel of the given frequency at the given time."""
        try:
            return self.spectrogram[int(freq * self.frequencies_index_ratio)][int(target_time * self.time_index_ratio)]
        except IndexError:
            return constants.visualizer.default_db

    def load(self) -> None:
        """Loads the audio file."""
        # Set the loading flag.
        self.loading = True

        with open(self.file_path, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)

        # Save current profile.
        state.save()

        file_hash = file_hash.hexdigest()
        state.cache_dir = f"{settings.cache_path}/{file_hash}"

        try:
            with gzip.open(f"{state.cache_dir}/spectrogram.xz", "rb") as f:
                self.spectrogram = pickle.load(f)

            with open(f"{state.cache_dir}/ratios.json", "r") as f:
                ratios = json.load(f)

                self.time_index_ratio = ratios["time_index_ratio"]
                self.frequencies_index_ratio = ratios["frequencies_index_ratio"]

            # Load the file profile.
            state.load()
            self.cached = True

        except (FileNotFoundError, TypeError, EOFError):
            log.warning("No cache found for this file, generating...")
            time_series, sample_rate = librosa.load(self.file_path)
            stft = np.abs(librosa.stft(time_series, hop_length=512, n_fft=2048 * 4))

            # Spectrogram and frequencies.
            self.spectrogram = librosa.amplitude_to_db(stft, ref=np.max)
            frequencies = librosa.core.fft_frequencies(n_fft=2048 * 4)

            # Ratios.
            times = librosa.core.frames_to_time(np.arange(self.spectrogram.shape[1]), sr=sample_rate, hop_length=512,
                                                n_fft=2048 * 4)
            self.time_index_ratio = len(times) / times[len(times) - 1]
            self.frequencies_index_ratio = len(frequencies) / frequencies[len(frequencies) - 1]

            pool.submit(self.cache)

        pygame.mixer.music.load(self.file_path)

        # End the loading flag.
        self.loading = False

    def cache(self) -> None:
        """Saves the audio file."""
        if not os.path.exists(state.cache_dir):
            os.makedirs(state.cache_dir)

        with gzip.open(f"{state.cache_dir}/spectrogram.xz", "wb") as f:
            pickle.dump(self.spectrogram, f)

        with open(f"{state.cache_dir}/ratios.json", "w") as f:
            json.dump({
                "time_index_ratio": self.time_index_ratio,
                "frequencies_index_ratio": self.frequencies_index_ratio
            }, f)

        # Move the file to the cache directory.
        recent_dir = f"{settings.cache_path}/recent"
        if not os.path.exists(recent_dir):
            os.makedirs(recent_dir)

        try:
            shutil.copy(self.file_path, f"{settings.cache_path}/recent/{os.path.basename(self.file_path)}")
            log.info(f"Moved {self.file_path} to recent directory")
        except shutil.SameFileError:
            log.warning(f"{self.file_path} is already in recent directory")
