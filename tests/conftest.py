import json
import shutil
import subprocess

import pytest

from ffmpeg_mcp.core.probe import probe_media


def _ffmpeg(*args):
	subprocess.run(['ffmpeg', '-v', 'error', '-y', *args], check=True)


@pytest.fixture(scope='session')
def media(tmp_path_factory):
	"""Synthetic test media generated with ffmpeg (and macOS `say` for speech when available)."""
	d = tmp_path_factory.mktemp('media')
	files = {
		'landscape': str(d / 'landscape.mp4'),
		'silent': str(d / 'silent.mp4'),
		'photo': str(d / 'photo.png'),
		'music': str(d / 'music_120bpm.wav'),
	}
	_ffmpeg('-f', 'lavfi', '-i', 'testsrc2=s=1920x1080:r=30:d=5', '-f', 'lavfi', '-i', 'sine=f=440:d=5', '-shortest', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', files['landscape'])  # fmt: skip
	_ffmpeg('-f', 'lavfi', '-i', 'mandelbrot=s=1280x720:r=25', '-t', '4', '-c:v', 'libx264', '-preset', 'ultrafast', files['silent'])
	_ffmpeg('-f', 'lavfi', '-i', 'smptehdbars=s=1200x1600', '-frames:v', '1', files['photo'])
	# 120 BPM kick drum: a decaying 80 Hz thump every 0.5 s plus a quiet pad.
	expr = '0.8*sin(2*PI*80*t)*exp(-30*mod(t,0.5))+0.15*sin(2*PI*330*t)'
	_ffmpeg('-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=44100:d=20", '-ac', '2', files['music'])

	if shutil.which('say'):
		speech = str(d / 'speech.aiff')
		subprocess.run(
			['say', '-o', speech, 'Hello everyone. Today I will show you how to edit videos. It is fast and simple.'], check=True
		)
		files['talk'] = str(d / 'talk.mp4')
		_ffmpeg('-f', 'lavfi', '-i', 'testsrc=s=1280x720:r=30', '-i', speech, '-shortest', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', files['talk'])  # fmt: skip
		# Same speech with a 2 s silent gap in the middle, for jump-cut tests.
		files['talk_gap'] = str(d / 'talk_gap.mp4')
		_ffmpeg(
			'-f', 'lavfi', '-i', 'testsrc=s=1280x720:r=30', '-i', speech, '-i', speech, '-filter_complex',
			'[1:a]apad=pad_dur=2[a1];[a1][2:a]concat=n=2:v=0:a=1[a]', '-map', '0:v', '-map', '[a]', '-shortest',
			'-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', files['talk_gap'],
		)  # fmt: skip
	return files


@pytest.fixture
def needs_speech(media):
	if 'talk' not in media:
		pytest.skip('speech fixture needs macOS `say`')
	return media


def parse(result: str) -> dict:
	data = json.loads(result)
	assert data.get('status') != 'ERROR', data
	return data


def info(path: str):
	return probe_media(path)
