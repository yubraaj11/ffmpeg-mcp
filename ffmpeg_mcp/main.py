import logging
import os

from fastmcp import FastMCP

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.services import (
	clip_video,
	concat_clips_with_transition,
	crop_video,
	extract_audio,
	extract_frames,
	get_normalized_clips,
	get_video_metadata,
	make_gif,
	overlay_image,
	overlays_video,
	scale_video,
	trim_and_concat_operation,
)

setup_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP(name='ffmpeg-mcp', version='0.1.0')

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
PROCESSED_ELEMENTS = os.path.join(CURR_PATH, 'processed_elements')

mcp.tool(name_or_fn=extract_frames)
mcp.tool(name_or_fn=extract_audio)
mcp.tool(name_or_fn=clip_video)
mcp.tool(name_or_fn=crop_video)
mcp.tool(name_or_fn=make_gif)
mcp.tool(name_or_fn=concat_clips_with_transition)
mcp.tool(name_or_fn=get_normalized_clips)
mcp.tool(name_or_fn=overlay_image)
mcp.tool(name_or_fn=overlays_video)
mcp.tool(name_or_fn=trim_and_concat_operation)
mcp.tool(name_or_fn=scale_video)
mcp.tool(name_or_fn=get_video_metadata)


def main():
	os.makedirs(PROCESSED_ELEMENTS, exist_ok=True)
	logger.info('Server running...')
	mcp.run(transport='stdio')


if __name__ == '__main__':
	main()
