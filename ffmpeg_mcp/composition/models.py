from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ffmpeg_mcp.core.formats import FormatName, PlatformName
from ffmpeg_mcp.core.styles import TextStyleName
from ffmpeg_mcp.effects.color import ColorPreset
from ffmpeg_mcp.effects.reframe import ReframeMode
from ffmpeg_mcp.effects.text import Position, TextAnimation

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff')


class SpeedSegment(BaseModel):
	"""Speed change for part of a clip. Times are seconds from the clip's trimmed start (before speed changes)."""

	start: float = Field(ge=0)
	end: float = Field(gt=0)
	speed: float | None = Field(default=None, description='Constant speed for the segment, e.g. 0.5 = slow motion, 2 = double speed')
	speed_start: float | None = Field(default=None, description='Gradual ramp: speed at segment start')
	speed_end: float | None = Field(default=None, description='Gradual ramp: speed at segment end')

	@model_validator(mode='after')
	def _check(self):
		if self.speed is None and (self.speed_start is None or self.speed_end is None):
			raise ValueError('Give either speed, or both speed_start and speed_end')
		return self


class ZoomSegment(BaseModel):
	"""Punch-in zoom. Times are seconds in the clip's output (after trimming and speed changes)."""

	start: float = Field(ge=0)
	end: float = Field(gt=0)
	zoom: float = Field(default=1.2, ge=1.0, le=4.0)
	center_x: float = Field(default=0.5, ge=0, le=1, description='Zoom focus, fraction of width')
	center_y: float = Field(default=0.5, ge=0, le=1, description='Zoom focus, fraction of height')
	ease: Literal['smooth', 'snap'] = 'smooth'
	ramp: float = Field(default=0.3, ge=0, description='Seconds to ease in/out when ease="smooth"')


class Transition(BaseModel):
	type: str = Field(
		default='fade',
		description='xfade transition name (fade, wipeleft, slideup, circleopen, dissolve, zoomin, ...) or "none" for a hard cut',
	)
	duration: float = Field(default=0.4, gt=0, le=3)


class ClipSpec(BaseModel):
	path: str = Field(description='Video or image file. Images become still clips (with a gentle ken-burns zoom by default).')
	start: float = Field(default=0.0, ge=0, description='Trim start (seconds in the source)')
	end: float | None = Field(default=None, description='Trim end (seconds in the source); None = end of file')
	image_duration: float = Field(default=3.0, gt=0, description='Length of an image clip')
	speed: float = Field(default=1.0, ge=0.1, le=10)
	speed_ramp: list[SpeedSegment] | None = None
	zoom: list[ZoomSegment] | None = None
	ken_burns: float | None = Field(default=None, ge=1.0, le=2.0, description='Slow zoom reaching this factor by the clip end, e.g. 1.1')
	color: ColorPreset | None = None
	volume: float = Field(default=1.0, ge=0, le=4)
	mute: bool = False
	reframe_mode: ReframeMode | None = Field(default=None, description='Override the composition reframe_mode for this clip')
	focus_x: float = Field(default=0.5, ge=0, le=1, description='Horizontal focus when cropping to the target format')
	focus_y: float = Field(default=0.5, ge=0, le=1)
	transition_in: Transition | None = Field(default=None, description='Transition from the previous clip; overrides default_transition')

	@property
	def is_image(self) -> bool:
		return self.path.lower().endswith(IMAGE_EXTENSIONS)


class TextOverlay(BaseModel):
	text: str
	start: float = Field(default=0.0, ge=0, description='Seconds on the final timeline')
	duration: float = Field(default=3.0, gt=0)
	style: TextStyleName = 'title'
	position: Position = 'top_center'
	x: float | None = Field(default=None, ge=0, le=1, description='Explicit centre x (fraction of width); needs y too')
	y: float | None = Field(default=None, ge=0, le=1)
	animation: TextAnimation = 'fade'
	color: str | None = Field(default=None, description='Override text colour, e.g. #FFE600')
	size: float | None = Field(default=None, gt=0, le=0.3, description='Override font size as a fraction of video height')


class ImageOverlay(BaseModel):
	path: str
	start: float = Field(default=0.0, ge=0)
	duration: float | None = Field(default=None, gt=0, description='None = until the end')
	position: Position = 'top_right'
	x: float | None = Field(default=None, ge=0, le=1)
	y: float | None = Field(default=None, ge=0, le=1)
	width: int | None = Field(default=200, gt=0, description='Width in px (aspect ratio kept); None = original size')
	opacity: float = Field(default=1.0, ge=0, le=1)
	animation: TextAnimation = 'fade'


class Captions(BaseModel):
	enabled: bool = True
	style: TextStyleName = 'bold_pop'
	mode: Literal['phrase_highlight', 'word', 'phrase'] = 'phrase_highlight'
	words_per_line: int = Field(default=3, ge=1, le=8)
	position: Position = 'caption'
	transcript_path: str | None = Field(
		default=None, description='Use this transcript (.json from transcribe_audio, or .srt) instead of auto-transcribing'
	)
	model_size: str = Field(default='base', description='faster-whisper model: tiny, base, small, medium, large-v3')
	language: str | None = Field(default=None, description='ISO code, e.g. "en"; None = auto-detect')


class Music(BaseModel):
	path: str
	volume: float = Field(default=0.25, ge=0, le=2)
	duck: bool = Field(default=True, description='Lower the music automatically while there is speech')
	fade_in: float = Field(default=0.5, ge=0)
	fade_out: float = Field(default=1.5, ge=0)
	start_offset: float = Field(default=0.0, ge=0, description='Start the song from this many seconds in')


class Export(BaseModel):
	platform: PlatformName = 'instagram_reel'
	crf: int = Field(default=20, ge=14, le=32)
	preset: Literal['ultrafast', 'veryfast', 'faster', 'fast', 'medium', 'slow'] = 'medium'
	normalize_loudness: bool = True
	target_lufs: float = Field(default=-14.0, ge=-30, le=-8)


class Composition(BaseModel):
	format: FormatName = 'reel'
	fps: int = Field(default=30, ge=12, le=60)
	reframe_mode: ReframeMode = 'crop'
	clips: list[ClipSpec] = Field(min_length=1)
	default_transition: Transition | None = Field(default=None, description='Transition between every pair of clips; None = hard cuts')
	text_overlays: list[TextOverlay] = Field(default_factory=list)
	image_overlays: list[ImageOverlay] = Field(default_factory=list)
	captions: Captions | None = None
	music: Music | None = None
	color: ColorPreset | None = Field(default=None, description='Grade applied to every clip without its own color')
	export: Export = Field(default_factory=Export)
