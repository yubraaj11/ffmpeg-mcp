import logging

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from utils import validate_input_video_path

setup_logging()
logger = logging.getLogger(__name__)


@validate_input_video_path
def get_video_duration(input_video_path: str) -> float:
	"""
	Calculates the duration of a video.

	Args:
	    input_video_path (str): Path to the video file.

	Returns:
	    float: Duration of the video in seconds (including milliseconds), formatted as SS.ss.
	"""
	try:
		probe = ffmpeg.probe(input_video_path)
		duration = float(probe['format']['duration'])
		return duration
	except Exception as e:
		logger.error('Error in calculating duration of a video')
		build_exception_message(error_type=Exception, message=f'Error in calculating duration: {str(e)}')
		


