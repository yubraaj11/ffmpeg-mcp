import json
import logging
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import ffmpeg

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.exceptions import build_exception_message
from ffmpeg_mcp.services import get_video_metadata
from utils import validate_input_video_path

setup_logging()
logger = logging.getLogger(__name__)


@validate_input_video_path
def extract_frames(
	input_video_path: str, output_dir: str, number_of_frames: Optional[int] = None, timestamp_offset: Optional[int] = None
) -> List[str]:
	"""
	Extract frames from a video file and save each frame with a unique UUID filename.

	Behavior:
	    - If `number_of_frames` is provided, extracts that many frames evenly across the video.
	      If requested frames exceed total frames available, caps at total frames.
	    - If `timestamp_offset` is provided (and `number_of_frames` is None), extracts frames
	      at every given second interval.
	    - If neither is provided, defaults to extracting one frame per second.
	    - `number_of_frames` takes priority if both are provided.

	Parameters:
	    input_video_path (str): Path to the input video file.
	    output_dir (str): Directory to save extracted frames (created if it doesn't exist).
	    number_of_frames (Optional[int]): Total number of frames to extract evenly across the video.
	    timestamp_offset (Optional[int]): Time interval in seconds between frames.

	Returns:
	    List[str]: List of file paths for the extracted frames with UUID-based filenames.
	"""
	Path(output_dir).mkdir(parents=True, exist_ok=True)

	metadata = get_video_metadata(input_video_path)
	metadata_streams = json.loads(metadata).get('streams', [])
	if not metadata_streams:
		raise build_exception_message(error_type=ValueError, message='No video streams found in the file.')

	stream = metadata_streams[0]
	total_duration = float(stream.get('duration') or json.loads(metadata)['format']['duration'])
	fps = eval(stream['r_frame_rate'])
	total_frames_available = int(total_duration * fps)

	frame_files = []

	# Case 1: number_of_frames provided → split total duration evenly
	if number_of_frames is not None:
		# Cap the frames to total available frames
		number_of_frames = min(number_of_frames, total_frames_available)
		interval = total_duration / number_of_frames
		for i in range(number_of_frames):
			timestamp = i * interval
			unique_name = f'frame_{uuid4().hex}.jpg'
			output_path = Path(output_dir) / unique_name
			(
				ffmpeg.input(input_video_path, ss=timestamp)
				.output(str(output_path), vframes=1, qscale=2)
				.overwrite_output()
				.run(quiet=True)
			)
			frame_files.append(str(output_path))

	# Case 2: timestamp_offset provided → extract frames at each offset
	elif timestamp_offset is not None:
		current_time = 0
		while current_time < total_duration:
			unique_name = f'frame_{uuid4().hex}.jpg'
			output_path = Path(output_dir) / unique_name
			(
				ffmpeg.input(input_video_path, ss=current_time)
				.output(str(output_path), vframes=1, qscale=2)
				.overwrite_output()
				.run(quiet=True)
			)
			frame_files.append(str(output_path))
			current_time += timestamp_offset

	# Case 3: neither provided → default extract every second
	else:
		current_time = 0
		timestamp_offset = 1
		while current_time < total_duration:
			unique_name = f'frame_{uuid4().hex}.jpg'
			output_path = Path(output_dir) / unique_name
			(
				ffmpeg.input(input_video_path, ss=current_time)
				.output(str(output_path), vframes=1, qscale=2)
				.overwrite_output()
				.run(quiet=True)
			)
			frame_files.append(str(output_path))
			current_time += timestamp_offset

	return frame_files
