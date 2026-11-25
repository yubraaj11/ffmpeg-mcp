import ffmpeg

from ffmpeg_mcp.core.formats import FormatName, resolve_format
from ffmpeg_mcp.core.paths import output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import encode, tool_errors
from ffmpeg_mcp.effects.reframe import ReframeMode, reframe
from utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def reframe_video(
	input_video_path: str,
	target_format: FormatName = 'reel',
	mode: ReframeMode = 'crop',
	focus_x: float = 0.5,
	focus_y: float = 0.5,
	output_filename: str | None = None,
) -> str:
	"""
	Convert a video to another aspect ratio, e.g. a landscape clip into a vertical 9:16 Reel.

	Args:
	    input_video_path: Source video.
	    target_format: reel/story/shorts/tiktok (1080x1920), square (1080x1080), portrait (1080x1350, 4:5), landscape (1920x1080).
	    mode: "crop" fills the frame and crops the overflow; "blur_fill" keeps the whole picture on a blurred
	        copy of itself (Instagram style); "pad" keeps the whole picture with black bars.
	    focus_x: For crop, which part to keep horizontally (0 = left edge, 0.5 = centre, 1 = right edge).
	    focus_y: For crop, which part to keep vertically.
	    output_filename: Optional output file name.

	Returns:
	    Path to the reframed video.
	"""
	width, height = resolve_format(target_format)
	info = probe_media(input_video_path)
	inp = ffmpeg.input(input_video_path)
	v = reframe(inp.video, width, height, mode=mode, focus_x=focus_x, focus_y=focus_y)
	out = output_path('reframed', output_filename, f'reframed_{target_format}')
	return encode(v, inp.audio if info.has_audio else None, out, 'reframe')
