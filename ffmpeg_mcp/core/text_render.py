import os
import uuid
from functools import lru_cache

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from ffmpeg_mcp.core.paths import FONTS_DIR
from ffmpeg_mcp.core.styles import TextStyle

DEFAULT_FONT = os.path.join(FONTS_DIR, 'Montserrat.ttf')


@lru_cache(maxsize=64)
def _font(font_path: str, size: int, weight: str) -> ImageFont.FreeTypeFont:
	font = ImageFont.truetype(font_path, size)
	try:
		font.set_variation_by_name(weight)
	except (OSError, ValueError):
		pass  # static font without variations
	return font


def _rgba(color: str | None) -> tuple[int, int, int, int] | None:
	if color is None:
		return None
	value = color.strip()
	if value.startswith('#') and len(value) == 9:
		r, g, b = ImageColor.getrgb(value[:7])
		return (r, g, b, int(value[7:9], 16))
	rgb = ImageColor.getrgb(value)
	return rgb if len(rgb) == 4 else (*rgb, 255)


def _wrap(words: list[str], font: ImageFont.FreeTypeFont, max_px: int, stroke: int) -> list[list[int]]:
	"""Greedy word wrap. Returns lines as lists of word indices."""
	lines: list[list[int]] = []
	current: list[int] = []
	for idx, word in enumerate(words):
		candidate = ' '.join(words[i] for i in current + [idx])
		width = font.getlength(candidate) + 2 * stroke
		if current and width > max_px:
			lines.append(current)
			current = [idx]
		else:
			current.append(idx)
	if current:
		lines.append(current)
	return lines


def render_text_image(
	text: str,
	style: TextStyle,
	video_width: int,
	video_height: int,
	highlight_index: int | None = None,
	font_path: str | None = None,
) -> Image.Image:
	"""
	Render a block of text to a tightly cropped transparent RGBA image.

	`highlight_index` (word index) draws that word in the style's highlight colour/pill - used for
	word-by-word karaoke captions.
	"""
	font_size = max(12, int(style.size * video_height))
	font = _font(font_path or DEFAULT_FONT, font_size, style.weight)
	stroke = int(round(style.stroke_width * font_size)) if style.stroke_color else 0
	pad = int(style.box_padding * font_size) if style.box_color else 0
	margin = stroke + (int(font_size * 0.15) if style.shadow else 0) + 4

	display = text.upper() if style.uppercase else text
	words = display.split()
	if not words:
		return Image.new('RGBA', (2, 2), (0, 0, 0, 0))

	max_px = int(style.max_width * video_width) - 2 * (pad + margin)
	lines = _wrap(words, font, max_px, stroke)
	space_w = font.getlength(' ')
	ascent, descent = font.getmetrics()
	line_h = int((ascent + descent) * style.line_spacing)

	line_widths = [sum(font.getlength(words[i]) for i in line) + space_w * (len(line) - 1) for line in lines]
	block_w = int(max(line_widths)) + 2 * stroke
	block_h = line_h * (len(lines) - 1) + ascent + descent + 2 * stroke
	img_w = block_w + 2 * (pad + margin)
	img_h = block_h + 2 * (pad + margin)

	image = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))

	if style.box_color:
		box = Image.new('RGBA', image.size, (0, 0, 0, 0))
		ImageDraw.Draw(box).rounded_rectangle(
			[margin, margin, img_w - margin, img_h - margin], radius=int(font_size * 0.3), fill=_rgba(style.box_color)
		)
		image = Image.alpha_composite(image, box)

	# Word positions (centre-aligned lines)
	positions: list[tuple[int, float, float]] = []
	for line_no, line in enumerate(lines):
		x = (img_w - line_widths[line_no]) / 2
		y = margin + pad + stroke + line_no * line_h
		for i in line:
			positions.append((i, x, y))
			x += font.getlength(words[i]) + space_w

	if highlight_index is not None and style.highlight_box and 0 <= highlight_index < len(words):
		_, hx, hy = next(p for p in positions if p[0] == highlight_index)
		hw = font.getlength(words[highlight_index])
		grow = int(font_size * 0.18)
		pill = Image.new('RGBA', image.size, (0, 0, 0, 0))
		ImageDraw.Draw(pill).rounded_rectangle(
			[hx - grow, hy - grow * 0.6, hx + hw + grow, hy + ascent + descent + grow * 0.2],
			radius=int(font_size * 0.25),
			fill=_rgba(style.highlight_box),
		)
		image = Image.alpha_composite(image, pill)

	if style.shadow:
		shadow = Image.new('RGBA', image.size, (0, 0, 0, 0))
		sdraw = ImageDraw.Draw(shadow)
		offset = max(2, int(font_size * 0.06))
		for i, x, y in positions:
			sdraw.text(
				(x + offset, y + offset), words[i], font=font, fill=(0, 0, 0, 150), stroke_width=stroke, stroke_fill=(0, 0, 0, 150)
			)
		shadow = shadow.filter(ImageFilter.GaussianBlur(max(1, font_size // 14)))
		image = Image.alpha_composite(image, shadow)

	draw = ImageDraw.Draw(image)
	base = _rgba(style.color)
	highlight = _rgba(style.highlight_color) if style.highlight_color else base
	stroke_fill = _rgba(style.stroke_color) if style.stroke_color else None
	for i, x, y in positions:
		fill = highlight if i == highlight_index else base
		draw.text((x, y), words[i], font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)

	return image


def save_text_png(image: Image.Image, folder: str, stem: str = 'text') -> str:
	path = os.path.join(folder, f'{stem}_{uuid.uuid4().hex[:8]}.png')
	image.save(path)
	return path
