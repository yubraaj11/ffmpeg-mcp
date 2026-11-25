from dataclasses import dataclass, replace
from typing import Literal

TextStyleName = Literal['bold_pop', 'karaoke', 'classic', 'minimal', 'boxed', 'title', 'subtitle']


@dataclass(frozen=True)
class TextStyle:
	weight: str = 'ExtraBold'  # Montserrat variation name
	size: float = 0.045  # font size as a fraction of the video height
	color: str = '#FFFFFF'
	highlight_color: str | None = None  # colour of the active word in captions
	highlight_box: str | None = None  # background pill behind the active word
	stroke_color: str | None = '#000000'
	stroke_width: float = 0.12  # stroke width as a fraction of the font size
	box_color: str | None = None  # background box behind the whole block (supports #RRGGBBAA)
	box_padding: float = 0.35  # fraction of the font size
	shadow: bool = False
	uppercase: bool = False
	line_spacing: float = 1.15
	max_width: float = 0.86  # fraction of video width before wrapping


STYLES: dict[str, TextStyle] = {
	'bold_pop': TextStyle(uppercase=True, size=0.05, highlight_color='#FFE600', stroke_width=0.14, shadow=True),
	'karaoke': TextStyle(weight='Black', size=0.046, highlight_color='#FFFFFF', highlight_box='#7C3AEDFF', stroke_width=0.1, shadow=True),
	'classic': TextStyle(weight='SemiBold', size=0.036, stroke_color=None, box_color='#000000A6', box_padding=0.3),
	'minimal': TextStyle(weight='SemiBold', size=0.038, stroke_color=None, shadow=True),
	'boxed': TextStyle(weight='Bold', size=0.04, color='#111111', stroke_color=None, box_color='#FFFFFFFF', box_padding=0.35),
	'title': TextStyle(weight='Black', size=0.07, uppercase=True, stroke_width=0.08, shadow=True, max_width=0.9),
	'subtitle': TextStyle(weight='Medium', size=0.035, stroke_color=None, shadow=True),
}


def get_style(name: str, **overrides) -> TextStyle:
	if name not in STYLES:
		raise ValueError(f'Unknown style "{name}". Choose one of: {", ".join(STYLES)}')
	clean = {k: v for k, v in overrides.items() if v is not None}
	return replace(STYLES[name], **clean) if clean else STYLES[name]
