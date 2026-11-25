import os
import tempfile

import ffmpeg
import numpy as np

from ffmpeg_mcp.core.runner import run


def detect_beats(audio_path: str, start_offset: float = 0.0, max_duration: float | None = None) -> dict:
	"""Decode any audio/video file with ffmpeg, then run beat tracking (see _detect_beats_wav)."""
	if not os.path.isfile(audio_path):
		raise FileNotFoundError(f'Audio file not found: {audio_path}')
	with tempfile.TemporaryDirectory() as tmp:
		wav = os.path.join(tmp, 'beats.wav')
		opts = {'ss': start_offset} if start_offset > 0 else {}
		if max_duration:
			opts['t'] = max_duration
		run(ffmpeg.input(audio_path, **opts).audio.output(wav, ac=1, ar=22050, acodec='pcm_s16le'), 'audio decode for beat detection')
		return _detect_beats_wav(wav)


def _detect_beats_wav(audio_path: str) -> dict:
	"""
	Beat tracking with librosa. Times are relative to the start of the decoded audio.

	Returns {tempo, beats, downbeats, duration}. Downbeats are estimated as every 4th beat, choosing the phase
	with the strongest onsets (assumes 4/4 - true for most pop/electronic music).
	"""
	import librosa  # heavy import, only when needed

	y, sr = librosa.load(audio_path, sr=22050, mono=True)
	if y.size == 0:
		raise ValueError('Audio is empty (check start_offset and that the file has an audio stream)')
	onset_env = librosa.onset.onset_strength(y=y, sr=sr)
	tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
	tempo = float(np.atleast_1d(tempo)[0])
	beats = librosa.frames_to_time(beat_frames, sr=sr)

	downbeats: list[float] = []
	if len(beat_frames) >= 4:
		strengths = onset_env[np.minimum(beat_frames, len(onset_env) - 1)]
		phase = int(np.argmax([strengths[p::4].mean() for p in range(4)]))
		downbeats = [round(float(t), 3) for t in beats[phase::4]]

	return {
		'tempo': round(tempo, 2),
		'beats': [round(float(t), 3) for t in beats],
		'downbeats': downbeats,
		'duration': round(len(y) / sr, 3),
	}
