import os

import ffmpeg
from PIL import Image, ImageDraw

from ffmpeg_mcp.core.paths import job_dir, output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import run, tool_errors
from ffmpeg_mcp.core.text_render import DEFAULT_FONT, _font
from utils import validate_input_video_path


@tool_errors
@validate_input_video_path
def render_preview(
	input_video_path: str,
	number_of_frames: int = 8,
	columns: int = 4,
	thumb_width: int = 320,
	timestamps: list[float] | None = None,
) -> str:
	"""
	Render a contact sheet (one PNG with timestamped thumbnails) so the edit can be checked visually.

	Args:
	    input_video_path: Video to preview.
	    number_of_frames: Evenly spaced frames to include (ignored when timestamps is given).
	    columns: Thumbnails per row.
	    thumb_width: Width of each thumbnail in px.
	    timestamps: Exact times (seconds) to sample instead.

	Returns:
	    Path to the contact sheet PNG.
	"""
	info = probe_media(input_video_path)
	if timestamps:
		times = [t for t in timestamps if 0 <= t < info.duration]
	else:
		n = max(1, min(number_of_frames, 48))
		times = [info.duration * (i + 0.5) / n for i in range(n)]
	if not times:
		raise ValueError(f'No valid timestamps inside the video (0 - {info.duration:.2f}s)')
	thumb_h = int(thumb_width * info.height / info.width) // 2 * 2
	thumbs = []
	with job_dir('preview') as work:
		for i, t in enumerate(times):
			path = os.path.join(work, f'f{i:03}.png')
			run(
				ffmpeg.input(input_video_path, ss=f'{t:.3f}').video.filter('scale', thumb_width, thumb_h).output(path, vframes=1),
				f'frame at {t:.2f}s',
			)
			thumbs.append((t, Image.open(path).convert('RGB')))
		cols = max(1, min(columns, len(thumbs)))
		rows = (len(thumbs) + cols - 1) // cols
		gap = 6
		sheet = Image.new('RGB', (cols * (thumb_width + gap) + gap, rows * (thumb_h + gap) + gap), (24, 24, 24))
		font = _font(DEFAULT_FONT, max(12, thumb_width // 14), 'Bold')
		for i, (t, img) in enumerate(thumbs):
			x = gap + (i % cols) * (thumb_width + gap)
			y = gap + (i // cols) * (thumb_h + gap)
			sheet.paste(img, (x, y))
			label = f'{t:.2f}s'
			draw = ImageDraw.Draw(sheet)
			draw.text((x + 6, y + 4), label, font=font, fill='white', stroke_width=2, stroke_fill='black')
	out = output_path('previews', None, 'preview', '.png')
	sheet.save(out)
	return out
