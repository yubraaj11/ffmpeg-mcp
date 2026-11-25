"""MCP tools that produce complete videos by combining every editing feature."""

from typing import Literal

from ffmpeg_mcp.composition.models import Composition
from ffmpeg_mcp.composition.presets import build_beat_sync_montage, build_reel_from_clips, build_talking_head_reel
from ffmpeg_mcp.composition.renderer import render
from ffmpeg_mcp.core.formats import FORMATS, PLATFORMS, FormatName
from ffmpeg_mcp.core.runner import success, tool_errors
from ffmpeg_mcp.core.styles import STYLES, TextStyleName
from ffmpeg_mcp.effects.color import ColorPreset
from ffmpeg_mcp.effects.reframe import ReframeMode

TRANSITIONS = [
	'fade', 'fadeblack', 'fadewhite', 'dissolve', 'wipeleft', 'wiperight', 'wipeup', 'wipedown', 'slideleft', 'slideright', 'slideup',
	'slidedown', 'smoothleft', 'smoothright', 'smoothup', 'smoothdown', 'circleopen', 'circleclose', 'circlecrop', 'rectcrop', 'radial',
	'pixelize', 'zoomin', 'hblur', 'squeezeh', 'squeezev', 'coverleft', 'coverright', 'revealleft', 'revealright', 'diagtl', 'diagbr',
]  # fmt: skip


def _result(comp: Composition, output_filename: str | None, dry_run: bool, **extra) -> str:
	result = render(comp, output_filename=output_filename, dry_run=dry_run)
	if dry_run:
		result['composition'] = comp.model_dump(exclude_defaults=True)
	return success(**extra, **result)


@tool_errors
def render_composition(composition: Composition, output_filename: str | None = None, dry_run: bool = False) -> str:
	"""
	Render a complete edited video from a declarative timeline - the tool that combines every feature.

	Pipeline: each clip is trimmed -> speed/speed-ramped -> reframed to the target format -> punch-in zoomed ->
	colour graded; clips are joined with transitions (or hard cuts); then word-synced captions, text titles,
	image/logo overlays and a ducked music bed are added, and the result is exported for the chosen platform
	(H.264/AAC, fast-start, -14 LUFS).

	Times: ClipSpec start/end and speed_ramp use the clip's source seconds; zoom uses seconds within the clip's
	output; text/image overlays use seconds on the final timeline (see dry_run output for clip positions).

	Minimal example:
	    {"format": "reel",
	     "clips": [{"path": "/v/intro.mp4", "end": 4}, {"path": "/v/b.mp4", "start": 2, "end": 6, "speed": 0.5}],
	     "default_transition": {"type": "fade", "duration": 0.4},
	     "text_overlays": [{"text": "My trip", "start": 0, "duration": 2.5}],
	     "captions": {"style": "bold_pop"},
	     "music": {"path": "/m/song.mp3", "volume": 0.25}}

	Args:
	    composition: The timeline spec.
	    output_filename: Optional output file name.
	    dry_run: Validate and return the resolved timeline (clip positions, durations) without rendering.

	Returns:
	    JSON with output_path, duration, resolution, the timeline and (if captions were auto-generated) transcript_path.
	"""
	if not isinstance(composition, Composition):
		composition = Composition.model_validate(composition)
	return _result(composition, output_filename, dry_run)


@tool_errors
def make_reel_from_clips(
	clips: list[str],
	music_path: str | None = None,
	title: str | None = None,
	captions: bool = True,
	caption_style: TextStyleName = 'bold_pop',
	transition: str | None = 'fade',
	transition_duration: float = 0.4,
	color: ColorPreset | None = None,
	target_duration: float | None = None,
	format: FormatName = 'reel',
	reframe_mode: ReframeMode = 'crop',
	output_filename: str | None = None,
	dry_run: bool = False,
) -> str:
	"""
	One call: turn a list of videos/photos into a finished vertical Reel - reframed to 9:16, joined with
	transitions, auto-captioned (when there is speech), titled, colour graded and scored with ducked music.

	Args:
	    clips: Video and/or image paths, in order.
	    music_path: Optional local music file.
	    title: Optional title shown for the first ~3 seconds.
	    captions: Auto-caption speech.
	    caption_style: bold_pop, karaoke, classic, minimal, boxed, ...
	    transition: xfade transition name, or "none" for hard cuts.
	    transition_duration: Seconds per transition.
	    color: Optional look: warm, cool, vintage, bw, vivid, cinematic, matte, moody.
	    target_duration: Optional maximum length; clips are shortened evenly to fit.
	    format: reel (default), square, portrait, landscape, ...
	    reframe_mode: crop, blur_fill or pad.
	    output_filename: Optional output file name.
	    dry_run: Return the generated composition and timeline without rendering.

	Returns:
	    JSON with output_path, duration, resolution and timeline.
	"""
	comp = build_reel_from_clips(
		clips,
		music_path=music_path,
		title=title,
		captions=captions,
		caption_style=caption_style,
		transition=transition,
		transition_duration=transition_duration,
		color=color,
		target_duration=target_duration,
		format=format,
		reframe_mode=reframe_mode,
	)
	return _result(comp, output_filename, dry_run)


@tool_errors
def beat_sync_montage(
	clips: list[str],
	music_path: str,
	cut_every_n_beats: int = 2,
	target_duration: float = 15.0,
	music_start_offset: float = 0.0,
	zoom_on_downbeats: bool = True,
	transition: str | None = None,
	color: ColorPreset | None = None,
	title: str | None = None,
	format: FormatName = 'reel',
	output_filename: str | None = None,
	dry_run: bool = False,
) -> str:
	"""
	One call: a beat-synced montage - detects the song's beats and cuts between your clips exactly on them,
	with punch-in zooms on the downbeats. Clips cycle in order; the music is the only audio.

	Args:
	    clips: Video and/or image paths to cycle through.
	    music_path: Local music file.
	    cut_every_n_beats: 1 = cut on every beat (frantic), 2 = every other beat, 4 = once per bar.
	    target_duration: Approximate length in seconds (ends on a cut point).
	    music_start_offset: Start the song this many seconds in (e.g. at the drop).
	    zoom_on_downbeats: Pulse-zoom on the first beat of each bar.
	    transition: Optional short transition between cuts (e.g. "fade"); default hard cuts.
	    color: Optional look preset.
	    title: Optional title text.
	    format: Output format (default reel 9:16).
	    output_filename: Optional output file name.
	    dry_run: Return the generated composition and timeline without rendering.

	Returns:
	    JSON with output_path, tempo, cut count and timeline.
	"""
	comp, beat_info = build_beat_sync_montage(
		clips,
		music_path,
		cut_every_n_beats=cut_every_n_beats,
		target_duration=target_duration,
		music_start_offset=music_start_offset,
		zoom_on_downbeats=zoom_on_downbeats,
		transition=transition,
		color=color,
		title=title,
		format=format,
	)
	return _result(comp, output_filename, dry_run, tempo=beat_info['tempo'], cuts=beat_info['cuts'])


@tool_errors
def talking_head_reel(
	video_path: str,
	caption_style: TextStyleName = 'karaoke',
	caption_mode: Literal['phrase_highlight', 'word', 'phrase'] = 'phrase_highlight',
	remove_silence: bool = False,
	auto_punch_in_every: float | None = 4.0,
	punch_in_zoom: float = 1.15,
	music_path: str | None = None,
	music_volume: float = 0.12,
	title: str | None = None,
	color: ColorPreset | None = None,
	focus_x: float = 0.5,
	format: FormatName = 'reel',
	output_filename: str | None = None,
	dry_run: bool = False,
) -> str:
	"""
	One call: turn a talking-to-camera recording into a creator-style Reel - vertical crop, animated word-by-word
	captions, alternating punch-in zooms, optional jump cuts that remove pauses, and a quiet ducked music bed.

	Args:
	    video_path: The recording.
	    caption_style: karaoke (default), bold_pop, classic, minimal, boxed.
	    caption_mode: phrase_highlight, word or phrase.
	    remove_silence: Jump-cut out pauses (punch-in alternates on every cut).
	    auto_punch_in_every: Seconds between zoom changes when not jump-cutting; None disables zooms.
	    punch_in_zoom: Zoom factor for punch-ins.
	    music_path: Optional local music file for a background bed.
	    music_volume: Music level under the voice.
	    title: Optional hook/title for the first seconds.
	    color: Optional look preset.
	    focus_x: Horizontal position of the speaker in the source (0-1) for the vertical crop.
	    format: Output format (default reel 9:16).
	    output_filename: Optional output file name.
	    dry_run: Return the generated composition and timeline without rendering.

	Returns:
	    JSON with output_path, transcript_path, duration and timeline.
	"""
	comp = build_talking_head_reel(
		video_path,
		caption_style=caption_style,
		caption_mode=caption_mode,
		remove_silence=remove_silence,
		auto_punch_in_every=auto_punch_in_every,
		punch_in_zoom=punch_in_zoom,
		music_path=music_path,
		music_volume=music_volume,
		title=title,
		color=color,
		focus_x=focus_x,
		format=format,
	)
	return _result(comp, output_filename, dry_run)


@tool_errors
def get_editing_capabilities() -> str:
	"""
	List the options the editing tools accept: output formats, platforms, caption/text styles, colour presets,
	transitions, positions and animations. Call this before building a composition.
	"""
	return success(
		formats={k: f'{w}x{h}' for k, (w, h) in FORMATS.items()},
		platforms={k: {'format': v['format'], 'max_duration': v['max_duration']} for k, v in PLATFORMS.items()},
		text_styles=list(STYLES),
		caption_modes=['phrase_highlight', 'word', 'phrase'],
		color_presets=['warm', 'cool', 'vintage', 'bw', 'vivid', 'cinematic', 'matte', 'moody'],
		transitions=TRANSITIONS + ['none'],
		reframe_modes=['crop', 'blur_fill', 'pad'],
		positions=[
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
		],  # fmt: skip
		text_animations=['none', 'fade', 'slide_up', 'slide_down'],
		zoom_eases=['smooth', 'snap'],
	)
