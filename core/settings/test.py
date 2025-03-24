"""Settings module for core tests."""

import logging

from core.settings.base import *

logger = logging.getLogger(__name__)

try:
    from core.settings.local import *
except ModuleNotFoundError:
    logger.warning('Local settings file not initialized yet.')

SKIP_ACTIVATION = True
IS_EMAIL_SENDING_ENABLED = False

INITIAL_AGREEMENT_TYPE_NAMES = []

ACTIVATION_EMAIL_TOKEN_EXPIRY_TIME = 3600