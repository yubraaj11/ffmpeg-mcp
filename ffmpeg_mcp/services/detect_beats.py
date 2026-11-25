from ffmpeg_mcp.core.beats import detect_beats as _detect
from ffmpeg_mcp.core.runner import success, tool_errors


@tool_errors
def detect_beats(audio_path: str, start_offset: float = 0.0, max_duration: float | None = 120.0) -> str:
	"""
	Detect the tempo and beat times of a song (or any audio/video file) for beat-synced editing.

	Args:
	    audio_path: Audio or video file.
	    start_offset: Analyse from this many seconds into the file; returned times are relative to it.
	    max_duration: Seconds to analyse (None = whole file).

	Returns:
	    JSON with tempo (BPM), beats (seconds), downbeats (first beat of each bar, assuming 4/4) and duration.
	"""
	return success(**_detect(audio_path, start_offset=start_offset, max_duration=max_duration))
