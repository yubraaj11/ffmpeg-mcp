import math

import ffmpeg


def atempo_chain(a, speed: float):
	"""Change audio tempo without changing pitch. atempo accepts 0.5-100, so chain it for slower speeds."""
	if abs(speed - 1.0) < 1e-6:
		return a
	remaining = speed
	while remaining < 0.5:
		a = a.filter('atempo', 0.5)
		remaining /= 0.5
	while remaining > 100.0:
		a = a.filter('atempo', 100.0)
		remaining /= 100.0
	return a.filter('atempo', round(remaining, 6))


def _validate_speed(speed: float) -> None:
	if not (0.1 <= speed <= 10.0):
		raise ValueError(f'Speed must be between 0.1 and 10.0, got {speed}')


def build_speed_pieces(duration: float, ramp: list[dict]) -> list[tuple[float, float, float]]:
	"""
	Expand ramp segments into contiguous (start, end, speed) pieces covering [0, duration].

	Each ramp segment is {start, end, speed} or {start, end, speed_start, speed_end}; the latter is
	approximated by short constant-speed steps with an ease-in-out curve. Gaps play at 1x.
	"""
	segments = sorted(ramp, key=lambda s: float(s['start']))
	pieces: list[tuple[float, float, float]] = []
	cursor = 0.0
	for seg in segments:
		start = max(0.0, float(seg['start']))
		end = min(duration, float(seg['end']))
		if end <= start:
			raise ValueError(f'Invalid speed segment {seg}: end must be after start and inside the clip ({duration:.2f}s)')
		if start < cursor - 1e-6:
			raise ValueError(f'Speed segments overlap at {start}s')
		if start > cursor + 1e-3:
			pieces.append((cursor, start, 1.0))
		s0 = float(seg.get('speed_start', seg.get('speed', 1.0)))
		s1 = float(seg.get('speed_end', seg.get('speed', s0)))
		_validate_speed(s0)
		_validate_speed(s1)
		if abs(s0 - s1) < 1e-6:
			pieces.append((start, end, s0))
		else:
			steps = max(2, min(12, math.ceil((end - start) / 0.2)))
			step_len = (end - start) / steps
			for k in range(steps):
				u = (k + 0.5) / steps
				eased = u * u * (3 - 2 * u)
				pieces.append((start + k * step_len, start + (k + 1) * step_len, s0 + (s1 - s0) * eased))
		cursor = end
	if duration - cursor > 1e-3:
		pieces.append((cursor, duration, 1.0))
	return pieces


def apply_speed(v, a, duration: float, speed: float | None = None, ramp: list[dict] | None = None):
	"""
	Apply a constant speed or a speed ramp to a video stream and (optional) audio stream.

	Returns (video, audio, new_duration). Ramp times are in the input's time base (seconds from its start).
	"""
	if ramp:
		pieces = build_speed_pieces(duration, ramp)
	else:
		speed = 1.0 if speed is None else float(speed)
		_validate_speed(speed)
		if abs(speed - 1.0) < 1e-6:
			return v, a, duration
		v = v.filter('setpts', f'(PTS-STARTPTS)/{speed}')
		if a is not None:
			a = atempo_chain(a, speed)
		return v, a, duration / speed

	n = len(pieces)
	v_split = v.split() if n > 1 else None
	a_split = a.asplit() if (a is not None and n > 1) else None
	parts = []
	new_duration = 0.0
	for i, (start, end, spd) in enumerate(pieces):
		vi = (v_split[i] if v_split is not None else v).trim(start=start, end=end).setpts(f'(PTS-STARTPTS)/{spd}')
		parts.append(vi)
		if a is not None:
			ai = (a_split[i] if a_split is not None else a).filter('atrim', start=start, end=end).filter('asetpts', 'PTS-STARTPTS')
			parts.append(atempo_chain(ai, spd))
		new_duration += (end - start) / spd
	joined = ffmpeg.concat(*parts, n=n, v=1, a=1 if a is not None else 0).node
	if a is not None:
		return joined[0], joined[1], new_duration
	return joined[0], None, new_duration
