import json
import logging

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message

# from ffmpeg_mcp.services import get_video_metadata
from ffmpeg_mcp.services.get_video_metadata import get_video_metadata

setup_logging()
logger = logging.getLogger(__name__)


def calculate_video_offset(input_video_path: str, transition_duration: float):
	"""
	Calculate the offset duration of the video
	Args:
	    input_video_path(str): takes the path of the input video in string format
	    transition_duration(float): takes the duration in second at which transition should be started
	Returns:
	    float: offset duration of the video in Seconds(including milliseconds)
	"""
	# video_duration = get_video_duration(input_video_path=input_video_path)
	metadata = get_video_metadata(input_video_path=input_video_path)
	video_duration = json.loads(metadata)['format']['duration']
	try:
		offset_duration = max(float(video_duration) - transition_duration, 0)
		return offset_duration
	except Exception as e:
		logger.error('Error in calculating offset duration')
		build_exception_message(error_type=Exception, message=f'Error in calculating offest duration: {str(e)}')
