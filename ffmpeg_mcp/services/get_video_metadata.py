import json
import logging

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from utils import validate_input_video_path

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
	return json.dumps(video_metadata, indent=2)


