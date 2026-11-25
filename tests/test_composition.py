import pytest

from ffmpeg_mcp.composition.models import Composition
from ffmpeg_mcp.composition.renderer import resolve_timeline
from ffmpeg_mcp.core.captions import caption_timeline, group_words
from ffmpeg_mcp.effects.speed import build_speed_pieces
from ffmpeg_mcp.services import beat_sync_montage, make_reel_from_clips, render_composition, talking_head_reel
from tests.conftest import info, parse


def test_speed_pieces_fill_gaps():
	pieces = build_speed_pieces(5.0, [{'start': 1, 'end': 2, 'speed': 0.5}])
	assert pieces == [(0.0, 1.0, 1.0), (1.0, 2.0, 0.5), (2.0, 5.0, 1.0)]


def test_speed_pieces_reject_overlap():
	with pytest.raises(ValueError):
		build_speed_pieces(5.0, [{'start': 1, 'end': 3, 'speed': 2}, {'start': 2, 'end': 4, 'speed': 2}])


def test_caption_grouping():
	words = [{'word': w, 'start': i * 0.3, 'end': i * 0.3 + 0.25} for i, w in enumerate('one two three. four five six seven'.split())]
	chunks = group_words(words, max_words=3)
	assert [len(c) for c in chunks] == [3, 3, 1]
	states = caption_timeline(words, mode='phrase_highlight')
	assert len(states) == len(words)
	assert all(s[0] < s[1] for s in states)
	assert all(a[1] <= b[0] + 1e-9 for a, b in zip(states, states[1:]))


def test_timeline_math(media):
	comp = Composition.model_validate(
		{
			'clips': [
				{'path': media['landscape'], 'end': 3},
				{'path': media['silent'], 'end': 2, 'speed': 0.5},
				{'path': media['photo'], 'image_duration': 2},
			],
			'default_transition': {'type': 'fade', 'duration': 0.5},
		}
	)
	t = resolve_timeline(comp)
	assert t['duration'] == pytest.approx(3 + 4 + 2 - 1.0, abs=0.05)
	assert t['clips'][1]['timeline_start'] == pytest.approx(2.5, abs=0.05)
	assert t['clips'][1]['has_audio'] is False


def test_render_composition_dry_run(media):
	data = parse(render_composition(composition={'clips': [{'path': media['landscape']}]}, dry_run=True))
	assert data['dry_run'] is True
	assert data['timeline']['width'] == 1080


def test_render_composition_missing_file():
	data = render_composition(composition={'clips': [{'path': '/missing.mp4'}]})
	assert '"ERROR"' in data


def test_render_composition_full(media):
	spec = {
		'format': 'reel',
		'clips': [
			{'path': media['landscape'], 'start': 0.5, 'end': 3.5, 'zoom': [{'start': 1, 'end': 2, 'zoom': 1.3}], 'color': 'warm'},
			{'path': media['silent'], 'end': 3, 'speed_ramp': [{'start': 0, 'end': 2, 'speed_start': 1, 'speed_end': 2.5}]},
			{'path': media['photo'], 'image_duration': 2, 'transition_in': {'type': 'slideup', 'duration': 0.3}},
		],
		'default_transition': {'type': 'fade', 'duration': 0.4},
		'text_overlays': [{'text': 'Test Reel', 'start': 0, 'duration': 2}],
		'image_overlays': [{'path': media['photo'], 'width': 120}],
		'music': {'path': media['music'], 'volume': 0.3},
	}
	data = parse(render_composition(composition=spec, output_filename='pytest_full.mp4'))
	i = info(data['output_path'])
	assert (i.width, i.height) == (1080, 1920)
	assert i.has_audio
	timeline = parse(render_composition(composition=spec, dry_run=True))['timeline']
	assert i.duration == pytest.approx(timeline['duration'], abs=0.1)
	assert abs(data['loudness_lufs'] + 14) <= 1.0


def test_make_reel_from_clips(media):
	data = parse(
		make_reel_from_clips(clips=[media['landscape'], media['photo']], music_path=media['music'], title='Hello', target_duration=5)
	)
	i = info(data['output_path'])
	assert (i.width, i.height) == (1080, 1920)
	assert i.duration == pytest.approx(5, abs=0.3)


def test_beat_sync_montage(media):
	data = parse(
		beat_sync_montage(clips=[media['landscape'], media['silent'], media['photo']], music_path=media['music'], target_duration=6)
	)
	assert 115 <= data['tempo'] <= 125
	starts = [c['timeline_start'] for c in data['timeline']]
	# cut every 2 beats at 120 BPM -> one cut per second
	assert all(abs((b - a) - 1.0) < 0.07 for a, b in zip(starts, starts[1:]))
	assert info(data['output_path']).duration == pytest.approx(starts[-1] + 1.0, abs=0.15)


def test_talking_head_reel(needs_speech):
	data = parse(
		talking_head_reel(video_path=needs_speech['talk_gap'], remove_silence=True, music_path=needs_speech['music'], title='Edit fast')
	)
	assert data['caption_words'] > 5
	assert len(data['timeline']) >= 2
	i = info(data['output_path'])
	assert (i.width, i.height) == (1080, 1920)
