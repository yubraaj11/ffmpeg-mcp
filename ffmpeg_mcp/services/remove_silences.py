import ffmpeg

from ffmpeg_mcp.core.paths import output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import encode, success, tool_errors
from ffmpeg_mcp.core.silence import detect_silences, speech_ranges
from ffmpeg_mcp.utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def remove_silences(
	input_video_path: str,
	noise_db: float = -35.0,
	min_silence: float = 0.5,
	padding: float = 0.12,
	output_filename: str | None = None,
) -> str:
	"""
	Jump-cut a talking video: cut out pauses and dead air automatically.

	Args:
	    input_video_path: Source video with speech.
	    noise_db: Anything quieter than this (dBFS) counts as silence; raise towards -25 for noisy rooms.
	    min_silence: Only cut pauses longer than this many seconds.
	    padding: Seconds of breathing room kept around speech.
	    output_filename: Optional output file name.

	Returns:
	    JSON with output_path, original/new duration and the kept ranges.
	"""
	info = probe_media(input_video_path)
	if not info.has_audio:
		raise ValueError('The video has no audio to detect silences in')
	keep = speech_ranges(info.duration, detect_silences(input_video_path, noise_db, min_silence), padding=padding)
	if not keep:
		raise ValueError('Everything was detected as silence; try a lower noise_db')
	inp = ffmpeg.input(input_video_path)
	n = len(keep)
	vs = inp.video.split() if n > 1 else None
	as_ = inp.audio.asplit() if n > 1 else None
	parts = []
	for i, (s, e) in enumerate(keep):
		parts.append((vs[i] if vs is not None else inp.video).trim(start=s, end=e).setpts('PTS-STARTPTS'))
		parts.append((as_[i] if as_ is not None else inp.audio).filter('atrim', start=s, end=e).filter('asetpts', 'PTS-STARTPTS'))
	joined = ffmpeg.concat(*parts, n=n, v=1, a=1).node
	out = output_path('jump_cuts', output_filename, 'jump_cut')
	encode(joined[0], joined[1], out, 'silence removal')
	return success(
		output_path=out,
		original_duration=round(info.duration, 3),
		new_duration=round(sum(e - s for s, e in keep), 3),
		segments_kept=[[s, e] for s, e in keep],
	)
