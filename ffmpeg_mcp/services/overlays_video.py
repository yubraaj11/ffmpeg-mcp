import logging
import os
from pathlib import Path
from typing import Literal

import ffmpeg
from utils import validate_input_video_path
from ffmpeg_mcp.configs.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
VIDEO_OVERLAY_PATH = os.path.join(CURR_PATH, '..', 'processed_elements', 'video_overlays')

os.makedirs(VIDEO_OVERLAY_PATH, exist_ok=True)


@validate_input_video_path
def overlays_video(
    input_video_path: str,
    overlay_video_path: str,
    output_filename: str = 'output.mp4',
    positioning: Literal['top_left', 'bottom_left', 'top_right', 'bottom_right'] = 'bottom_right',
    scale: tuple = (200, 300),
    keep_audio: bool = True,
) -> str:
    """
    Overlay a video on top of another with simple positioning.
    Loops the overlay video until the background video ends, trimming any extra frames.

    Args:
        input_video_path (str): Path to background video.
        overlay_video_path (str): Path to overlay video.
        output_filename (str): Name of the output video file (saved inside VIDEO_OVERLAY_PATH).
        positioning (Literal): Where to place overlay.
        scale (tuple): (width, height) to resize overlay video before placing.
        keep_audio (bool): Whether to keep background audio.

    Returns:
        str: Path to the generated video.
    """

    input_video = Path(input_video_path)
    overlay_video = Path(overlay_video_path)
    output = Path(VIDEO_OVERLAY_PATH) / output_filename

    if not input_video.exists():
        raise FileNotFoundError(f'Background video not found: {input_video}')
    if not overlay_video.exists():
        raise FileNotFoundError(f'Overlay video not found: {overlay_video}')

    logger.info(f'Processing overlay: {input_video} + {overlay_video} -> {output}')

    bg_duration = float(ffmpeg.probe(str(input_video))['format']['duration'])
    ov_duration = float(ffmpeg.probe(str(overlay_video))['format']['duration'])

    loop_count = int(bg_duration // ov_duration)
    if bg_duration % ov_duration != 0:
        loop_count += 1

    bg_stream = ffmpeg.input(str(input_video))
    ov_stream = ffmpeg.input(str(overlay_video), stream_loop=loop_count-1)

    if scale:
        ov_stream = ffmpeg.filter(ov_stream, 'scale', scale[0], scale[1])

    ov_stream = ov_stream.filter('trim', duration=bg_duration).filter('setpts', 'PTS-STARTPTS')

    positions = {
        'top_left': ('10', '10'),
        'top_right': ('W-w-10', '10'),
        'bottom_left': ('10', 'H-h-10'),
        'bottom_right': ('W-w-10', 'H-h-10'),
    }

    if positioning not in positions:
        raise ValueError(f'Invalid positioning: {positioning}')

    x, y = positions[positioning]

    video = ffmpeg.overlay(bg_stream.video, ov_stream, x=x, y=y)

    if keep_audio:
        audio = bg_stream.audio
        out = ffmpeg.output(video, audio, str(output))
    else:
        out = ffmpeg.output(video, str(output))

    out.run(overwrite_output=True, quiet=True)
    logger.info(f'Overlay complete: {output}')

    return str(output)


