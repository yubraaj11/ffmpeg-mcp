"""One-call recipes. Each builds a Composition spec and renders it with the composition engine."""

from ffmpeg_mcp.composition.models import Captions, ClipSpec, Composition, Music, TextOverlay, Transition, ZoomSegment
from ffmpeg_mcp.composition.renderer import render
from ffmpeg_mcp.core.beats import detect_beats
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.silence import detect_silences, speech_ranges


def _transition(name: str | None, duration: float) -> Transition | None:
	if not name or name == 'none':
		return None
	return Transition(type=name, duration=duration)


def _title(title: str | None, total: float) -> list[TextOverlay]:
	if not title:
		return []
	return [
		TextOverlay(
			text=title, start=0.0, duration=max(0.5, min(3.0, total - 0.1)), style='title', position='top_center', animation='slide_up'
		)
	]


def build_reel_from_clips(
	clips: list[str],
	music_path: str | None = None,
	title: str | None = None,
	captions: bool = True,
	caption_style: str = 'bold_pop',
	transition: str | None = 'fade',
	transition_duration: float = 0.4,
	color: str | None = None,
	target_duration: float | None = None,
	format: str = 'reel',
	reframe_mode: str = 'crop',
) -> Composition:
	if not clips:
		raise ValueError('Provide at least one clip')
	specs: list[ClipSpec] = []
	lengths: list[float] = []
	any_audio = False
	for path in clips:
		spec = ClipSpec(path=path)
		if spec.is_image:
			lengths.append(spec.image_duration)
		else:
			info = probe_media(path)
			any_audio = any_audio or info.has_audio
			lengths.append(info.duration)
		specs.append(spec)

	trans = _transition(transition, transition_duration)
	overlap = (trans.duration if trans else 0.0) * (len(specs) - 1)
	total = sum(lengths) - overlap
	if target_duration and total > target_duration:
		# Shorten every clip by the same factor, keeping each clip's beginning.
		budget = target_duration + overlap
		factor = budget / sum(lengths)
		for spec, length in zip(specs, lengths):
			keep = max(0.5, length * factor)
			if spec.is_image:
				spec.image_duration = keep
			else:
				spec.end = keep
		total = target_duration

	music = None
	if music_path:
		music = Music(path=music_path, volume=0.25 if any_audio else 0.9, duck=any_audio)
	return Composition(
		format=format,
		reframe_mode=reframe_mode,
		clips=specs,
		default_transition=trans,
		text_overlays=_title(title, total),
		captions=Captions(style=caption_style) if (captions and any_audio) else None,
		music=music,
		color=color,
	)


def build_beat_sync_montage(
	clips: list[str],
	music_path: str,
	cut_every_n_beats: int = 2,
	target_duration: float = 15.0,
	music_start_offset: float = 0.0,
	zoom_on_downbeats: bool = True,
	transition: str | None = None,
	color: str | None = None,
	title: str | None = None,
	format: str = 'reel',
	fps: int = 30,
) -> tuple[Composition, dict]:
	if not clips:
		raise ValueError('Provide at least one clip')
	if cut_every_n_beats < 1:
		raise ValueError('cut_every_n_beats must be >= 1')
	beats = detect_beats(music_path, start_offset=music_start_offset, max_duration=target_duration + 10)
	times = beats['beats']
	if len(times) < 2:
		raise ValueError('Not enough beats detected in the music; try a different track or start offset')

	first = times[0]
	rel = [t - first for t in times]
	downbeats = {round(t - first, 2) for t in beats['downbeats']}
	cuts = [t for t in rel[::cut_every_n_beats] if t <= target_duration + 1e-3]
	if len(cuts) < 2:
		raise ValueError(f'target_duration {target_duration}s is shorter than {cut_every_n_beats} beats at {beats["tempo"]} BPM')
	frames = [round(c * fps) for c in cuts]
	seg_lengths = [(frames[i + 1] - frames[i]) / fps for i in range(len(frames) - 1)]

	infos = {}
	for path in clips:
		if not ClipSpec(path=path).is_image:
			infos[path] = probe_media(path)
	cursors = {path: 0.0 for path in clips}
	specs: list[ClipSpec] = []
	trans = _transition(transition, 0.15)
	for k, seg in enumerate(seg_lengths):
		path = clips[k % len(clips)]
		zoom = None
		if zoom_on_downbeats and round(cuts[k], 2) in downbeats:
			zoom = [ZoomSegment(start=0.0, end=max(0.1, seg * 0.6), zoom=1.15, ease='smooth', ramp=0.06)]
		if path not in infos:
			specs.append(ClipSpec(path=path, image_duration=seg, mute=True, zoom=zoom, transition_in=trans))
			continue
		dur = infos[path].duration
		if seg >= dur - 0.05:
			# Source shorter than the beat gap: slow it down to fill the gap.
			specs.append(ClipSpec(path=path, start=0.0, end=dur, speed=max(0.1, dur / seg), mute=True, zoom=zoom, transition_in=trans))
			continue
		start = cursors[path]
		if start + seg > dur:
			start = 0.0
		cursors[path] = start + seg
		specs.append(ClipSpec(path=path, start=start, end=start + seg, mute=True, zoom=zoom, transition_in=trans))

	total = (frames[-1] - frames[0]) / fps
	comp = Composition(
		format=format,
		fps=fps,
		clips=specs,
		text_overlays=_title(title, total),
		music=Music(path=music_path, volume=1.0, duck=False, fade_in=0.0, fade_out=1.0, start_offset=music_start_offset + first),
		color=color,
	)
	return comp, {'tempo': beats['tempo'], 'cuts': len(specs), 'cut_points': [round(c, 3) for c in cuts]}


def build_talking_head_reel(
	video_path: str,
	caption_style: str = 'karaoke',
	caption_mode: str = 'phrase_highlight',
	remove_silence: bool = False,
	auto_punch_in_every: float | None = 4.0,
	punch_in_zoom: float = 1.15,
	music_path: str | None = None,
	music_volume: float = 0.12,
	title: str | None = None,
	color: str | None = None,
	focus_x: float = 0.5,
	format: str = 'reel',
) -> Composition:
	info = probe_media(video_path)
	if not info.has_audio:
		raise ValueError('talking_head_reel needs a video with speech audio')
	specs: list[ClipSpec] = []
	if remove_silence:
		ranges = speech_ranges(info.duration, detect_silences(video_path))
		if not ranges:
			raise ValueError('No speech detected - try remove_silence=False')
		for i, (s, e) in enumerate(ranges):
			zoom = [ZoomSegment(start=0.0, end=e - s, zoom=punch_in_zoom, ease='snap')] if (auto_punch_in_every and i % 2 == 1) else None
			specs.append(ClipSpec(path=video_path, start=s, end=e, zoom=zoom, focus_x=focus_x))
		total = sum(e - s for s, e in ranges)
	else:
		zooms = []
		if auto_punch_in_every and auto_punch_in_every > 0:
			t, k = 0.0, 0
			while t < info.duration:
				end = min(info.duration, t + auto_punch_in_every)
				if k % 2 == 1 and end - t > 0.2:
					zooms.append(ZoomSegment(start=t, end=end, zoom=punch_in_zoom, ease='snap'))
				t, k = end, k + 1
		specs.append(ClipSpec(path=video_path, zoom=zooms or None, focus_x=focus_x))
		total = info.duration

	return Composition(
		format=format,
		clips=specs,
		text_overlays=_title(title, total),
		captions=Captions(style=caption_style, mode=caption_mode),
		music=Music(path=music_path, volume=music_volume, duck=True) if music_path else None,
		color=color,
	)


__all__ = ['build_reel_from_clips', 'build_beat_sync_montage', 'build_talking_head_reel', 'render']
