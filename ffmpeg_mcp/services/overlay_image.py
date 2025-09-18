import logging
import os
from pathlib import Path
from typing import Literal

import ffmpeg

from ffmpeg_mcp.configs.logging_config import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from utils import validate_input_video_path

setup_logging()
logger = logging.getLogger(__name__)


CURR_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGE_OVERLAY_PATH = os.path.join(CURR_PATH, '..', 'processed_elements', 'image_overlays')

os.makedirs(IMAGE_OVERLAY_PATH, exist_ok=True)


@validate_input_video_path
def overlay_image(
	input_video_path: str,
	overlay_image_path: str,
	output_filename: str = 'output.mp4',
	positioning: Literal['top_left', 'top_right', 'bottom_left', 'bottom_right', 'center', 'top_center', 'bottom_center'] = 'top_right',
	scale: tuple | None = (100, 100),
	keep_audio: bool = True,
	opacity: float | None = None,
	start_time: float = 0.0,
	duration: float | None = None,
) -> str:
	"""
	Overlay an image on top of a video with timing control.

	Args:
	    input_video_path (str): Path to background video.
	    overlay_image_path (str): Path to image file.
	    output_filename (str): Output video filename (saved inside VIDEO_OVERLAY_PATH).
	    positioning (Literal): Where to place overlay.
	    scale (tuple | None): (width, height) to resize image before placing.
	    keep_audio (bool): Whether to keep background audio.
	    opacity (float | None): Transparency level (0–1). None = no alpha applied.
	    start_time (float): When to start showing overlay (seconds).
	    duration (float | None): How long to show overlay (seconds). None = until end of video.

	Returns:
	    str: Path to generated video.
	"""
	input_video = Path(input_video_path)
	overlay_image = Path(overlay_image_path)
	output = Path(IMAGE_OVERLAY_PATH) / output_filename

	if not overlay_image.exists():
		return build_exception_message(error_type=FileNotFoundError, message=f'Overlay image not found at path {overlay_image_path}')

	logger.info(f'Processing overlay: {input_video} + {overlay_image} -> {output}')

	probe = ffmpeg.probe(str(input_video))
	video_duration = float(probe['format']['duration'])

	if start_time < 0.0:
		logger.error('Start time negative')
		return build_exception_message(error_type=ValueError, message='Start time must be greater than 0.0 seconds')
	if duration is not None:
		if duration <= 0.0:
			logger.error('Overlay Duration value cannot be 0 or less')
			return build_exception_message(error_type=ValueError, message='Duration for overlay must be greater than 0 seconds')
		if start_time + duration > video_duration:
			logger.error('Overlay duration greater than the video duration')
			return build_exception_message(
				error_type=ValueError, message='Duration for overlay cannot be greater than the video duration'
			)

	bg_stream = ffmpeg.input(str(input_video))
	ov_stream = ffmpeg.input(str(overlay_image), loop=1)

	if scale:
		ov_stream = ffmpeg.filter(ov_stream, 'scale', scale[0], scale[1])

	if opacity is not None:
		ov_stream = ov_stream.filter('format', 'rgba').filter('colorchannelmixer', aa=opacity)

	positions = {
		'top_left': ('10', '10'),
		'top_right': ('W-w-10', '10'),
		'bottom_left': ('10', 'H-h-10'),
		'bottom_right': ('W-w-10', 'H-h-10'),
		'center': ('(W-w)/2', '(H-h)/2'),
		'top_center': ('(W-w)/2', '10'),
		'bottom_center': ('(W-w)/2', 'H-h-10'),
	}

	if positioning not in positions:
		return build_exception_message(error_type=ValueError, message=f'Invalid positioning : {positioning}')

	x, y = positions[positioning]

	if duration is None:
		enable_expr = f'gte(t,{start_time})'
	else:
		end_time = start_time + duration
		enable_expr = f'between(t,{start_time},{end_time})'

	video = ffmpeg.overlay(
		bg_stream.video,
		ov_stream,
		x=x,
		y=y,
		enable=enable_expr,
		shortest=1,
	)

	if keep_audio:
		audio = bg_stream.audio
		out = ffmpeg.output(video, audio, str(output))
	else:
		out = ffmpeg.output(video, str(output))

	out.run(overwrite_output=True, quiet=True)
	logger.info(f'Overlay complete: {output}')

	return str(output)


# if __name__ == "__main__":
#     overlay_image(
#         input_video_path=r"C:\Users\aayus\Downloads\07a1cc329f74427c9e9daf94afed9749.mov",
#         overlay_image_path=r"C:\Users\aayus\Pictures\Screenshots\Screenshot 2025-09-09 185855.png",
#         output_filename="overlaid.mp4",
#         start_time=10.5,
#         duration=5.5,
#         positioning="center",
#         opacity=0.8
#     )
