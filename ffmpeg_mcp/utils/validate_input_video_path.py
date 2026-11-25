import logging
import os
import subprocess
from functools import wraps

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message

setup_logging()
logger = logging.getLogger(__name__)


def validate_input_video_path(func):
	"""
	Decorator to check if the video path exists, is non-empty, and is valid.
	"""

	@wraps(func)
	def wrapper(input_video_path, *args, **kwargs):
		if not os.path.isfile(input_video_path):
			return build_exception_message(error_type=FileNotFoundError, message=f'File not found: {input_video_path}')
		if os.path.getsize(input_video_path) == 0:
			return build_exception_message(error_type=ValueError, message=f'File is empty: {input_video_path}')

		try:
			subprocess.run(
				['ffprobe', '-v', 'error', '-show_streams', '-select_streams', 'v', input_video_path],
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL,
				check=True,
			)
		except subprocess.CalledProcessError:
			return build_exception_message(error_type=ValueError, message=f'File is not a valid video: {input_video_path}')

		return func(input_video_path, *args, **kwargs)

	return wrapper
