from typing import Literal

ReframeMode = Literal['crop', 'blur_fill', 'pad']


def reframe(v, out_w: int, out_h: int, mode: ReframeMode = 'crop', focus_x: float = 0.5, focus_y: float = 0.5, pad_color: str = 'black'):
	"""
	Fit a video stream into an out_w x out_h frame.

	- crop: fill the frame and crop the overflow; focus_x/focus_y (0-1) choose which part of the source is kept.
	- blur_fill: fit the whole source and fill the empty area with a blurred, zoomed copy (Instagram style).
	- pad: fit the whole source and pad with `pad_color`.
	"""
	fx = min(max(focus_x, 0.0), 1.0)
	fy = min(max(focus_y, 0.0), 1.0)

	if mode == 'crop':
		v = v.filter('scale', out_w, out_h, force_original_aspect_ratio='increase', force_divisible_by=2)
		v = v.filter('crop', out_w, out_h, f'(iw-{out_w})*{fx}', f'(ih-{out_h})*{fy}')
	elif mode == 'pad':
		v = v.filter('scale', out_w, out_h, force_original_aspect_ratio='decrease', force_divisible_by=2)
		v = v.filter('pad', out_w, out_h, '(ow-iw)/2', '(oh-ih)/2', color=pad_color)
	elif mode == 'blur_fill':
		split = v.split()
		bg = (
			split[0]
			.filter('scale', out_w // 4, out_h // 4, force_original_aspect_ratio='increase')
			.filter('crop', out_w // 4, out_h // 4)
			.filter('gblur', sigma=12)
			.filter('eq', brightness=-0.08)
			.filter('scale', out_w, out_h)
		)
		fg = split[1].filter('scale', out_w, out_h, force_original_aspect_ratio='decrease', force_divisible_by=2)
		v = bg.overlay(fg, x='(W-w)/2', y='(H-h)/2')
	else:
		raise ValueError(f'Unknown reframe mode "{mode}". Use crop, blur_fill or pad.')
	return v.filter('setsar', 1)
