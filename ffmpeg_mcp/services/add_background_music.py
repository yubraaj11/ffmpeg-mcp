import os

import ffmpeg

from ffmpeg_mcp.core.paths import output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import run, tool_errors
from ffmpeg_mcp.effects.audio import mix_music, music_bed
from utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def add_background_music(
	input_video_path: str,
	music_path: str,
	volume: float = 0.25,
	duck_voice: bool = True,
	fade_in: float = 0.5,
	fade_out: float = 1.5,
	start_offset: float = 0.0,
	replace_audio: bool = False,
	output_filename: str | None = None,
) -> str:
	"""
	Add a local music track under a video. The track loops/trims to the video length; the video is not re-encoded.

	Args:
	    input_video_path: Source video.
	    music_path: Local audio file (mp3, wav, m4a, ...).
	    volume: Music volume (0-2; 0.25 suits a bed under speech, 1.0 for music-only edits).
	    duck_voice: Automatically lower the music while someone is speaking.
	    fade_in: Music fade-in seconds.
	    fade_out: Music fade-out seconds at the end of the video.
	    start_offset: Start the song from this many seconds in (e.g. skip to the drop).
	    replace_audio: Drop the original audio and keep only the music.
	    output_filename: Optional output file name.

	Returns:
	    Path to the new video.
	"""
	if not os.path.isfile(music_path):
		raise FileNotFoundError(f'Music file not found: {music_path}')
	info = probe_media(input_video_path)
	inp = ffmpeg.input(input_video_path)
	bed = music_bed(music_path, info.duration, volume=volume, fade_in=fade_in, fade_out=fade_out, start_offset=start_offset)
	voice = inp.audio if (info.has_audio and not replace_audio) else None
	audio = mix_music(voice, bed, duck=duck_voice)
	out = output_path('with_music', output_filename, 'with_music')
	run(
		ffmpeg.output(
			inp.video,
			audio,
			out,
			vcodec='copy',
			acodec='aac',
			audio_bitrate='192k',
			ar=48000,
			movflags='+faststart',
			t=f'{info.duration:.4f}',
		),
		'music mix',
	)
	return out
