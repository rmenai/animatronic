from appdirs import user_cache_dir


class Global:
    """The app settings."""

    # Paths.
    cache_path: str = user_cache_dir("AnimatronicControl")
    resources_path: str = "data"


settings = Global()
