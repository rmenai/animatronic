import logging

from app.core import constants
from app.window import Window

log = logging.getLogger(__name__)

# Initialize the window.
window = Window(constants.window.size, constants.window.title)
log.info("Window initialized")

window.run()
