import json
import logging

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message

setup_logging()
logger = logging.getLogger(__name__)


def get_video_metadata(input_video_path: str):
	"""
	Function to extract metadata of the given input video.

	Params:
		input_video_path (str): Path to the input video.

	Returns:
		JSON of the video metadata.
	"""
	try:
		logger.info(f'Extracting metadata for {input_video_path}')
		video_metadata = ffmpeg.probe(input_video_path)
		logger.info('Metadata extracted...')
		return json.dumps(video_metadata, indent=2)
	except ffmpeg._run.Error as e:
		return build_exception_message(error_type=ffmpeg._run.Error, message=f'FFmpeg command failed: {e.stderr.decode("utf-8")}')
	except Exception as e:
		return build_exception_message(error_type=Exception, message=f'Unexpected error: {str(e)}')

