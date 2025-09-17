import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import ffmpeg
from ffmpeg_mcp.exceptions import build_exception_message
from ffmpeg_mcp.configs.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
PROCESSED_VIDEO_PATH = os.path.join(CURR_PATH, '..', 'processed_elements', 'trim_and_concat')
os.makedirs(PROCESSED_VIDEO_PATH, exist_ok=True)

DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 1280
DEFAULT_X = 0
DEFAULT_Y = 0

#for checking multiple videos
def validate_input_video_path(func):
    def wrapper(inputs, *args, **kwargs):
        if inputs is None and len(args) > 0:
            inputs = args[0]

        if isinstance(inputs, list):
            for idx, item in enumerate(inputs):
                video_path = item.get('path')
                if not Path(video_path).exists():
                    raise FileNotFoundError(f"Video {idx + 1} not found: {video_path}")
        elif isinstance(inputs, str):
            if not Path(inputs).exists():
                raise FileNotFoundError(f"Video not found: {inputs}")
        else:
            raise ValueError("Invalid input type for video path validation")

        return func(inputs, *args, **kwargs)

    return wrapper


@validate_input_video_path
def trim_and_concat_operation(
    inputs: List[Dict[str, Optional[str]]],
    output_filename: str = 'final_output.mp4',
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    x: int = DEFAULT_X,
    y: int = DEFAULT_Y,
) -> Optional[str]:
    """
    Trim and concatenate multiple videos (portrait orientation, normalize format).

    Args:
        inputs (list[dict]): Each dict must have:
            - 'path' (str): path to the video file
            - 'start_time' (str, optional): start time in seconds
            - 'end_time' (str, optional): end time in seconds
        output_filename (str): Name of the final concatenated video file.
        width (int): Width to scale each video (portrait).
        height (int): Height to scale each video (portrait).
        x (int): X position for overlay (default 0).
        y (int): Y position for overlay (default 0).

    Returns:
        str: Path to the output video if successful.
        None: If an error occurs.
    """
    v_streams = []
    a_streams = []

    if not inputs:
        logger.error('No input videos provided')
        raise ValueError('Provide at least one input video')

    output_path = Path(PROCESSED_VIDEO_PATH) / output_filename

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

            v = inp.video.filter('scale', width, height, force_original_aspect_ratio='decrease') \
                          .filter('pad', width, height, x, y) \
                          .filter('format', 'yuv420p')

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
            .run(quiet=True)
        )

        logger.info(f'Final concatenated video saved at: {output_path.resolve()}')
        return str(output_path.resolve())

    except ffmpeg.Error as e:
        return build_exception_message(
            error_type=ffmpeg.Error,
            message=f'FFmpeg Command Failed: {e.stderr.decode("utf-8")}',
        )
    except Exception as e:
        return build_exception_message(
            error_type=Exception,
            message=f'An Unexpected error has occurred: {str(e)}',
        )


