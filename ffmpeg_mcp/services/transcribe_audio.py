import json
import os

from ffmpeg_mcp.core.paths import job_dir, output_path
from ffmpeg_mcp.core.runner import success, tool_errors
from ffmpeg_mcp.core.transcribe import to_srt, transcribe


@tool_errors
def transcribe_audio(input_media_path: str, model_size: str = 'base', language: str | None = None) -> str:
	"""
	Transcribe speech from a video or audio file with word-level timestamps (local faster-whisper, offline after the
	first model download).

	The JSON transcript can be corrected by hand and passed to add_captions / render_composition as transcript_path.

	Args:
	    input_media_path: Video or audio file.
	    model_size: tiny, base (default), small, medium or large-v3. Larger is more accurate but slower.
	    language: ISO language code such as "en"; None auto-detects.

	Returns:
	    JSON with transcript_path (.json with words[{word,start,end}] and segments), srt_path, language and text.
	"""
	if not os.path.isfile(input_media_path):
		raise FileNotFoundError(f'File not found: {input_media_path}')
	with job_dir('transcribe') as work:
		result = transcribe(input_media_path, work, model_size=model_size, language=language)
	stem = os.path.splitext(os.path.basename(input_media_path))[0]
	json_path = output_path('transcripts', None, stem, '.json')
	with open(json_path, 'w', encoding='utf-8') as f:
		json.dump(result, f, indent=2, ensure_ascii=False)
	srt_path = json_path[:-5] + '.srt'
	with open(srt_path, 'w', encoding='utf-8') as f:
		f.write(to_srt(result['segments']))
	return success(
		transcript_path=json_path,
		srt_path=srt_path,
		language=result['language'],
		duration=result['duration'],
		word_count=len(result['words']),
		text=result['text'],
	)
