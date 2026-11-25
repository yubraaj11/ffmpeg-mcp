import ffmpeg


def silent_audio(duration: float):
	"""A silent stereo 48 kHz track of the given length (for clips without audio)."""
	return ffmpeg.input('anullsrc=r=48000:cl=stereo', f='lavfi', t=f'{duration:.4f}').audio


def normalize_audio(a):
	return a.filter('aresample', 48000).filter('aformat', sample_fmts='fltp', channel_layouts='stereo')


def music_bed(
	music_path: str,
	duration: float,
	volume: float = 0.25,
	fade_in: float = 0.5,
	fade_out: float = 1.5,
	start_offset: float = 0.0,
	loop: bool = True,
):
	"""Load a music file, loop/trim it to `duration`, set volume and apply fades."""
	opts = {'ss': start_offset} if start_offset > 0 else {}
	if loop:
		opts['stream_loop'] = -1
	m = ffmpeg.input(music_path, **opts).audio
	m = normalize_audio(m).filter('atrim', duration=f'{duration:.4f}').filter('asetpts', 'PTS-STARTPTS')
	m = m.filter('volume', f'{volume:.4f}')
	if fade_in > 0:
		m = m.filter('afade', t='in', st=0, d=fade_in)
	if fade_out > 0:
		m = m.filter('afade', t='out', st=max(0.0, duration - fade_out), d=min(fade_out, duration))
	return m


def mix_music(voice, music, duck: bool = True, duck_amount: float = 8.0):
	"""
	Mix a music bed under a voice track. With duck=True the music is side-chain compressed by the voice so it
	automatically dips while someone is talking.
	"""
	if voice is None:
		return music
	voice = normalize_audio(voice)
	if duck:
		split = voice.asplit()
		voice, sidechain = split[0], split[1]
		music = ffmpeg.filter([music, sidechain], 'sidechaincompress', threshold=0.02, ratio=duck_amount, attack=20, release=400)
	mixed = ffmpeg.filter([voice, music], 'amix', inputs=2, duration='first', normalize=0, dropout_transition=0)
	return mixed.filter('alimiter', limit=0.95)


def loudness_normalize(a, target_lufs: float = -14.0):
	return a.filter('loudnorm', I=target_lufs, TP=-1.5, LRA=11).filter('aresample', 48000)
