import json
import logging

import ffmpeg

from ffmpeg_mcp.configs import setup_logging

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
	logger.info(f'Extracting metadata for {input_video_path}')
	video_metadata = ffmpeg.probe(input_video_path)
	logger.info('Metadata extracted...')
	return json.dumps(video_metadata, indent=2)
