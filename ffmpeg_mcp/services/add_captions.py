import json
from typing import Literal

import ffmpeg

from ffmpeg_mcp.core.captions import build_caption_track, load_words
from ffmpeg_mcp.core.paths import job_dir, output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import encode, success, tool_errors
from ffmpeg_mcp.core.styles import TextStyleName, get_style
from ffmpeg_mcp.core.transcribe import transcribe
from ffmpeg_mcp.effects.text import Position, overlay_image_track
from utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def add_captions(
	input_video_path: str,
	style: TextStyleName = 'bold_pop',
	mode: Literal['phrase_highlight', 'word', 'phrase'] = 'phrase_highlight',
	words_per_line: int = 3,
	position: Position = 'caption',
	transcript_path: str | None = None,
	model_size: str = 'base',
	language: str | None = None,
	output_filename: str | None = None,
) -> str:
	"""
	Burn animated, word-synced captions into a video (auto-transcribed, or from a transcript you provide).

	Args:
	    input_video_path: Source video with speech.
	    style: bold_pop (uppercase, yellow active word), karaoke (highlight pill), classic (boxed subtitles),
	        minimal, boxed, subtitle or title.
	    mode: phrase_highlight = short phrases with the spoken word highlighted; word = one word at a time;
	        phrase = plain phrases.
	    words_per_line: Max words per caption phrase.
	    position: Where captions sit; "caption" is the lower-middle safe zone used by Reels/TikTok.
	    transcript_path: Optional .json (from transcribe_audio, possibly hand-corrected) or .srt file.
	    model_size: faster-whisper model used when auto-transcribing.
	    language: ISO language code, None = auto-detect.
	    output_filename: Optional output file name.

	Returns:
	    JSON with output_path and transcript_path.
	"""
	info = probe_media(input_video_path)
	extra = {}
	with job_dir('captions') as work:
		if transcript_path:
			words = load_words(transcript_path)
		else:
			if not info.has_audio:
				raise ValueError('The video has no audio to transcribe; pass transcript_path instead')
			result = transcribe(input_video_path, work, model_size=model_size, language=language)
			words = result['words']
			transcript_path = output_path('transcripts', None, 'captions_transcript', '.json')
			with open(transcript_path, 'w', encoding='utf-8') as f:
				json.dump(result, f, indent=2, ensure_ascii=False)
			extra['transcript_hint'] = 'Edit this JSON to fix words and call add_captions again with transcript_path.'
		if not words:
			raise ValueError('No speech found to caption')
		track = build_caption_track(
			words,
			get_style(style),
			info.width,
			info.height,
			info.duration,
			work,
			mode=mode,
			words_per_line=words_per_line,
			position=position,
		)
		inp = ffmpeg.input(input_video_path)
		v = overlay_image_track(inp.video, track, round(info.fps or 30))
		out = output_path('captioned', output_filename, 'captioned')
		encode(v, inp.audio if info.has_audio else None, out, 'captions')
	return success(output_path=out, transcript_path=transcript_path, caption_words=len(words), **extra)
