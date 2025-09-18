import json
import logging
import os
import shutil
from typing import List

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from ffmpeg_mcp.services import get_video_metadata
from ffmpeg_mcp.services.normalize_video_clips import get_normalized_clips

from utils import calculate_video_offset

base_dir = os.path.dirname(os.path.abspath(__file__))
video_clip_path = os.path.join(base_dir, '..', 'processed_elements', 'normalized_video_clips')

final_output_path = os.path.abspath(
	os.path.join(base_dir, '..', 'processed_elements', 'concatenated_video', 'output_concatenated_video.mp4')
)

os.makedirs(os.path.dirname(final_output_path), exist_ok=True)


setup_logging()
logger = logging.getLogger(__name__)


def concat_clips_with_transition(input_video_clips: List[str], transition_type: str = 'fade', transition_duration: float = 2) -> str:
	"""
	Concatenate multiple video clips with transitions.

	Args:
	    input_video_clips (List[str]):
	        A list of file paths (strings) to the video clips that will be concatenated.
	    transition_type (str, optional):
	        The type of transition to apply between clips.
	        Supported transitions include:
	        - fade (default), fadeblack, fadewhite, distance
	        - wipeleft, wiperight, wipeup, wipedown
	        - slideleft, slideright, slideup, slidedown
	        - smoothleft, smoothright, smoothup, smoothdown
	        - circlecrop, rectcrop, circleclose, circleopen
	        - horzclose, horzopen, vertclose, vertopen
	        - diagbl, diagbr, diagtl, diagtr
	        - hlslice, hrslice, vuslice, vdslice
	        - dissolve, pixelize, radial, hblur
	        - wipetl, wipetr, wipebl, wipebr
	        - zoomin, fadegrays, squeezev, squeezeh
	        - hlwind, hrwind, vuwind, vdwind
	        - coverleft, coverright, coverup, coverdown
	    transition_duration (float, optional):
	        Duration of the transition effect in seconds.

	Returns:
	    str:
	        The absolute path to the final concatenated video with transitions applied.
	"""

	output_video_path = os.path.join(base_dir, '..', 'processed_elements', 'Intermediate_files', 'final_edited_video.mp4')
	os.makedirs(output_video_path, exist_ok=True)

	if len(input_video_clips) < 2:
		logger.error('Need at lest two video clips to concat')
		return None

	get_normalized_clips(input_video_clips=input_video_clips)

	video_list = sorted([os.path.join(video_clip_path, f) for f in os.listdir(video_clip_path) if f.endswith('.mp4')])
	for i in range(1, len(video_list)):
		clip_1 = video_list[0] if i == 1 else output_video_path
		clip_2 = video_list[i]

		metadata = get_video_metadata(input_video_path=clip_1)
		clip_1_duration = json.loads(metadata)['format']['duration']
		metadata = get_video_metadata(input_video_path=clip_2)
		clip_2_duration = json.loads(metadata)['format']['duration']

		logger.info(f'clip_1 ({i - 1}) duration: {clip_1_duration}s, clip_2 ({i}) duration: {clip_2_duration}s')

		input1 = ffmpeg.input(clip_1)
		input2 = ffmpeg.input(clip_2)

		video1 = input1.video
		video2 = input2.video
		audio1 = input1.audio
		audio2 = input2.audio

		offset_duration = calculate_video_offset(input_video_path=clip_1, transition_duration=transition_duration)
		logger.info(f'offeset duration for clips is {offset_duration}')
		try:
			v = ffmpeg.filter([video1, video2], 'xfade', transition=transition_type, duration=transition_duration, offset=offset_duration)
			a = ffmpeg.filter([audio1, audio2], 'acrossfade', duration=transition_duration)
			temp_output = output_video_path.replace('.mp4', f'_step_{i}.mp4')
			(ffmpeg.output(v, a, temp_output, safe=0).run(overwrite_output=True, quiet=True))
			output_video_path = temp_output
		except ffmpeg.Error as e:
			logger.error(f'Error occured in ffmpeg: {str(e)}')
			build_exception_message(error_type=ffmpeg.Error, message=f'Error occured while concatenating video: {str(e)}')

	if os.path.exists(output_video_path):
		os.rename(output_video_path, final_output_path)
		logger.info(f'Final concatenated video saved to: {final_output_path}')

		# Clean up: remove normalized clips and intermediate files
		if os.path.exists(video_clip_path):
			shutil.rmtree(video_clip_path)
			logger.info(f'Deleted normalized clips folder: {video_clip_path}')

		intermediate_dir = os.path.join(base_dir, '..', 'processed_elements', 'Intermediate_files')
		if os.path.exists(intermediate_dir):
			shutil.rmtree(intermediate_dir)
			logger.info(f'Deleted intermediate files folder: {intermediate_dir}')

		return final_output_path
	else:
		logger.error(f'Output video not found: {output_video_path}')
		return None

