import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import ffmpeg
from tqdm import tqdm

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message

setup_logging()
logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
video_clip_path = os.path.join(base_dir, '..', 'processed_elements', 'normalized_video_clips')
os.makedirs(video_clip_path, exist_ok=True)
max_workers = os.cpu_count() or 4


def normalize_single_clip(clip, output_path, resolution, frame_rate, crf, audio_bitrate, preset):
	"""
	Normalize a single video clip by adjusting resolution, frame rate, codec, and compression parameters.

	Args:
	    clip (str): Full path to the input video clip.
	    output_path (str): Path where the normalized output video will be saved.
	    resolution (tuple): Target resolution as (width, height), e.g., (1280, 720).
	    frame_rate (int): Target frame rate, e.g., 30.
	    crf (int): Constant Rate Factor for quality control (lower is higher quality; typical 18–28).
	    audio_bitrate (str): Target audio bitrate, e.g., '128k'.
	    preset (str): Encoding speed vs. compression efficiency preset (e.g., 'fast', 'slow').

	Returns:
	    Path to the normalized output video if successful, or None if an error occurred.

	Logs:
	    Logs success and failure of the normalization process, including any ffmpeg errors.

	Notes:
	    - Maintains the original aspect ratio by padding if needed.
	    - Uses H.264 for video and AAC for audio encoding.
	"""
	width, height = resolution
	try:
		(
			ffmpeg.input(clip)
			.output(
				output_path,
				vcodec='libx264',
				acodec='aac',
				crf=crf,
				preset=preset,
				vf=(f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2'),
				r=frame_rate,
				audio_bitrate=audio_bitrate,
				format='mp4',
			)
			.run(overwrite_output=True, quiet=True)
		)
		logger.info(f'Normalized {clip} → {output_path}')
		return output_path
	except ffmpeg.Error as e:
		logger.error(f'Error normalizing {clip}: {e.stderr.decode()}')
		return None


def get_normalized_clips(
	input_video_clips: list[str], resolution=(1280, 720), frame_rate=30, crf=23, audio_bitrate='128k', preset='fast'
):
	"""
	Normalize multiple video clips in parallel by adjusting resolution, frame rate, codec, and compression parameters.

	Parameters:
	    input_video_clips (list[str]): should give input video clips in the form of string
	    resolution (tuple, optional): Target resolution as (width, height). Defaults to (1280, 720).
	    frame_rate (int, optional): Target frame rate. Defaults to 30.
	    crf (int, optional): Constant Rate Factor for quality control (lower = better quality). Defaults to 23.
	    audio_bitrate (str, optional): Target audio bitrate. Defaults to '128k'.
	    preset (str, optional): Encoding speed vs. compression efficiency preset. Defaults to 'fast'.
	    max_workers (int, optional): Number of parallel worker threads. If None, uses os.cpu_count().

	Returns:
	    list: Sorted list of file paths to the successfully normalized video clips.

	Notes:
	    - Runs normalization tasks in parallel using ThreadPoolExecutor.
	    - Includes a progress bar (tqdm) to track processing status.
	    - Automatically determines the number of workers based on CPU cores if not specified.
	    - Skips clips that encounter errors but continues processing the rest.
	"""
	width, height = resolution

	if not input_video_clips:
		logger.error("Couldn't find videos to normalize")
		build_exception_message(error_type=ValueError, message="Couldn't find videos to normalize")
	clips = input_video_clips

	temp_files = [os.path.join(video_clip_path, f'normalized_{i}.mp4') for i in range(len(clips))]

	assert len(clips) == len(temp_files), 'Clips and temp_files must be of the same length'

	logger.info(f'Starting normalization with {max_workers} parallel workers...')

	results = []

	with ThreadPoolExecutor(max_workers=max_workers) as executor:
		futures = {
			executor.submit(normalize_single_clip, clip, temp_path, resolution, frame_rate, crf, audio_bitrate, preset): temp_path
			for clip, temp_path in zip(clips, temp_files)
		}

		for future in tqdm(as_completed(futures), total=len(futures), desc='Normalizing Clips'):
			result = future.result()
			if result:
				results.append(result)

	logger.info('All clips normalized.')
	return sorted(results)
