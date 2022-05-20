import logging.handlers

from app.core import settings

# Console handler prints to terminal.
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Format configuration.
fmt = "%(asctime)s - %(name)s %(levelname)s: %(message)s"
datefmt = "%H:%M:%S"

# Add colors for logging if available.
try:
    from colorlog import ColoredFormatter

    console_handler.setFormatter(
        ColoredFormatter(fmt=f"%(log_color)s{fmt}", datefmt=datefmt))
except ModuleNotFoundError:
    pass

# Remove old loggers, if any.
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

# Silence irrelevant loggers.
# logging.getLogger("asyncio").setLevel(logging.ERROR)

# Setup new logging configuration.
logging.basicConfig(
    format=fmt,
    datefmt=datefmt,
    level=logging.DEBUG,
    handlers=[console_handler]
)
