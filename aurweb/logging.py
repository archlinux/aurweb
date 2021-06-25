import logging
import logging.config
import os

import aurweb.config

aurwebdir = aurweb.config.get("options", "aurwebdir")
config_path = os.path.join(aurwebdir, "logging.conf")

logging.config.fileConfig(config_path, disable_existing_loggers=False)
logger = logging.getLogger(__name__)
