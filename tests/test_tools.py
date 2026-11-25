import json
import os

import pytest

from ffmpeg_mcp.services import (
	add_background_music,
	add_captions,
	add_text_overlay,
	apply_color_filter,
	apply_zoom,
	change_speed,
	detect_beats,
	export_for_platform,
	reframe_video,
	remove_silences,
	render_preview,
	transcribe_audio,
)
from tests.conftest import info, parse


def assert_video(path, width=None, height=None):
	assert not path.startswith('{'), path
	assert os.path.isfile(path), path
	i = info(path)
	if width:
		assert (i.width, i.height) == (width, height)
	return i


@pytest.mark.parametrize('mode', ['crop', 'blur_fill', 'pad'])
def test_reframe_video(media, mode):
	out = reframe_video(input_video_path=media['landscape'], target_format='reel', mode=mode)
	i = assert_video(out, 1080, 1920)
	assert i.has_audio
	assert abs(i.duration - 5) < 0.2


def test_reframe_invalid_path():
	data = json.loads(reframe_video(input_video_path='/nope/missing.mp4'))
	assert data['status'] == 'ERROR'


def test_add_text_overlay(media):
	out = add_text_overlay(input_video_path=media['landscape'], text='Hello Reels', start_time=1, duration=2, animation='slide_up')
	assert_video(out, 1920, 1080)


def test_add_text_overlay_rejects_late_start(media):
	data = json.loads(add_text_overlay(input_video_path=media['landscape'], text='x', start_time=50))
	assert data['status'] == 'ERROR'


def test_change_speed_constant(media):
	i = assert_video(change_speed(input_video_path=media['landscape'], speed=2.0))
	assert abs(i.duration - 2.5) < 0.2


def test_change_speed_ramp(media):
	# 1s at 0.5x becomes 2s -> total 6s
	i = assert_video(change_speed(input_video_path=media['landscape'], speed_ramp=[{'start': 1, 'end': 2, 'speed': 0.5}]))
	assert abs(i.duration - 6.0) < 0.25


def test_change_speed_on_silent_clip(media):
	i = assert_video(change_speed(input_video_path=media['silent'], speed=0.5))
	assert abs(i.duration - 8.0) < 0.3
	assert not i.has_audio


def test_apply_zoom(media):
	out = apply_zoom(input_video_path=media['landscape'], zooms=[{'start': 1, 'end': 3, 'zoom': 1.5, 'center_x': 0.3, 'ease': 'snap'}])
	assert_video(out, 1920, 1080)


@pytest.mark.parametrize('preset', ['warm', 'cinematic', 'bw', 'vintage'])
def test_apply_color_filter(media, preset):
	assert_video(apply_color_filter(input_video_path=media['landscape'], preset=preset), 1920, 1080)


def test_apply_color_filter_partial_intensity(media):
	assert_video(apply_color_filter(input_video_path=media['landscape'], preset='vivid', intensity=0.5), 1920, 1080)


def test_add_background_music(media):
	out = add_background_music(input_video_path=media['silent'], music_path=media['music'], volume=0.8)
	i = assert_video(out)
	assert i.has_audio
	assert abs(i.duration - 4.0) < 0.2


def test_detect_beats_120bpm(media):
	data = parse(detect_beats(audio_path=media['music']))
	assert 115 <= data['tempo'] <= 125
	gaps = [b - a for a, b in zip(data['beats'], data['beats'][1:])]
	assert abs(sum(gaps) / len(gaps) - 0.5) < 0.03


def test_export_for_platform(media):
	data = parse(export_for_platform(input_video_path=media['landscape'], platform='instagram_reel'))
	assert data['resolution'] == '1080x1920'
	assert data['loudness_lufs'] is None or abs(data['loudness_lufs'] + 14) <= 1.5


def test_render_preview(media):
	out = render_preview(input_video_path=media['landscape'], number_of_frames=4, columns=2)
	assert out.endswith('.png') and os.path.isfile(out)


def test_transcribe_and_captions(needs_speech):
	media = needs_speech
	data = parse(transcribe_audio(input_media_path=media['talk']))
	assert 'edit' in data['text'].lower()
	assert os.path.isfile(data['srt_path'])
	cap = parse(add_captions(input_video_path=media['talk'], transcript_path=data['transcript_path'], style='karaoke'))
	assert_video(cap['output_path'], 1280, 720)


def test_remove_silences(needs_speech):
	media = needs_speech
	data = parse(remove_silences(input_video_path=media['talk_gap']))
	assert data['new_duration'] < data['original_duration'] - 1.5
	assert_video(data['output_path'])
