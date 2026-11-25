from typing import Literal

ZoomEase = Literal['snap', 'smooth']


def _envelope(start: float, end: float, ease: str, ramp: float) -> str:
	"""ffmpeg expression in t: 1 inside [start, end], 0 outside, with optional smoothstep ramps."""
	if ease == 'snap' or ramp <= 0:
		return f'between(t,{start:.4f},{end:.4f})'
	r = min(ramp, (end - start) / 2)
	f = f'min(clip((t-{start:.4f})/{r:.4f},0,1),clip(({end:.4f}-t)/{r:.4f},0,1))'
	return f'(between(t,{start:.4f},{end:.4f})*({f})*({f})*(3-2*({f})))'


def zoom_expressions(zooms: list[dict], duration: float, ken_burns: float | None = None) -> tuple[str, str, str]:
	"""Build (zoom, center_x, center_y) expressions of t for the given punch-in segments."""
	zoom_terms, cx_terms, cy_terms = [], [], []
	for z in zooms:
		start, end = float(z['start']), float(z['end'])
		if end <= start:
			raise ValueError(f'Invalid zoom segment {z}: end must be after start')
		level = float(z.get('zoom', 1.2))
		if not (1.0 <= level <= 4.0):
			raise ValueError(f'Zoom level must be between 1.0 and 4.0, got {level}')
		env = _envelope(start, end, z.get('ease', 'smooth'), float(z.get('ramp', 0.3)))
		zoom_terms.append(f'{level - 1:.4f}*{env}')
		cx = float(z.get('center_x', 0.5)) - 0.5
		cy = float(z.get('center_y', 0.5)) - 0.5
		if abs(cx) > 1e-6:
			cx_terms.append(f'{cx:.4f}*{env}')
		if abs(cy) > 1e-6:
			cy_terms.append(f'{cy:.4f}*{env}')

	zoom = '1' + ''.join(f'+{t}' for t in zoom_terms)
	if ken_burns and ken_burns > 1.0 and duration > 0:
		zoom = f'({zoom})*(1+{ken_burns - 1:.4f}*clip(t/{duration:.4f},0,1))'
	cx = '0.5' + ''.join(f'+{t}' for t in cx_terms)
	cy = '0.5' + ''.join(f'+{t}' for t in cy_terms)
	return zoom, cx, cy


def apply_zoom(v, width: int, height: int, zooms: list[dict], duration: float, ken_burns: float | None = None):
	"""
	Animated punch-in zooms on a width x height stream.

	zooms: [{start, end, zoom=1.2, center_x=0.5, center_y=0.5, ease='smooth'|'snap', ramp=0.3}]
	ken_burns: optional slow continuous zoom reaching this factor at the end (e.g. 1.1).
	"""
	if not zooms and not (ken_burns and ken_burns > 1.0):
		return v
	z, cx, cy = zoom_expressions(zooms or [], duration, ken_burns)
	sw = f'trunc({width}*({z})/2)*2'
	sh = f'trunc({height}*({z})/2)*2'
	x = f'clip({width}*({z})*({cx})-{width / 2},0,{width}*({z})-{width})'
	y = f'clip({height}*({z})*({cy})-{height / 2},0,{height}*({z})-{height})'
	v = v.filter('scale', w=sw, h=sh, eval='frame', flags='bicubic')
	return v.filter('crop', width, height, x, y).filter('setsar', 1)
