import ffmpeg

from ffmpeg_mcp.composition.models import SpeedSegment
from ffmpeg_mcp.core.paths import output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import encode, tool_errors
from ffmpeg_mcp.effects.speed import apply_speed
from ffmpeg_mcp.utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def change_speed(
	input_video_path: str,
	speed: float | None = None,
	speed_ramp: list[SpeedSegment] | None = None,
	output_filename: str | None = None,
) -> str:
	"""
	Speed up, slow down, or speed-ramp a video. Audio keeps its pitch.

	Args:
	    input_video_path: Source video.
	    speed: Constant speed for the whole video (0.1-10, e.g. 0.5 = half-speed slow motion, 2 = double).
	    speed_ramp: Instead of `speed`, a list of segments in source seconds, e.g.
	        [{"start": 2, "end": 4, "speed": 0.4}] for a slow-motion moment, or
	        [{"start": 0, "end": 3, "speed_start": 1, "speed_end": 3}] for a gradual ramp. Gaps play at 1x.
	    output_filename: Optional output file name.

	Returns:
	    Path to the new video.
	"""
	if speed is None and not speed_ramp:
		raise ValueError('Provide speed or speed_ramp')
	info = probe_media(input_video_path)
	inp = ffmpeg.input(input_video_path)
	ramp = [s.model_dump(exclude_none=True) if hasattr(s, 'model_dump') else dict(s) for s in speed_ramp] if speed_ramp else None
	v, a, _ = apply_speed(inp.video, inp.audio if info.has_audio else None, info.duration, speed=speed, ramp=ramp)
	out = output_path('speed', output_filename, 'speed')
	return encode(v, a, out, 'speed change')
