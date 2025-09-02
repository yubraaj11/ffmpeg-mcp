import logging
import os
from typing import Literal
from uuid import uuid4

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from utils import validate_input_video_path

setup_logging()
logger = logging.getLogger(__name__)

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGE_OVERLAY_PATH = os.path.join(CURR_PATH, '..', 'processed_elements', 'image_overlays')

os.makedirs(IMAGE_OVERLAY_PATH, exist_ok=True)


@validate_input_video_path
def overlays_image(
	input_video_path: str, image_path: str, positioning: Literal['top_left', 'bottom_left', 'top_right', 'bottom_right'] = 'top_left'
) -> str:
	"""
	Overlay an image on a video at one of the four corners using ffmpeg-python.

	Args:
	    input_video_path (str): Path to the source video file.
	    image_path (str): Path to the image file to overlay.
	    positioning (Literal): Position of the overlay (top_left, bottom_left, top_right, bottom_right).
	                           Defaults to 'top_left'.

	Returns:
	    str: Path to the output video with overlay applied.
	"""
	logger.info('Starting image overlay process...')
	overlay_video_name = f'{os.path.basename(image_path).split(".")[0]}_ovr_img_{uuid4()}.mp4'
	overlay_video_path = os.path.join(IMAGE_OVERLAY_PATH, overlay_video_name)

	position_map = {
		'top_left': ('10', '10'),
		'bottom_left': ('10', 'main_h-overlay_h-10'),
		'top_right': ('main_w-overlay_w-10', '10'),
		'bottom_right': ('main_w-overlay_w-10', 'main_h-overlay_h-10'),
	}

	if positioning not in position_map:
		return build_exception_message(
			error_type=ValueError, message=f'Invalid positioning: {positioning}. Choose from {list(position_map.keys())}'
		)

	x, y = position_map[positioning]

	if not os.path.isfile(image_path):
		return build_exception_message(error_type=ValueError, message=f'File exists: {image_path}')
	if os.path.getsize(image_path) == 0:
		return build_exception_message(error_type=ValueError, message=f'File empty: {image_path}')

	try:
		(
			ffmpeg.input(input_video_path)
			.overlay(
				ffmpeg.input(image_path).filter('scale', 150, -1),  # scale logo to 100px width, keep aspect ratio
				x=x,
				y=y,
			)
			.output(overlay_video_path, c='libx264', preset='fast', crf=23, pix_fmt='yuv420p')
			.overwrite_output()
			.run(quiet=True)
		)
		logger.info('Finished image overlay process.')
		return overlay_video_path
	except ffmpeg.Error as e:
		return build_exception_message(error_type=ffmpeg.Error, message=f'FFmpeg error: {e.stderr.decode("utf-8")}')
	except Exception as e:
		return build_exception_message(error_type=RuntimeError, message=f'Unexpected error: {str(e)}')
