import logging

from ffmpeg_mcp.configs.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# Example usage of logging
logger.info('This is an info message.')
logger.warning('This is a warning message.')
logger.error('This is an error message.')