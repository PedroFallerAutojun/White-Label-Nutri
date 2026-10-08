from config.settings.base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedStaticFilesStorage"
