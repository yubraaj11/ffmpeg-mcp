import logging
import os

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from utils import validate_input_video_path

setup_logging()
logger = logging.getLogger(__name__)

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
AUDIO_PATH = os.path.join(CURR_PATH, '..', 'processed_elements', 'audio')

os.makedirs(AUDIO_PATH, exist_ok=True)


@validate_input_video_path
def extract_audio(input_video_path: str):
	"""
	Function to extract audio from the given input video.

	Params:
	    input_video_path (str): Path to the input video.

	Returns:
	    audio_file_path (str): Path to the audio file.
	"""
	logger.info('Starting audio extraction process...')
	audio_file_name = f'{os.path.basename(input_video_path).split(".")[0]}.wav'
	audio_file_path = os.path.join(AUDIO_PATH, audio_file_name)
	try:
		(
			ffmpeg.input(input_video_path)
			.output(audio_file_path, vn=None, acodec='pcm_s16le', ac=2, ar=44100)
			.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
		)
		logger.info('Finished audio extraction process...')
		return audio_file_path
	except ffmpeg.Error as e:
		return build_exception_message(error_type=ffmpeg.Error, message=f'FFmpeg Command Failed: {e.stderr.decode("utf-8")}')
	except Exception as e:
		return build_exception_message(error_type=Exception, message=f'An Unexpected error has occurred: {str(e)}')
