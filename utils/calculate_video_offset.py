import logging

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from utils import get_video_duration

setup_logging()
logger = logging.getLogger(__name__)


def calculate_video_offset(input_video_path: str, transition_duration: float) -> float:
	"""
	Calculate the offset duration of the video
	Args:
	    input_video_path(str): takes the path of the input video in string format
	    transition_duration(float): takes the duration in second at which transition should be started
	Returns:
	    float: offset duration of the video in Seconds(including milliseconds)
	"""
	video_duration = get_video_duration(input_video_path=input_video_path)
	try:
		offset_duration = max(video_duration - transition_duration, 0)
		return offset_duration
	except Exception as e:
		logger.error('Error in calculating offset duration')
		build_exception_message(error_type=Exception, message=f'Error in calculating offest duration: {str(e)}')

