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
GIF_ROOT_DIR = os.path.join(CURR_PATH, '..', 'processed_elements', 'gifs')

os.makedirs(GIF_ROOT_DIR, exist_ok=True)


@validate_input_video_path
def make_gif(input_video_path: str, start_timestamp: float = 0.0, duration: float = 2.0):
	"""
	Make gif using video path provided by user.

	Args:
	    input_video_path (str): Path to the source video file.
	    start_timestamp (float, optional): Start time in seconds. Defaults to 0.0.
	    duration (float, optional): Clip length in seconds. Defaults to 4.0.

	Returns:
	    str: Path to the generated clip, or an exception message string on failure.
	"""
	logger.info('Starting making gif...')

	gif_file_name = f'{os.path.splitext(os.path.basename(input_video_path))[0]}_gif_{uuid4()}.gif'
	gif_file_path = os.path.join(GIF_ROOT_DIR, gif_file_name)

	try:
		(
			ffmpeg.input(input_video_path, ss=start_timestamp, t=duration)
			.filter('fps', fps=10)
			.filter('scale', 480, -1, flags='lanczos')
			.output(gif_file_path, gifflags='+transdiff')
			.overwrite_output()
			.run(quiet=True)
		)
		logger.info('Finished making gif...')
		return gif_file_path

	except ffmpeg._run.Error as e:
		return build_exception_message(error_type=ffmpeg._run.Error, message=f'FFmpeg command failed: {e.stderr.decode("utf-8")}')
	except Exception as e:
		return build_exception_message(error_type=Exception, message=f'Unexpected error: {str(e)}')


# if __name__ == '__main__':
# 	path = '/path/to/your/video'
# 	paths = make_gif(input_video_path=path, start_timestamp=0.0, duration=2.0)
# 	print(paths)
