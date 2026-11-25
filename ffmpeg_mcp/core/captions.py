import json
import os
from typing import Literal

from ffmpeg_mcp.core.styles import TextStyle
from ffmpeg_mcp.core.text_render import render_text_image
from ffmpeg_mcp.core.transcribe import words_from_srt
from ffmpeg_mcp.effects.text import place_on_canvas, write_image_sequence

CaptionMode = Literal['phrase_highlight', 'word', 'phrase']

_SENTENCE_END = ('.', '!', '?', '…')
_CLAUSE_END = (',', ';', ':')


def load_words(transcript_path: str) -> list[dict]:
	"""Load words from a transcribe_audio JSON file (or any {words:[...]}/[...] JSON) or an .srt file."""
	if not os.path.isfile(transcript_path):
		raise FileNotFoundError(f'Transcript not found: {transcript_path}')
	with open(transcript_path, encoding='utf-8') as f:
		raw = f.read()
	if transcript_path.lower().endswith('.srt'):
		return words_from_srt(raw)
	data = json.loads(raw)
	words = data['words'] if isinstance(data, dict) else data
	return [{'word': str(w['word']).strip(), 'start': float(w['start']), 'end': float(w['end'])} for w in words if str(w['word']).strip()]


def group_words(words: list[dict], max_words: int = 3, max_gap: float = 0.6, max_chunk: float = 2.5) -> list[list[dict]]:
	"""Split words into caption chunks on sentence ends, long pauses, length and duration limits."""
	chunks: list[list[dict]] = []
	current: list[dict] = []
	for w in words:
		if current:
			gap = w['start'] - current[-1]['end']
			span = w['end'] - current[0]['start']
			prev = current[-1]['word']
			if (
				len(current) >= max_words
				or gap > max_gap
				or span > max_chunk
				or prev.endswith(_SENTENCE_END)
				or prev.endswith(_CLAUSE_END)
			):
				chunks.append(current)
				current = []
		current.append(w)
	if current:
		chunks.append(current)
	return chunks


def caption_timeline(words: list[dict], mode: str = 'phrase_highlight', words_per_line: int = 3, hold: float = 0.25):
	"""
	Build caption states: [(start, end, text, highlight_index | None)], non-overlapping and time ordered.
	"""
	states = []
	if mode == 'word':
		for i, w in enumerate(words):
			nxt = words[i + 1]['start'] if i + 1 < len(words) else w['end'] + hold
			end = min(nxt, w['end'] + hold) if nxt > w['end'] else nxt
			states.append((w['start'], max(end, w['start'] + 0.08), w['word'], None))
		return states

	chunks = group_words(words, max_words=words_per_line)
	for c_idx, chunk in enumerate(chunks):
		text = ' '.join(w['word'] for w in chunk)
		next_start = chunks[c_idx + 1][0]['start'] if c_idx + 1 < len(chunks) else None
		chunk_end = chunk[-1]['end'] + hold
		if next_start is not None:
			chunk_end = min(chunk_end, next_start)
		if mode == 'phrase':
			states.append((chunk[0]['start'], chunk_end, text, None))
			continue
		for i, w in enumerate(chunk):
			end = chunk[i + 1]['start'] if i + 1 < len(chunk) else chunk_end
			states.append((w['start'], max(end, w['start'] + 0.05), text, i))
	return states


def build_caption_track(
	words: list[dict],
	style: TextStyle,
	width: int,
	height: int,
	duration: float,
	work_dir: str,
	mode: str = 'phrase_highlight',
	words_per_line: int = 3,
	position: str = 'caption',
) -> str | None:
	"""Render caption states to full-frame PNGs and return an ffconcat playlist covering [0, duration]."""
	states = caption_timeline(words, mode=mode, words_per_line=words_per_line)
	if not states:
		return None
	folder = os.path.join(work_dir, 'captions')
	os.makedirs(folder, exist_ok=True)

	from PIL import Image

	blank = os.path.join(folder, 'blank.png')
	Image.new('RGBA', (width, height), (0, 0, 0, 0)).save(blank)

	cache: dict[tuple, str] = {}
	entries: list[tuple[str, float]] = []
	cursor = 0.0
	for start, end, text, highlight in states:
		start = max(start, cursor)
		end = min(end, duration)
		if end - start < 0.02:
			continue
		if start - cursor > 0.001:
			entries.append((blank, start - cursor))
		key = (text, highlight)
		if key not in cache:
			image = render_text_image(text, style, width, height, highlight_index=highlight)
			path = os.path.join(folder, f'cap_{len(cache):05}.png')
			place_on_canvas(image, width, height, position).save(path, compress_level=1)
			cache[key] = path
		entries.append((cache[key], end - start))
		cursor = end
	if duration - cursor > 0.001:
		entries.append((blank, duration - cursor))
	return write_image_sequence(entries, folder, 'captions.ffconcat')
