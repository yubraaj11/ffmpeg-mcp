import os
from typing import Literal

import ffmpeg

ColorPreset = Literal['warm', 'cool', 'vintage', 'bw', 'vivid', 'cinematic', 'matte', 'moody']


def _preset_chain(v, preset: str):
	if preset == 'warm':
		return v.filter('colortemperature', temperature=5200).filter('eq', saturation=1.1, contrast=1.03)
	if preset == 'cool':
		return v.filter('colortemperature', temperature=8000).filter('eq', saturation=1.0, contrast=1.04)
	if preset == 'vintage':
		return v.filter('curves', preset='vintage').filter('eq', saturation=0.85).filter('vignette', angle='PI/5')
	if preset == 'bw':
		return v.filter('hue', s=0).filter('eq', contrast=1.15, brightness=0.01)
	if preset == 'vivid':
		return v.filter('eq', saturation=1.4, contrast=1.08).filter('unsharp', 5, 5, 0.6)
	if preset == 'cinematic':
		return (
			v.filter('colorbalance', rs=-0.06, gs=0.0, bs=0.08, rh=0.08, gh=0.02, bh=-0.06)
			.filter('eq', contrast=1.1, saturation=0.9)
			.filter('vignette', angle='PI/6')
		)
	if preset == 'matte':
		return v.filter('curves', all='0/0.08 0.5/0.5 1/0.92').filter('eq', saturation=0.85)
	if preset == 'moody':
		return (
			v.filter('eq', brightness=-0.04, contrast=1.12, saturation=0.75)
			.filter('colorbalance', bs=0.05, bm=0.03)
			.filter('vignette', angle='PI/4')
		)
	raise ValueError(f'Unknown color preset "{preset}"')


def apply_color(v, preset: str | None = None, lut_path: str | None = None, intensity: float = 1.0):
	"""
	Colour grade a stream with a preset and/or a .cube LUT. intensity (0-1) blends with the original.
	"""
	if not preset and not lut_path:
		return v
	intensity = min(max(float(intensity), 0.0), 1.0)
	if intensity == 0.0:
		return v
	if intensity < 1.0:
		split = v.split()
		original, graded = split[0], split[1]
	else:
		original, graded = None, v
	if preset:
		graded = _preset_chain(graded, preset)
	if lut_path:
		if not os.path.isfile(lut_path):
			raise FileNotFoundError(f'LUT file not found: {lut_path}')
		graded = graded.filter('lut3d', file=lut_path)
	if original is None:
		return graded
	return ffmpeg.filter([graded, original], 'blend', all_mode='normal', all_opacity=intensity)
