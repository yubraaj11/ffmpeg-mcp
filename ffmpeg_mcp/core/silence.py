import re
import subprocess


def detect_silences(media_path: str, noise_db: float = -35.0, min_silence: float = 0.5) -> list[tuple[float, float]]:
	"""Return [(start, end)] silent ranges using ffmpeg's silencedetect."""
	cmd = [
		'ffmpeg',
		'-hide_banner',
		'-nostats',
		'-i',
		media_path,
		'-af',
		f'silencedetect=noise={noise_db}dB:d={min_silence}',
		'-f',
		'null',
		'-',
	]
	stderr = subprocess.run(cmd, capture_output=True, text=True).stderr
	starts = [float(m) for m in re.findall(r'silence_start: (-?[\d.]+)', stderr)]
	ends = [float(m) for m in re.findall(r'silence_end: (-?[\d.]+)', stderr)]
	ranges = []
	for i, s in enumerate(starts):
		e = ends[i] if i < len(ends) else None
		ranges.append((max(0.0, s), e if e is not None else float('inf')))
	return ranges


def speech_ranges(
	duration: float, silences: list[tuple[float, float]], padding: float = 0.12, min_keep: float = 0.3
) -> list[tuple[float, float]]:
	"""Invert silences into the ranges to keep, with a little padding so words are not clipped."""
	keep = []
	cursor = 0.0
	for s, e in silences:
		seg_end = min(duration, s + padding)
		if seg_end - cursor >= min_keep:
			keep.append((round(cursor, 3), round(seg_end, 3)))
		cursor = max(cursor, min(duration, e - padding))
	if duration - cursor >= min_keep:
		keep.append((round(cursor, 3), round(duration, 3)))
	return keep
