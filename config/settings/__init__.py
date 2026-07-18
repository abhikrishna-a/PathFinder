"""
Default settings shim — imports dev settings for local development.

Override with environment variable:
  DJANGO_SETTINGS_MODULE=config.settings.prod   (production)
  DJANGO_SETTINGS_MODULE=config.settings.test   (tests)
"""
from config.settings.dev import *  # noqa: F401, F403
