import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

from app.core import settings

log = logging.getLogger(__name__)


class State:
    """Groups together the global state of the game."""

    def __init__(self):
        self.allowed_rotations: List[int] = []
        self.rotations_range: Tuple[int, int] = (0, 180)

        self.holding_mouse: bool = False
        self.mouse_pos: Tuple[int, int] = (0, 0)

        self.min_dbfs = -80
        self.max_dbfs = -45

        self.angle: int = 90
        self.db = -80
        self.cache_dir: str = f"{settings.cache_path}/default"

        # Load default profile.
        self.load()

        # Animations.
        self.loading: bool = False
        self.loading_frame: str = ""

    def load(self) -> None:
        """Load the servo's settings from the profile."""
        try:
            with open(f"{self.cache_dir}/profile.json", "r") as f:
                config = json.load(f)

                # Load profile settings.
                self.rotations_range = (config["rotations"]["min"], config["rotations"]["max"])
                self.allowed_rotations = config["rotations"]["allowed"]

                self.min_dbfs, self.max_dbfs = config["dbfs"]["min"], config["dbfs"]["max"]

            log.info(f"Loaded profile from {self.cache_dir}/profile.json")
        except FileNotFoundError:
            log.warning(f"Profile not found in {self.cache_dir}/profile.json, creating profile")
            self.save()

    def save(self) -> None:
        """Save the servo's angle to the given config."""
        # Create the cache directory if it doesn't exist.
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        with open(f"{self.cache_dir}/profile.json", "w") as f:
            json.dump({
                "rotations": {
                    "min": self.rotations_range[0],
                    "max": self.rotations_range[1],
                    "allowed": self.allowed_rotations
                },
                "dbfs": {
                    "min": self.min_dbfs,
                    "max": self.max_dbfs
                }
            }, f
            )

        log.info(f"Saved profile to {self.cache_dir}/profile.json")


state = State()

# Threading pool.
pool = ThreadPoolExecutor()
