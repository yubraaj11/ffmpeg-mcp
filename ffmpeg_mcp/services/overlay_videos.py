import logging
import os
from uuid import uuid4

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from utils import validate_input_video_path

setup_logging()
logger = logging.getLogger(__name__)

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
VIDEO_OVERLAY_PATH = os.path.join(CURR_PATH, '..', 'processed_elements', 'video_overlays')

os.makedirs(VIDEO_OVERLAY_PATH, exist_ok=True)


@validate_input_video_path
def overlay_videos(
	input_videos: list,
	mode: str = 'pip',  # "pip", "full_scale", "full_width", "stack_vertical"
	position: str = 'top_right',  # for pip mode
	mute_overlay: bool = True,
	overlay_scale: tuple = (320, 240),  # default PiP size
):
	"""
	Overlay videos in different styles using ffmpeg-python.

	Args:
	    input_videos (list): list of input video paths (at least 2 for overlay, 3 for vertical stack).
	    output_path (str): final output video path.
	    mode (str): overlay mode. Options: "pip", "full_scale", "full_width", "stack_vertical".
	    position (str): position for PiP. Options: top_left, top_right, bottom_left, bottom_right.
	    mute_overlay (bool): mute overlay video(s) or keep audio.
	    overlay_scale (tuple): (width, height) for PiP overlay video.
	"""
	logger.info('Starting image overlay process...')
	overlay_video_name = f'{os.path.basename(input_videos[0]).split(".")[0]}_ov_vid_{uuid4()}.mp4'
	overlay_video_path = os.path.join(VIDEO_OVERLAY_PATH, overlay_video_name)
	try:
		if not input_videos or len(input_videos) < 2:
			return build_exception_message(ValueError, 'At least 2 videos are required for overlay.')

		# Load main input
		main = ffmpeg.input(input_videos[0])

		if mode == 'pip':
			overlay = ffmpeg.input(input_videos[1])

			# Scale overlay to defined size
			overlay = overlay.filter('scale', overlay_scale[0], overlay_scale[1])

			# Position mapping
			position_map = {
				'top_left': (10, 10),
				'top_right': 'main_w-overlay_w-10:10',
				'bottom_left': '10:main_h-overlay_h-10',
				'bottom_right': 'main_w-overlay_w-10:main_h-overlay_h-10',
			}
			pos = position_map.get(position, '10:10')

			# Overlay
			video = ffmpeg.overlay(main, overlay, x=pos.split(':')[0], y=pos.split(':')[1])

			# Audio handling
			if mute_overlay:
				audio = main.audio
			else:
				audio = ffmpeg.filter([main.audio, overlay.audio], 'amix', inputs=2)

			out = ffmpeg.output(video, audio, overlay_video_path)

		elif mode == 'full_scale':
			overlay = ffmpeg.input(input_videos[1])
			video = ffmpeg.overlay(main, overlay)
			audio = main.audio if mute_overlay else ffmpeg.filter([main.audio, overlay.audio], 'amix', inputs=2)
			out = ffmpeg.output(video, audio, overlay_video_path)

		elif mode == 'full_width':
			overlay = ffmpeg.input(input_videos[1])
			overlay = overlay.filter('scale', 'main_w', -1)  # scale width to match main, keep aspect ratio
			video = ffmpeg.overlay(main, overlay)
			audio = main.audio if mute_overlay else ffmpeg.filter([main.audio, overlay.audio], 'amix', inputs=2)
			out = ffmpeg.output(video, audio, overlay_video_path)

		elif mode == 'stack_vertical':
			if len(input_videos) < 3:
				return build_exception_message(ValueError, '3 videos required for vertical stack template.')
			vids = [ffmpeg.input(v) for v in input_videos[:3]]
			video = ffmpeg.filter([vids[0], vids[1], vids[2]], 'vstack', inputs=3)
			if mute_overlay:
				audio = vids[0].audio  # keep only first video’s audio
			else:
				audios = [v.audio for v in vids]
				audio = ffmpeg.filter(audios, 'amix', inputs=len(audios))
			out = ffmpeg.output(video, audio, overlay_video_path)

		else:
			return build_exception_message(ValueError, f'Invalid mode: {mode}')

		# Run the ffmpeg pipeline
		ffmpeg.run(out, overwrite_output=True)
		return overlay_video_path

	except Exception as e:
		return build_exception_message(error_type=e.__name__, message=str(e))
