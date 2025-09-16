import json
import logging
import os
from uuid import uuid4

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from ffmpeg_mcp.services import get_video_metadata
from utils import validate_input_video_path

setup_logging()
logger = logging.getLogger(__name__)


CURR_PATH = os.path.dirname(os.path.abspath(__file__))
CLIPS_ROOT_DIR = os.path.join(CURR_PATH, '..', 'processed_elements', 'video_clips')

os.makedirs(CLIPS_ROOT_DIR, exist_ok=True)


@validate_input_video_path
def clip_video(input_video_path: str, start_timestamp: float = 0.0, duration: float = 5.0):
	"""
	Generate a video clip from the given video file using ffmpeg-python.

	Args:
	    input_video_path (str): Path to the source video file.
	    start_timestamp (float, optional): Start time in seconds. Defaults to 0.0.
	    duration (float, optional): Clip length in seconds. Defaults to 5.0.

	Returns:
	    str: Path to the generated clip, or an exception message string on failure.
	"""
	logger.info('Starting video clipping...')
	video_metadata = get_video_metadata(input_video_path)
	metadata = json.loads(video_metadata)
	streams = metadata.get('streams', [])

	if not streams:
		return build_exception_message(error_type=ValueError, message='No video streams found in the file.')

	stream = streams[0]
	total_duration = float(stream.get('duration') or metadata['format']['duration'])

	if start_timestamp + duration > total_duration:
		return build_exception_message(error_type=ValueError, message='Clip duration exceeds total duration.')

	clip_file_name = f'{os.path.splitext(os.path.basename(input_video_path))[0]}_clip_{uuid4()}.mp4'
	clip_file_path = os.path.join(CLIPS_ROOT_DIR, clip_file_name)

	try:
		(
			ffmpeg.input(input_video_path, ss=start_timestamp, t=duration)
			.output(clip_file_path, c='copy')
			.overwrite_output()
			.run(quiet=True)
		)
		logger.info('Finished video clipping...')
		return clip_file_path

	except ffmpeg.Error as e:
		return build_exception_message(error_type=ffmpeg.Error, message=f'FFmpeg command failed: {e.stderr.decode("utf-8")}')
	except Exception as e:
		return build_exception_message(error_type=Exception, message=f'Unexpected error: {str(e)}')


if __name__ == '__main__':
	path = '/Users/student/Downloads/IMG_4766.MOV'
	paths = clip_video(input_video_path=path, start_timestamp=0.0, duration=2.0)
	print(paths)
