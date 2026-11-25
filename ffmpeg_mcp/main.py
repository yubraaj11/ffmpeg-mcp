import logging
import os

from fastmcp import FastMCP

from ffmpeg_mcp import __version__
from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.core.paths import PROCESSED_ROOT
from ffmpeg_mcp.services import (
	add_background_music,
	add_captions,
	add_text_overlay,
	apply_color_filter,
	apply_zoom,
	beat_sync_montage,
	change_speed,
	clip_video,
	concat_clips_with_transition,
	crop_video,
	detect_beats,
	export_for_platform,
	extract_audio,
	extract_frames,
	get_editing_capabilities,
	get_normalized_clips,
	get_video_metadata,
	make_gif,
	make_reel_from_clips,
	overlay_image,
	overlays_video,
	reframe_video,
	remove_silences,
	render_composition,
	render_preview,
	scale_video,
	talking_head_reel,
	transcribe_audio,
	trim_and_concat_operation,
)

setup_logging()
logger = logging.getLogger(__name__)

INSTRUCTIONS = (
	'AI video editor powered by FFmpeg. For a finished Reel/Short/TikTok in one call use make_reel_from_clips, '
	'beat_sync_montage or talking_head_reel; for full control build a timeline with render_composition '
	'(call get_editing_capabilities first for styles, transitions and formats, and use dry_run to check timing). '
	'Single-effect tools (captions, text, zoom, speed, color, music, reframe, export) work on one file at a time. '
	'Use render_preview to visually check results. All paths must be absolute local paths. '
	f'Outputs are written under {PROCESSED_ROOT}.'
)

mcp = FastMCP(name='ffmpeg-mcp', version=__version__, instructions=INSTRUCTIONS)

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

# Creator editing tools
mcp.tool(name_or_fn=reframe_video)
mcp.tool(name_or_fn=add_text_overlay)
mcp.tool(name_or_fn=transcribe_audio)
mcp.tool(name_or_fn=add_captions)
mcp.tool(name_or_fn=change_speed)
mcp.tool(name_or_fn=apply_zoom)
mcp.tool(name_or_fn=apply_color_filter)
mcp.tool(name_or_fn=add_background_music)
mcp.tool(name_or_fn=detect_beats)
mcp.tool(name_or_fn=remove_silences)
mcp.tool(name_or_fn=export_for_platform)
mcp.tool(name_or_fn=render_preview)

# Full video production (combines the tools above)
mcp.tool(name_or_fn=get_editing_capabilities)
mcp.tool(name_or_fn=render_composition)
mcp.tool(name_or_fn=make_reel_from_clips)
mcp.tool(name_or_fn=beat_sync_montage)
mcp.tool(name_or_fn=talking_head_reel)


def main():
	os.makedirs(PROCESSED_ROOT, exist_ok=True)
	logger.info(f'ffmpeg-mcp {__version__} running; outputs in {PROCESSED_ROOT}')
	mcp.run(transport='stdio')


if __name__ == '__main__':
	main()
