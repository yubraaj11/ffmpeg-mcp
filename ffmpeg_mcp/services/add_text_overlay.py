import os

import ffmpeg

from ffmpeg_mcp.core.paths import category_dir, output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import encode, tool_errors
from ffmpeg_mcp.core.styles import TextStyleName, get_style
from ffmpeg_mcp.core.text_render import render_text_image, save_text_png
from ffmpeg_mcp.effects.text import Position, TextAnimation, overlay_png
from ffmpeg_mcp.utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def add_text_overlay(
	input_video_path: str,
	text: str,
	start_time: float = 0.0,
	duration: float | None = None,
	style: TextStyleName = 'title',
	position: Position = 'top_center',
	x: float | None = None,
	y: float | None = None,
	animation: TextAnimation = 'fade',
	color: str | None = None,
	size: float | None = None,
	output_filename: str | None = None,
) -> str:
	"""
	Add a styled title or text label to a video (rendered with a bundled font, wraps automatically).

	Args:
	    input_video_path: Source video.
	    text: The text to show.
	    start_time: When the text appears (seconds).
	    duration: How long it stays; None = until the end.
	    style: title, subtitle, bold_pop, karaoke, classic, minimal or boxed.
	    position: Anchor (top_/center_/bottom_ + left/center/right, or caption). Positions avoid the Reels UI areas.
	    x: Optional exact centre x as a fraction of width (0-1); requires y.
	    y: Optional exact centre y as a fraction of height (0-1); requires x.
	    animation: none, fade, slide_up or slide_down.
	    color: Optional text colour override, e.g. "#FFE600".
	    size: Optional font size as a fraction of video height (e.g. 0.06).
	    output_filename: Optional output file name.

	Returns:
	    Path to the new video.
	"""
	info = probe_media(input_video_path)
	if start_time < 0 or start_time >= info.duration:
		raise ValueError(f'start_time must be within the video (0 - {info.duration:.2f}s)')
	shown = (info.duration - start_time) if duration is None else min(duration, info.duration - start_time)
	if shown <= 0:
		raise ValueError('duration must be positive')
	text_style = get_style(style, color=color, size=size)
	png = save_text_png(
		render_text_image(text, text_style, info.width, info.height), category_dir(os.path.join('text_overlays', 'assets'))
	)
	inp = ffmpeg.input(input_video_path)
	v = overlay_png(inp.video, png, start_time, shown, round(info.fps or 30), position=position, x=x, y=y, animation=animation)
	out = output_path('text_overlays', output_filename, 'text_overlay')
	return encode(v, inp.audio if info.has_audio else None, out, 'text overlay')
