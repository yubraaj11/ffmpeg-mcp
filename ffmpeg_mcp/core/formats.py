from typing import Literal

FormatName = Literal['reel', 'story', 'shorts', 'tiktok', 'square', 'portrait', 'landscape']

FORMATS: dict[str, tuple[int, int]] = {
	'reel': (1080, 1920),
	'story': (1080, 1920),
	'shorts': (1080, 1920),
	'tiktok': (1080, 1920),
	'square': (1080, 1080),
	'portrait': (1080, 1350),
	'landscape': (1920, 1080),
}

PlatformName = Literal['instagram_reel', 'instagram_story', 'instagram_feed', 'tiktok', 'youtube_shorts', 'youtube']

PLATFORMS: dict[str, dict] = {
	'instagram_reel': {'format': 'reel', 'fps': 30, 'max_duration': 180, 'video_bitrate': '8M'},
	'instagram_story': {'format': 'story', 'fps': 30, 'max_duration': 60, 'video_bitrate': '8M'},
	'instagram_feed': {'format': 'portrait', 'fps': 30, 'max_duration': 3600, 'video_bitrate': '8M'},
	'tiktok': {'format': 'tiktok', 'fps': 30, 'max_duration': 600, 'video_bitrate': '8M'},
	'youtube_shorts': {'format': 'shorts', 'fps': 30, 'max_duration': 180, 'video_bitrate': '10M'},
	'youtube': {'format': 'landscape', 'fps': 30, 'max_duration': None, 'video_bitrate': '12M'},
}


def resolve_format(name: str) -> tuple[int, int]:
	if name not in FORMATS:
		raise ValueError(f'Unknown format "{name}". Choose one of: {", ".join(FORMATS)}')
	return FORMATS[name]
