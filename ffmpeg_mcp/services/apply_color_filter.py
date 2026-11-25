import ffmpeg

from ffmpeg_mcp.core.paths import output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import encode, tool_errors
from ffmpeg_mcp.effects.color import ColorPreset, apply_color
from utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def apply_color_filter(
	input_video_path: str,
	preset: ColorPreset | None = None,
	lut_path: str | None = None,
	intensity: float = 1.0,
	output_filename: str | None = None,
) -> str:
	"""
	Colour-grade a video with a look preset and/or a .cube LUT.

	Args:
	    input_video_path: Source video.
	    preset: warm, cool, vintage, bw, vivid, cinematic (teal & orange), matte or moody.
	    lut_path: Optional path to a .cube 3D LUT.
	    intensity: 0-1 blend between original (0) and graded (1).
	    output_filename: Optional output file name.

	Returns:
	    Path to the graded video.
	"""
	if not preset and not lut_path:
		raise ValueError('Provide preset and/or lut_path')
	info = probe_media(input_video_path)
	inp = ffmpeg.input(input_video_path)
	v = apply_color(inp.video, preset=preset, lut_path=lut_path, intensity=intensity)
	out = output_path('color_graded', output_filename, f'graded_{preset or "lut"}')
	return encode(v, inp.audio if info.has_audio else None, out, 'color grade')
