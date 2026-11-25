import ffmpeg

from ffmpeg_mcp.composition.models import ZoomSegment
from ffmpeg_mcp.core.paths import output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import encode, tool_errors
from ffmpeg_mcp.effects.zoom import apply_zoom as zoom_effect
from ffmpeg_mcp.utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def apply_zoom(
	input_video_path: str,
	zooms: list[ZoomSegment] | None = None,
	ken_burns: float | None = None,
	output_filename: str | None = None,
) -> str:
	"""
	Add punch-in zooms (and/or a slow ken-burns push) to a video - the classic talking-head emphasis cut.

	Args:
	    input_video_path: Source video.
	    zooms: Segments like [{"start": 2.0, "end": 4.5, "zoom": 1.25, "center_x": 0.5, "center_y": 0.4, "ease": "snap"}].
	        ease "snap" jumps in instantly; "smooth" eases over `ramp` seconds (default 0.3).
	    ken_burns: Optional slow continuous zoom reaching this factor at the end (e.g. 1.1).
	    output_filename: Optional output file name.

	Returns:
	    Path to the new video.
	"""
	if not zooms and not ken_burns:
		raise ValueError('Provide zooms and/or ken_burns')
	info = probe_media(input_video_path)
	width, height = info.width - info.width % 2, info.height - info.height % 2
	inp = ffmpeg.input(input_video_path)
	v = inp.video
	if (width, height) != (info.width, info.height):
		v = v.filter('scale', width, height)
	segments = [z.model_dump() if hasattr(z, 'model_dump') else ZoomSegment(**z).model_dump() for z in (zooms or [])]
	v = zoom_effect(v, width, height, segments, info.duration, ken_burns=ken_burns)
	out = output_path('zoomed', output_filename, 'zoomed')
	return encode(v, inp.audio if info.has_audio else None, out, 'zoom')
