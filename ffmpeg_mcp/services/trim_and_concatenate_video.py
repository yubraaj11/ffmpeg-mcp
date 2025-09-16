import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import ffmpeg
from utils import validate_input_video_path
from ffmpeg_mcp.exceptions import build_exception_message
from ffmpeg_mcp.configs.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
PROCESSED_VIDEO_PATH = os.path.join(CURR_PATH, '..', 'processed_elements', 'video_overlays')
os.makedirs(PROCESSED_VIDEO_PATH, exist_ok=True)


@validate_input_video_path
def __init__(self, target_resolution: str = '1280x720', output_dir: str = PROCESSED_VIDEO_PATH):
    """
    VideoEditor for trimming and concatenating multiple videos.

    Args:
        target_resolution (str): Resolution to scale all videos (e.g. '1280x720').
        output_dir (str): Directory to save processed videos.
    """
    self.target_resolution = target_resolution
    self.output_dir = Path(output_dir)
    logger.info(f'Output directory set to: {self.output_dir.resolve()}')


@validate_input_video_path
def trim_and_concat_operation(
    self,
    inputs: List[Dict[str, Optional[str]]],
    output_filename: str = 'final_output.mp4',
) -> Optional[str]:
    """
    Trim and concatenate multiple videos (normalize resolution & format if needed).

    Args:
        inputs (list[dict]): Each dict must have:
            - 'path' (str): path to the video file
            - 'start_time' (str, optional): start time in seconds
            - 'end_time' (str, optional): end time in seconds
        output_filename (str): Name of the final concatenated video file.

    Returns:
        str: Path to the output video if successful.
        None: If an error occurs.
    """
    v_streams = []
    a_streams = []

    if not inputs:
        logger.error('No input videos provided')
        raise ValueError('Provide at least one input video')

    output_path = self.output_dir / output_filename
    width, height = self.target_resolution.split('x')

    try:
        for idx, item in enumerate(inputs):
            video_path = item.get('path')
            start = item.get('start_time')
            end = item.get('end_time')

            if not video_path:
                raise FileNotFoundError(f'Missing path for video {idx + 1}')

            if start is not None and end is not None:
                inp = ffmpeg.input(video_path, ss=start, to=end)
                logger.info(f'Prepared segment {idx + 1}: {video_path} ({start}s → {end}s)')
            else:
                inp = ffmpeg.input(video_path)
                logger.info(f'Prepared full video {idx + 1}: {video_path}')

            v = inp.video.filter('scale', width, height).filter('format', 'yuv420p')
            v_streams.append(v)
            a_streams.append(inp.audio)

        streams = []
        for v, a in zip(v_streams, a_streams):
            streams.extend([v, a])

        joined = ffmpeg.concat(*streams, v=1, a=1).node
        v = joined[0]
        a = joined[1]

        logger.info('Saving final concatenated video...')
        (
            ffmpeg.output(v, a, str(output_path), vcodec='libx264', acodec='aac')
            .overwrite_output()
            .run(quiet=False)
        )
        logger.info(f'Final concatenated video saved at: {output_path.resolve()}')
        return str(output_path.resolve())

    except ffmpeg.Error as e:
        return build_exception_message(error_type=ffmpeg.Error, message=f'FFmpeg Command Failed: {e.stderr.decode("utf-8")}')
    except Exception as e:
        return build_exception_message(error_type=Exception, message=f'An Unexpected error has occurred: {str(e)}')
        
