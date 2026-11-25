import os
import re
import shutil
import subprocess

import ffmpeg

from ffmpeg_mcp.core.runner import run


def measure_loudness(path: str) -> float | None:
	"""Integrated loudness (LUFS) of a file's audio, or None if it has no measurable audio."""
	cmd = ['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-vn', '-af', 'ebur128=framelog=quiet', '-f', 'null', '-']
	stderr = subprocess.run(cmd, capture_output=True, text=True).stderr
	matches = re.findall(r'I:\s+(-?[\d.]+|-inf) LUFS', stderr)
	if not matches or matches[-1] == '-inf':
		return None
	return float(matches[-1])


def correct_loudness(path: str, target_lufs: float = -14.0, tolerance: float = 1.0) -> float | None:
	"""
	Measure the file and, if it is off target by more than `tolerance` LU, apply a static gain (with a true-peak
	limiter) to the audio only - the video stream is copied untouched. Returns the final loudness.
	"""
	measured = measure_loudness(path)
	if measured is None or measured < -60 or abs(measured - target_lufs) <= tolerance:
		return measured
	gain_db = max(-20.0, min(20.0, target_lufs - measured))
	tmp = f'{os.path.splitext(path)[0]}.loudfix{os.path.splitext(path)[1]}'
	inp = ffmpeg.input(path)
	audio = inp.audio.filter('volume', f'{gain_db:.2f}dB').filter('alimiter', limit=0.89, level=0)
	run(
		ffmpeg.output(inp.video, audio, tmp, vcodec='copy', acodec='aac', audio_bitrate='192k', ar=48000, movflags='+faststart'),
		'loudness correction',
	)
	shutil.move(tmp, path)
	return measure_loudness(path)
