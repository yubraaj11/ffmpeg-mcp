import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import ffmpeg

from ffmpeg_mcp.composition.models import ClipSpec, Composition
from ffmpeg_mcp.core.captions import build_caption_track, load_words
from ffmpeg_mcp.core.formats import PLATFORMS, resolve_format
from ffmpeg_mcp.core.loudness import correct_loudness
from ffmpeg_mcp.core.paths import category_dir, job_dir, output_path
from ffmpeg_mcp.core.probe import probe_media
from ffmpeg_mcp.core.runner import INTERMEDIATE_AUDIO, INTERMEDIATE_VIDEO, run
from ffmpeg_mcp.core.styles import get_style
from ffmpeg_mcp.core.text_render import render_text_image, save_text_png
from ffmpeg_mcp.core.transcribe import transcribe
from ffmpeg_mcp.effects.audio import loudness_normalize, mix_music, music_bed, normalize_audio, silent_audio
from ffmpeg_mcp.effects.color import apply_color
from ffmpeg_mcp.effects.reframe import reframe
from ffmpeg_mcp.effects.speed import apply_speed, build_speed_pieces
from ffmpeg_mcp.effects.text import overlay_image_track, overlay_png
from ffmpeg_mcp.effects.zoom import apply_zoom

logger = logging.getLogger(__name__)
MAX_WORKERS = max(1, min(4, (os.cpu_count() or 2) // 2))


# --------------------------------------------------------------------------- timeline


def _check_file(path: str, what: str) -> None:
	if not os.path.isfile(path):
		raise FileNotFoundError(f'{what} not found: {path}')
	if os.path.getsize(path) == 0:
		raise ValueError(f'{what} is empty: {path}')


def resolve_timeline(comp: Composition) -> dict:
	"""Validate inputs and compute exact (frame-aligned) durations and timeline positions for every clip."""
	fps = comp.fps
	width, height = resolve_format(comp.format)
	clips = []
	total = 0.0
	for idx, clip in enumerate(comp.clips):
		_check_file(clip.path, f'Clip {idx}')
		if clip.is_image:
			src_start, src_end, has_audio = 0.0, clip.image_duration, False
		else:
			info = probe_media(clip.path)
			if not info.has_video:
				raise ValueError(f'Clip {idx} has no video stream: {clip.path}')
			src_start = clip.start
			src_end = min(clip.end, info.duration) if clip.end is not None else info.duration
			has_audio = info.has_audio
			if src_end - src_start <= 0.05:
				raise ValueError(f'Clip {idx} trim range is empty ({src_start}s - {src_end}s, file is {info.duration:.2f}s)')
		src_len = src_end - src_start
		if clip.speed_ramp:
			pieces = build_speed_pieces(src_len, [s.model_dump(exclude_none=True) for s in clip.speed_ramp])
			out_len = sum((e - s) / spd for s, e, spd in pieces)
		else:
			out_len = src_len / clip.speed
		frames = max(1, round(out_len * fps))
		out_len = frames / fps

		transition = clip.transition_in if clip.transition_in is not None else comp.default_transition
		t_dur = 0.0
		t_type = 'none'
		if idx > 0 and transition is not None and transition.type != 'none':
			prev_len = clips[-1]['duration']
			t_dur = min(transition.duration, prev_len / 2, out_len / 2)
			t_dur = round(t_dur * fps) / fps
			t_type = transition.type if t_dur > 0 else 'none'
		start = total - t_dur
		total = start + out_len
		clips.append(
			{
				'index': idx,
				'path': clip.path,
				'is_image': clip.is_image,
				'has_audio': has_audio and not clip.mute,
				'source_start': round(src_start, 3),
				'source_end': round(src_end, 3),
				'duration': out_len,
				'frames': frames,
				'timeline_start': round(start, 3),
				'timeline_end': round(total, 3),
				'transition_in': {'type': t_type, 'duration': t_dur} if idx > 0 else None,
			}
		)

	for t in comp.text_overlays:
		if t.start >= total:
			raise ValueError(f'Text overlay "{t.text}" starts at {t.start}s but the video is only {total:.2f}s long')
	for o in comp.image_overlays:
		_check_file(o.path, 'Overlay image')
	if comp.music:
		_check_file(comp.music.path, 'Music file')
	if comp.captions and comp.captions.enabled and comp.captions.transcript_path:
		_check_file(comp.captions.transcript_path, 'Transcript')

	warnings = []
	max_dur = PLATFORMS[comp.export.platform]['max_duration']
	if max_dur and total > max_dur:
		warnings.append(f'Duration {total:.1f}s exceeds the {comp.export.platform} limit of {max_dur}s')
	return {
		'width': width,
		'height': height,
		'fps': fps,
		'duration': round(total, 3),
		'clips': clips,
		'warnings': warnings,
	}


# --------------------------------------------------------------------------- stage 1: clips


def render_clip(clip: ClipSpec, entry: dict, comp: Composition, width: int, height: int, out_path: str) -> str:
	fps = comp.fps
	duration = entry['duration']
	src_len = entry['source_end'] - entry['source_start']

	if clip.is_image:
		v = ffmpeg.input(clip.path, loop=1, framerate=fps, t=f'{src_len:.4f}').video
		a = None
	else:
		inp = ffmpeg.input(clip.path, ss=entry['source_start'], t=f'{src_len:.4f}')
		v = inp.video
		a = inp.audio if entry['has_audio'] else None

	v = v.filter('setpts', 'PTS-STARTPTS')
	if a is not None:
		a = a.filter('asetpts', 'PTS-STARTPTS')
	ramp = [s.model_dump(exclude_none=True) for s in clip.speed_ramp] if clip.speed_ramp else None
	v, a, _ = apply_speed(v, a, src_len, speed=clip.speed, ramp=ramp)

	v = reframe(v, width, height, mode=clip.reframe_mode or comp.reframe_mode, focus_x=clip.focus_x, focus_y=clip.focus_y)
	v = v.filter('fps', fps)
	ken_burns = clip.ken_burns if clip.ken_burns is not None else (1.08 if clip.is_image else None)
	zooms = [z.model_dump() for z in clip.zoom] if clip.zoom else []
	v = apply_zoom(v, width, height, zooms, duration, ken_burns=ken_burns)
	v = apply_color(v, preset=clip.color or comp.color)
	# Pad/trim to the exact frame count so transitions line up precisely.
	v = (
		v.filter('tpad', stop_mode='clone', stop_duration=1)
		.trim(end_frame=entry['frames'])
		.setpts('PTS-STARTPTS')
		.filter('format', 'yuv420p')
	)

	if a is None:
		a = silent_audio(duration)
	else:
		a = normalize_audio(a)
		if clip.volume != 1.0:
			a = a.filter('volume', clip.volume)
	a = a.filter('apad').filter('atrim', duration=f'{duration:.4f}').filter('asetpts', 'PTS-STARTPTS')

	run(
		ffmpeg.output(v, a, out_path, r=fps, **INTERMEDIATE_VIDEO, **INTERMEDIATE_AUDIO),
		f'clip {entry["index"]} ({os.path.basename(clip.path)})',
	)
	return out_path


# --------------------------------------------------------------------------- stage 2: join


def join_clips(paths: list[str], timeline: dict, out_path: str) -> str:
	entries = timeline['clips']
	if len(paths) == 1:
		return paths[0]
	inputs = [ffmpeg.input(p) for p in paths]
	v, a = inputs[0].video, inputs[0].audio
	length = entries[0]['duration']
	for i in range(1, len(paths)):
		vi, ai = inputs[i].video, inputs[i].audio
		trans = entries[i]['transition_in']
		if trans and trans['type'] != 'none' and trans['duration'] > 0:
			d = trans['duration']
			v = ffmpeg.filter([v, vi], 'xfade', transition=trans['type'], duration=f'{d:.4f}', offset=f'{length - d:.4f}')
			a = ffmpeg.filter([a, ai], 'acrossfade', d=f'{d:.4f}', c1='tri', c2='tri')
			length += entries[i]['duration'] - d
		else:
			joined = ffmpeg.concat(v, a, vi, ai, n=2, v=1, a=1).node
			v, a = joined[0], joined[1]
			length += entries[i]['duration']
	run(ffmpeg.output(v, a, out_path, r=timeline['fps'], **INTERMEDIATE_VIDEO, **INTERMEDIATE_AUDIO), 'joining clips')
	return out_path


# --------------------------------------------------------------------------- stage 3: finishing


def export_args(comp: Composition) -> dict:
	platform = PLATFORMS[comp.export.platform]
	bitrate = platform['video_bitrate']
	return {
		'vcodec': 'libx264',
		'profile:v': 'high',
		'pix_fmt': 'yuv420p',
		'crf': comp.export.crf,
		'preset': comp.export.preset,
		'maxrate': bitrate,
		'bufsize': f'{int(bitrate[:-1]) * 2}M',
		'r': comp.fps,
		'acodec': 'aac',
		'audio_bitrate': '192k',
		'ar': 48000,
		'ac': 2,
		'movflags': '+faststart',
	}


def finish(joined: str, comp: Composition, timeline: dict, work_dir: str, out_path: str) -> dict:
	width, height, fps, duration = timeline['width'], timeline['height'], timeline['fps'], timeline['duration']
	inp = ffmpeg.input(joined)
	v, a = inp.video, inp.audio
	extra = {}

	if comp.captions and comp.captions.enabled:
		cap = comp.captions
		if cap.transcript_path:
			words = load_words(cap.transcript_path)
		else:
			result = transcribe(joined, work_dir, model_size=cap.model_size, language=cap.language)
			words = result['words']
			transcript_file = output_path('transcripts', None, 'composition_transcript', '.json')
			with open(transcript_file, 'w', encoding='utf-8') as f:
				json.dump(result, f, indent=2, ensure_ascii=False)
			extra['transcript_path'] = transcript_file
			extra['transcript_hint'] = 'Edit this JSON to fix words, then pass it as captions.transcript_path to re-render.'
		track = build_caption_track(
			words,
			get_style(cap.style),
			width,
			height,
			duration,
			work_dir,
			mode=cap.mode,
			words_per_line=cap.words_per_line,
			position=cap.position,
		)
		if track:
			v = overlay_image_track(v, track, fps)
		extra['caption_words'] = len(words)

	text_dir = os.path.join(work_dir, 'text')
	os.makedirs(text_dir, exist_ok=True)
	for t in comp.text_overlays:
		style = get_style(t.style, color=t.color, size=t.size)
		png = save_text_png(render_text_image(t.text, style, width, height), text_dir)
		v = overlay_png(
			v, png, t.start, min(t.duration, duration - t.start), fps, position=t.position, x=t.x, y=t.y, animation=t.animation
		)

	for o in comp.image_overlays:
		dur = o.duration if o.duration is not None else duration - o.start
		dur = min(dur, duration - o.start)
		scale = (o.width, -1) if o.width else None
		v = overlay_png(
			v, o.path, o.start, dur, fps, position=o.position, x=o.x, y=o.y, animation=o.animation, opacity=o.opacity, scale=scale
		)

	if comp.music:
		m = comp.music
		bed = music_bed(m.path, duration, volume=m.volume, fade_in=m.fade_in, fade_out=m.fade_out, start_offset=m.start_offset)
		voice = None if all(not c['has_audio'] for c in timeline['clips']) else a
		a = mix_music(voice, bed, duck=m.duck)
	if comp.export.normalize_loudness:
		a = loudness_normalize(a, comp.export.target_lufs)

	run(ffmpeg.output(v, a, out_path, t=f'{duration:.4f}', **export_args(comp)), 'final export')
	if comp.export.normalize_loudness:
		lufs = correct_loudness(out_path, comp.export.target_lufs)
		if lufs is not None:
			extra['loudness_lufs'] = round(lufs, 1)
	return extra


# --------------------------------------------------------------------------- entry point


def render(comp: Composition, output_filename: str | None = None, dry_run: bool = False) -> dict:
	timeline = resolve_timeline(comp)
	if dry_run:
		return {'dry_run': True, 'timeline': timeline}

	out_path = output_path('compositions', output_filename, f'{comp.format}')
	category_dir('compositions')
	with job_dir('composition') as work:
		width, height = timeline['width'], timeline['height']
		clip_paths = [os.path.join(work, f'clip_{i:03}.mp4') for i in range(len(comp.clips))]
		with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
			futures = [
				pool.submit(render_clip, clip, entry, comp, width, height, path)
				for clip, entry, path in zip(comp.clips, timeline['clips'], clip_paths)
			]
			for f in futures:
				f.result()
		joined = join_clips(clip_paths, timeline, os.path.join(work, 'joined.mp4'))
		extra = finish(joined, comp, timeline, work, out_path)

	info = probe_media(out_path)
	return {
		'output_path': out_path,
		'duration': round(info.duration, 3),
		'resolution': f'{info.width}x{info.height}',
		'fps': comp.fps,
		**extra,
		'warnings': timeline['warnings'],
		'timeline': [{k: c[k] for k in ('index', 'path', 'timeline_start', 'timeline_end', 'transition_in')} for c in timeline['clips']],
	}
