import logging
import os

import ffmpeg

from ffmpeg_mcp.configs.logging_config import setup_logging
from utils import validate_input_video_path
from ffmpeg_mcp.exceptions import build_exception_message

setup_logging()
logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
output_video_path = os.path.join(base_dir, '..', 'processed_elements', 'upscaled_video', 'final_edited_video.mp4')
os.makedirs(os.path.dirname(output_video_path), exist_ok=True)


@validate_input_video_path
def scale_up_videos(input_video_path: str, resolution: str = '1080p') -> str:
	"""
		Upscales a video to 1080p, 2K, or 4K using FFmpeg while preserving aspect ratio and color accuracy.

		Args:
			input_video_path (str): Path to the input video file.
			resolution (str, optional): Target resolution for upscaling. 
				Acceptable values are '1080p', '2k', or '4k'. Defaults to '1080p'.

		Returns:
			str: Path to the upscaled video if successful.
			
		Raises:
			RuntimeError: If upscaling fails due to an error during processing.
	"""
	resoultions = {'1080p': (1920, 1080), '2k': (2560, 1440), '4k': (3840, 2160)}
	target = resoultions.get(resolution)
	if not target:
		logger.error('Invalid resolution, unable to use it')
		raise ValueError(f'Invalid resolution {resoultions}')

	w, h = target
	try:
		(
			ffmpeg.input(input_video_path)
			.output(
				output_video_path,
				vcodec='h264',
				acodec='aac',
				vf=(f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2'),
				r=60,
				audio_bitrate='128k',
				crf=23,
				preset='fast',
				color_primaries='bt709',
				colorspace='bt709',
				color_trc='bt709',
			)
			.overwrite_output()
			.run(quiet=True)
		)
		logger.info(f'{resolution} video saved at: {output_video_path}')
		return output_video_path

	except ffmpeg.Error as e:
		logger.error(f'FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}')
		return build_exception_message(error_type=ffmpeg.Error, message=f'FFmpeg Command Failed: {e.stderr.decode("utf-8")}')


	except Exception as e:
		logger.error(f'Unexpected error: {str(e)}')
		return build_exception_message(error_type=Exception, message= f'An unexpected error occured: {str(e)}',)


# if __name__ == '__main__':
# 	print(scale_up_videos(input_video_path='/home/yogesh/Downloads/vid1.MOV', resolution='2k'))
