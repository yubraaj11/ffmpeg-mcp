import functools
import json
import logging
import traceback

import ffmpeg

from ffmpeg_mcp.exceptions import build_exception_message

logger = logging.getLogger(__name__)

# Encoder settings for intermediate files: fast and visually lossless enough for further processing.
INTERMEDIATE_VIDEO = {'vcodec': 'libx264', 'crf': 18, 'preset': 'veryfast', 'pix_fmt': 'yuv420p'}
INTERMEDIATE_AUDIO = {'acodec': 'aac', 'audio_bitrate': '192k', 'ar': 48000, 'ac': 2}


class FFmpegRunError(RuntimeError):
	pass


def run(stream_spec, description: str = 'ffmpeg') -> None:
	"""Run an ffmpeg-python graph, raising FFmpegRunError with the tail of stderr on failure."""
	cmd = ffmpeg.compile(stream_spec, overwrite_output=True)
	logger.debug('Running: %s', ' '.join(cmd))
	try:
		ffmpeg.run(stream_spec, overwrite_output=True, capture_stdout=True, capture_stderr=True)
	except ffmpeg.Error as e:
		stderr = (e.stderr or b'').decode('utf-8', errors='replace')
		tail = '\n'.join(stderr.strip().splitlines()[-15:])
		raise FFmpegRunError(f'{description} failed:\n{tail}') from e


def tool_errors(func):
	"""Convert any exception raised by a tool into the project's structured JSON error message."""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except FFmpegRunError as e:
			logger.error(str(e))
			return build_exception_message(error_type=FFmpegRunError, message=str(e))
		except (ValueError, FileNotFoundError) as e:  # includes pydantic ValidationError
			logger.error(str(e))
			return build_exception_message(error_type=type(e), message=str(e))
		except Exception as e:
			logger.error(traceback.format_exc())
			return build_exception_message(error_type=type(e), message=f'Unexpected error: {e}')

	return wrapper


def success(**payload) -> str:
	return json.dumps({'status': 'SUCCESS', **payload}, indent=2)


# Encoder settings for files handed back to the user by single-effect tools.
OUTPUT_ARGS = {
	'vcodec': 'libx264',
	'crf': 18,
	'preset': 'fast',
	'pix_fmt': 'yuv420p',
	'acodec': 'aac',
	'audio_bitrate': '192k',
	'ar': 48000,
	'movflags': '+faststart',
}


def encode(v, a, path: str, description: str, **overrides) -> str:
	"""Encode a video stream (and optional audio stream) to `path` with OUTPUT_ARGS."""
	streams = [v] if a is None else [v, a]
	args = {**OUTPUT_ARGS, **overrides}
	if a is None:
		for key in ('acodec', 'audio_bitrate', 'ar'):
			args.pop(key, None)
	run(ffmpeg.output(*streams, path, **args), description)
	return path
