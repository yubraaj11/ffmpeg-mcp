import json
import logging
import os
from uuid import uuid4

import ffmpeg

from ffmpeg_mcp.exceptions import build_exception_message
from ffmpeg_mcp.services import get_video_metadata

logger = logging.getLogger(__name__)

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
CROPPED_VIDEO_DIR = os.path.join(CURR_PATH, '..', 'processed_elements', 'cropped_videos')

os.makedirs(CROPPED_VIDEO_DIR, exist_ok=True)


def crop_video(input_video_path: str, safe_crop: bool = False, height: int = 480, width: int = 640, x_offset: int = 0, y_offset: int = 0):
	"""
	Crop a video using ffmpeg-python.

	Params:
	    input_video_path: Path to input video (required)
	    safe_crop: If True, allows exact cropping (ignores mod-2 restrictions). Default: False
	    height: Output height (default: 480)
	    width: Output width (default: 640)
	    x_offset: Top-left X coordinate of crop (default: 0)
	    y_offset: Top-left Y coordinate of crop (default: 0)

	Returns:
	    str: Path to the cropped video.
	"""
	logger.info('Starting video cropping...')
	try:
		cropped_video_file_name = f'{os.path.splitext(os.path.basename(input_video_path))[0]}_cropped_{uuid4()}.mp4'
		cropped_video_path = os.path.join(CROPPED_VIDEO_DIR, cropped_video_file_name)

		# Extract metadata
		video_metadata = get_video_metadata(input_video_path)
		metadata_streams = json.loads(video_metadata).get('streams', [])
		if not metadata_streams:
			return build_exception_message(error_type=ValueError, message='No video streams found in the file.')

		stream = metadata_streams[0]
		video_width, video_height = stream.get('width'), stream.get('height')

		if not safe_crop:
			if width > video_width or height > video_height:  # validation
				return build_exception_message(
					error_type=ValueError, message='Crop dimensions must be smaller than or equal to original video dimensions.'
				)

		# Build crop filter
		crop_filter = f'crop={width}:{height}:{x_offset}:{y_offset}'
		if safe_crop:
			crop_filter += ':exact=1'

		(ffmpeg.input(input_video_path).output(cropped_video_path, vf=crop_filter).run(overwrite_output=True))

		logger.info('Finished video cropping...')
		return cropped_video_path
	except ffmpeg.Error as e:
		return build_exception_message(
			error_type=ffmpeg.Error, message=f'FFmpeg Command Failed: {e.stderr.decode("utf-8") if e.stderr else str(e)}'
		)
	except Exception as e:
		return build_exception_message(error_type=Exception, message=f'An unexpected error occurred: {str(e)}')


if __name__ == '__main__':
	path = '/Users/student/Downloads/IMG_4818.MOV'
	val = crop_video(path, height=120, width=4096, x_offset=0, y_offset=0)
	print(val)
