import ffmpeg

from ffmpeg_mcp.core.formats import PLATFORMS, PlatformName, resolve_format
from ffmpeg_mcp.core.loudness import correct_loudness
from ffmpeg_mcp.core.paths import output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import run, success, tool_errors
from ffmpeg_mcp.effects.audio import loudness_normalize, silent_audio
from ffmpeg_mcp.effects.reframe import ReframeMode, reframe
from utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def export_for_platform(
	input_video_path: str,
	platform: PlatformName = 'instagram_reel',
	reframe_mode: ReframeMode = 'blur_fill',
	crf: int = 20,
	normalize_loudness: bool = True,
	output_filename: str | None = None,
) -> str:
	"""
	Produce an upload-ready file for a platform: right resolution/aspect, 30 fps, H.264 High + AAC 48 kHz,
	fast-start MP4 and -14 LUFS loudness. Warns when the video is longer than the platform allows.

	Args:
	    input_video_path: Source video.
	    platform: instagram_reel, instagram_story, instagram_feed (4:5), tiktok, youtube_shorts or youtube (16:9).
	    reframe_mode: How to fit a different aspect ratio: blur_fill, crop or pad.
	    crf: Quality (lower = better/larger; 18-23 is typical).
	    normalize_loudness: Normalise audio to -14 LUFS.
	    output_filename: Optional output file name.

	Returns:
	    JSON with output_path, resolution, duration, loudness and warnings.
	"""
	settings = PLATFORMS[platform]
	width, height = resolve_format(settings['format'])
	info = probe_media(input_video_path)
	inp = ffmpeg.input(input_video_path)
	v = reframe(inp.video, width, height, mode=reframe_mode).filter('fps', settings['fps'])
	a = inp.audio if info.has_audio else silent_audio(info.duration)
	if normalize_loudness and info.has_audio:
		a = loudness_normalize(a)
	bitrate = settings['video_bitrate']
	out = output_path('exports', output_filename, platform)
	run(
		ffmpeg.output(
			v,
			a,
			out,
			vcodec='libx264',
			**{'profile:v': 'high'},
			pix_fmt='yuv420p',
			crf=crf,
			preset='medium',
			maxrate=bitrate,
			bufsize=f'{int(bitrate[:-1]) * 2}M',
			acodec='aac',
			audio_bitrate='192k',
			ar=48000,
			ac=2,
			movflags='+faststart',
			t=f'{info.duration:.4f}',
		),
		'platform export',
	)
	lufs = correct_loudness(out) if (normalize_loudness and info.has_audio) else None
	warnings = []
	if settings['max_duration'] and info.duration > settings['max_duration']:
		warnings.append(f'Video is {info.duration:.1f}s; {platform} allows up to {settings["max_duration"]}s')
	return success(
		output_path=out,
		resolution=f'{width}x{height}',
		fps=settings['fps'],
		duration=round(info.duration, 3),
		loudness_lufs=lufs,
		warnings=warnings,
	)
