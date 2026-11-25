from dataclasses import dataclass
from fractions import Fraction

import ffmpeg


@dataclass
class MediaInfo:
	path: str
	duration: float
	width: int | None
	height: int | None
	fps: float | None
	has_video: bool
	has_audio: bool


def probe_media(path: str) -> MediaInfo:
	"""Probe a media file and return the fields the editing pipeline needs."""
	data = ffmpeg.probe(path)
	streams = data.get('streams', [])
	video = next((s for s in streams if s.get('codec_type') == 'video' and s.get('disposition', {}).get('attached_pic', 0) == 0), None)
	audio = next((s for s in streams if s.get('codec_type') == 'audio'), None)

	duration = data.get('format', {}).get('duration')
	if duration is None and video is not None:
		duration = video.get('duration')
	duration = float(duration or 0.0)

	width = height = fps = None
	if video is not None:
		width = int(video.get('width', 0)) or None
		height = int(video.get('height', 0)) or None
		rotation = _rotation(video)
		if rotation in (90, 270) and width and height:
			width, height = height, width
		rate = video.get('avg_frame_rate') or video.get('r_frame_rate') or '0/1'
		try:
			fps = float(Fraction(rate)) or None
		except (ValueError, ZeroDivisionError):
			fps = None

	return MediaInfo(
		path=path,
		duration=duration,
		width=width,
		height=height,
		fps=fps,
		has_video=video is not None,
		has_audio=audio is not None,
	)


def _rotation(video_stream: dict) -> int:
	tags = video_stream.get('tags', {}) or {}
	if 'rotate' in tags:
		try:
			return abs(int(tags['rotate'])) % 360
		except ValueError:
			return 0
	for side in video_stream.get('side_data_list', []) or []:
		if 'rotation' in side:
			try:
				return abs(int(side['rotation'])) % 360
			except (TypeError, ValueError):
				return 0
	return 0
