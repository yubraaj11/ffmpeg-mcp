import os
from typing import Literal

import ffmpeg

Position = Literal[
	'top_left',
	'top_center',
	'top_right',
	'center_left',
	'center',
	'center_right',
	'bottom_left',
	'bottom_center',
	'bottom_right',
	'caption',
]
TextAnimation = Literal['none', 'fade', 'slide_up', 'slide_down']

# Vertical anchors keep text clear of the Reels/TikTok UI (top bar, caption + buttons at the bottom).
_Y = {'top': 'H*0.10', 'center': '(H-h)/2', 'bottom': 'H*0.80-h', 'caption': 'H*0.68-h/2'}
_X = {'left': 'W*0.06', 'center': '(W-w)/2', 'right': 'W*0.94-w'}


def position_xy(position: str, x: float | None = None, y: float | None = None) -> tuple[str, str]:
	"""Overlay x/y expressions for an anchor name, or explicit fractions of the frame (centre of the overlay)."""
	if x is not None and y is not None:
		return f'W*{x:.4f}-w/2', f'H*{y:.4f}-h/2'
	if position == 'caption':
		return _X['center'], _Y['caption']
	if position == 'center':
		return _X['center'], _Y['center']
	try:
		vert, horiz = position.split('_')
		return _X[horiz], _Y[vert]
	except (ValueError, KeyError):
		raise ValueError(f'Unknown position "{position}"') from None


def overlay_png(
	v,
	png_path: str,
	start: float,
	duration: float,
	fps: int,
	position: str = 'center',
	x: float | None = None,
	y: float | None = None,
	animation: str = 'fade',
	anim_duration: float = 0.3,
	opacity: float = 1.0,
	scale: tuple[int, int] | None = None,
):
	"""Overlay a still image (rendered text, logo, sticker) for [start, start+duration] with an entrance/exit animation."""
	if duration <= 0:
		raise ValueError('Overlay duration must be positive')
	ov = ffmpeg.input(png_path, loop=1, framerate=fps, t=f'{duration:.4f}').video
	if scale:
		ov = ov.filter('scale', scale[0], scale[1])
	ov = ov.filter('format', 'rgba')
	if opacity < 1.0:
		ov = ov.filter('colorchannelmixer', aa=max(0.0, opacity))
	ad = min(anim_duration, duration / 3)
	if animation in ('fade', 'slide_up', 'slide_down') and ad > 0:
		ov = ov.filter('fade', t='in', st=0, d=ad, alpha=1).filter('fade', t='out', st=max(0.0, duration - ad), d=ad, alpha=1)
	ov = ov.filter('setpts', f'PTS-STARTPTS+{start:.4f}/TB')

	ox, oy = position_xy(position, x, y)
	if animation in ('slide_up', 'slide_down'):
		sign = '+' if animation == 'slide_up' else '-'
		oy = f'{oy}{sign}H*0.04*pow(1-clip((t-{start:.4f})/{max(ad, 0.01):.4f},0,1),2)'
	return v.overlay(ov, x=ox, y=oy, eof_action='pass', enable=f'between(t,{start:.4f},{start + duration:.4f})')


def write_image_sequence(entries: list[tuple[str, float]], folder: str, name: str = 'track.ffconcat') -> str:
	"""
	Write an ffconcat playlist of (png_path, duration) entries. Played as a single input it becomes a
	timed image track - one input for hundreds of caption states instead of one overlay per word.
	"""
	path = os.path.join(folder, name)
	with open(path, 'w') as f:
		f.write('ffconcat version 1.0\n')
		for png, dur in entries:
			f.write(f"file '{os.path.abspath(png)}'\nduration {max(dur, 0.001):.4f}\n")
		if entries:
			f.write(f"file '{os.path.abspath(entries[-1][0])}'\n")  # concat demuxer ignores the last duration otherwise
	return path


def place_on_canvas(image, width: int, height: int, position: str = 'caption', x: float | None = None, y: float | None = None):
	"""Paste an RGBA image onto a transparent full-frame canvas using the same anchors as position_xy."""
	from PIL import Image

	w, h = image.size
	if x is not None and y is not None:
		px, py = width * x - w / 2, height * y - h / 2
	else:
		horiz, vert = 'center', 'caption'
		if position not in ('caption', 'center'):
			vert, horiz = position.split('_')
		elif position == 'center':
			vert = 'center'
		px = {'left': width * 0.06, 'center': (width - w) / 2, 'right': width * 0.94 - w}[horiz]
		py = {'top': height * 0.10, 'center': (height - h) / 2, 'bottom': height * 0.80 - h, 'caption': height * 0.68 - h / 2}[vert]
	canvas = Image.new('RGBA', (width, height), (0, 0, 0, 0))
	canvas.alpha_composite(image, (int(max(0, min(px, width - w))), int(max(0, min(py, height - h)))))
	return canvas


def overlay_image_track(v, playlist_path: str, fps: int):
	"""Overlay a full-frame ffconcat image track (see write_image_sequence) at 0,0."""
	track = ffmpeg.input(playlist_path, f='concat', safe=0).video.filter('fps', fps).filter('format', 'rgba')
	return v.overlay(track, x=0, y=0, eof_action='pass')
