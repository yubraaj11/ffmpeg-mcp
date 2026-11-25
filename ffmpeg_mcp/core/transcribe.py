import logging
import os
import threading

import ffmpeg

from ffmpeg_mcp.core.runner import run

logger = logging.getLogger(__name__)

_MODELS: dict[str, object] = {}
_LOCK = threading.Lock()


def _model(size: str):
	with _LOCK:
		if size not in _MODELS:
			from faster_whisper import WhisperModel  # heavy import, only when needed

			logger.info(f'Loading faster-whisper model "{size}" (first use downloads it)...')
			_MODELS[size] = WhisperModel(size, device='auto', compute_type='int8')
		return _MODELS[size]


def extract_speech_wav(media_path: str, out_path: str) -> str:
	run(ffmpeg.input(media_path).audio.output(out_path, ac=1, ar=16000, acodec='pcm_s16le'), 'audio extraction')
	return out_path


def transcribe(media_path: str, work_dir: str, model_size: str = 'base', language: str | None = None) -> dict:
	"""
	Transcribe speech with word-level timestamps.

	Returns {language, duration, text, words: [{word, start, end}], segments: [{start, end, text}]}.
	"""
	wav = extract_speech_wav(media_path, os.path.join(work_dir, 'speech_16k.wav'))
	import soundfile

	samples, _ = soundfile.read(wav, dtype='float32')  # decode ourselves; avoids faster-whisper's PyAV decoder
	if samples.size == 0:
		raise ValueError('The media has no audio to transcribe')
	model = _model(model_size)
	segments_iter, info = model.transcribe(samples, word_timestamps=True, vad_filter=True, language=language)
	words, segments = [], []
	for seg in segments_iter:
		segments.append({'start': round(seg.start, 3), 'end': round(seg.end, 3), 'text': seg.text.strip()})
		for w in seg.words or []:
			token = w.word.strip()
			if token:
				words.append({'word': token, 'start': round(w.start, 3), 'end': round(w.end, 3)})
	return {
		'language': info.language,
		'duration': round(info.duration, 3),
		'text': ' '.join(s['text'] for s in segments),
		'words': words,
		'segments': segments,
	}


def _fmt_srt_time(t: float) -> str:
	ms = int(round(t * 1000))
	h, ms = divmod(ms, 3_600_000)
	m, ms = divmod(ms, 60_000)
	s, ms = divmod(ms, 1000)
	return f'{h:02}:{m:02}:{s:02},{ms:03}'


def to_srt(segments: list[dict]) -> str:
	blocks = []
	for i, seg in enumerate(segments, 1):
		blocks.append(f'{i}\n{_fmt_srt_time(seg["start"])} --> {_fmt_srt_time(seg["end"])}\n{seg["text"]}\n')
	return '\n'.join(blocks)


def _parse_srt_time(value: str) -> float:
	hms, ms = value.strip().replace('.', ',').split(',')
	h, m, s = hms.split(':')
	return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def words_from_srt(srt_text: str) -> list[dict]:
	"""Approximate word timings from SRT cues by spreading each cue's duration across its words."""
	words = []
	for block in srt_text.replace('\r', '').strip().split('\n\n'):
		lines = [ln for ln in block.split('\n') if ln.strip()]
		arrow = next((i for i, ln in enumerate(lines) if '-->' in ln), None)
		if arrow is None:
			continue
		start_s, end_s = lines[arrow].split('-->')
		start, end = _parse_srt_time(start_s), _parse_srt_time(end_s.split()[0])
		tokens = ' '.join(lines[arrow + 1 :]).split()
		if not tokens or end <= start:
			continue
		weights = [len(t) + 2 for t in tokens]
		total = sum(weights)
		t = start
		for token, wgt in zip(tokens, weights):
			dur = (end - start) * wgt / total
			words.append({'word': token, 'start': round(t, 3), 'end': round(t + dur, 3)})
			t += dur
	return words
