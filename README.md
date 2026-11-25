<div align="center">

![ffmpeg-mcp: AI video editor MCP server powered by FFmpeg](https://raw.githubusercontent.com/yubraaj11/ffmpeg-mcp/main/statics/ffmpeg-mcp.png)

# ffmpeg-mcp 🎬⚡

**The AI video editor for Claude, Cursor and every MCP client. Edit, caption and produce videos just by asking.**

`ffmpeg-mcp` is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that turns **FFmpeg** into an AI video editing toolkit your LLM can drive. It covers **automatic captions and subtitles** (local Whisper speech-to-text), **Instagram Reels, YouTube Shorts and TikTok** formatting, **beat-synced montages**, **jump cuts**, punch-in zooms, speed ramps, transitions, colour grading, background music with ducking, and **one-call video production** from raw clips to an upload-ready MP4. It also has the classic tools: clip, crop, scale, overlay, concatenate, extract frames and audio, and make GIFs. No command-line flags to memorize.

```bash
uvx ffmpeg-mcp-studio   # that's it - add it to your MCP client (see Quick Start)
```

[![PyPI](https://img.shields.io/pypi/v/ffmpeg-mcp-studio.svg)](https://pypi.org/project/ffmpeg-mcp-studio/)
[![CI](https://github.com/yubraaj11/ffmpeg-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/yubraaj11/ffmpeg-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://github.com/yubraaj11/ffmpeg-mcp/blob/main/LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-black.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/built%20with-FastMCP-6E56CF.svg)](https://github.com/jlowin/fastmcp)
[![FFmpeg](https://img.shields.io/badge/powered%20by-FFmpeg-007808.svg)](https://ffmpeg.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-contributing)
[![Stars](https://img.shields.io/github/stars/yubraaj11/ffmpeg-mcp?style=social)](https://github.com/yubraaj11/ffmpeg-mcp)

</div>

<!-- mcp-name: io.github.yubraaj11/ffmpeg-mcp -->

---

## ✨ Why ffmpeg-mcp?

FFmpeg is incredibly powerful and incredibly hard to remember. `ffmpeg-mcp` hands that power to your AI assistant so you can say what you want in plain English:

> *"Grab the first 10 seconds of `demo.mov`, scale it to 1080p, slap my logo in the top-right corner, and turn it into a GIF."*

…and the model orchestrates the right tools for you. Each tool is a small, validated Python function — easy to read, reuse, and extend.

- 🗣️ **Natural-language video editing** — works in any MCP client (Claude Desktop, Cursor, Cline, …)
- 🎞️ **Creator editing** — Reels/Shorts reframing, word-by-word animated captions, titles, punch-in zooms, speed ramps, beat-synced cuts, jump cuts, colour looks and ducked music
- 🎬 **Full video production** — one declarative timeline (or a one-call preset) renders a finished, upload-ready video
- 🧱 **29 focused tools** — composable building blocks instead of one giant black box
- ✅ **Input validation built in** — paths are checked for existence, emptiness, and validity before FFmpeg runs
- 🧩 **Hackable** — add a new tool by writing one function and registering it

---

## 🎯 Use Cases

- **Talking-head Reels & Shorts**: vertical crop, karaoke-style animated captions, punch-in zooms and automatic jump cuts from one recording.
- **Beat-synced montages**: travel, event and product clips cut exactly on the beat of your song.
- **Podcast & interview clips**: transcribe, cut highlights, burn in subtitles and export for every platform.
- **Product promos & ads**: titles, logo watermark, colour look, music and transitions in one timeline.
- **Batch content repurposing**: turn landscape YouTube footage into 9:16 TikTok/Reels/Shorts with blurred-background fill.
- **Everyday FFmpeg chores**: trim, crop, scale, GIFs, frame grabs and audio extraction, by just asking.

---

## 🛠️ Available Tools

| Tool | What it does | Key parameters |
| --- | --- | --- |
| `get_video_metadata` | Probe a file for streams, codecs, duration, etc. | `input_video_path` |
| `extract_frames` | Save frames as images (evenly, by interval, or 1/sec) | `input_video_path`, `number_of_frames?`, `timestamp_offset?` |
| `extract_audio` | Pull audio out to a `.wav` file | `input_video_path` |
| `scale_video` | Upscale to `1080p` / `2k` / `4k`, aspect-preserving | `input_video_path`, `resolution="1080p"` |
| `crop_video` | Crop to a region | `input_video_path`, `width`, `height`, `x_offset`, `y_offset`, `safe_crop` |
| `clip_video` | Cut a sub-clip by start + duration | `input_video_path`, `start_timestamp`, `duration` |
| `make_gif` | Turn a segment into an optimized GIF | `input_video_path`, `start_timestamp`, `duration` |
| `overlay_image` | Composite an image (logo/watermark) with timing & opacity | `input_video_path`, `overlay_image_path`, `positioning`, `opacity`, `start_time`, `duration` |
| `overlays_video` | Overlay a (looping) video onto another | `input_video_path`, `overlay_video_path`, `positioning`, `scale` |
| `trim_and_concat_operation` | Trim multiple clips and stitch them together | `inputs: [{path, start_time?, end_time?}]`, `width`, `height` |
| `get_normalized_clips` | Normalize clips to a common res/fps/codec (in parallel) | `input_video_clips`, `resolution`, `frame_rate`, `crf` |
| `concat_clips_with_transition` | Concatenate clips with an `xfade` transition | `input_video_clips`, `transition_type="fade"`, `transition_duration` |

> `?` marks optional parameters. `concat_clips_with_transition` supports many transitions — `fade`, `wipeleft`, `slideup`, `circlecrop`, `dissolve`, `pixelize`, `radial`, and [dozens more](https://trac.ffmpeg.org/wiki/Xfade).


### 🎞️ Creator editing tools

| Tool | What it does | Key parameters |
| --- | --- | --- |
| `reframe_video` | Convert to 9:16 / 1:1 / 4:5 / 16:9 | `target_format`, `mode` (`crop` / `blur_fill` / `pad`), `focus_x?`, `focus_y?` |
| `add_text_overlay` | Styled, auto-wrapped title or label with an animation | `text`, `start_time`, `duration?`, `style`, `position`, `animation` |
| `transcribe_audio` | Local speech-to-text with word timestamps (faster-whisper) → `.json` + `.srt` | `input_media_path`, `model_size="base"`, `language?` |
| `add_captions` | Burned-in word-synced captions (karaoke highlight, one word at a time, phrases) | `style`, `mode`, `words_per_line`, `transcript_path?` |
| `change_speed` | Constant speed, slow-mo segments or gradual speed ramps (pitch preserved) | `speed?` or `speed_ramp: [{start, end, speed \| speed_start+speed_end}]` |
| `apply_zoom` | Punch-in zooms and ken-burns push | `zooms: [{start, end, zoom, center_x, center_y, ease}]`, `ken_burns?` |
| `apply_color_filter` | Looks: `warm`, `cool`, `vintage`, `bw`, `vivid`, `cinematic`, `matte`, `moody`, or a `.cube` LUT | `preset?`, `lut_path?`, `intensity` |
| `add_background_music` | Music bed that loops/trims, fades and auto-ducks under speech | `music_path`, `volume`, `duck_voice`, `start_offset`, `replace_audio` |
| `detect_beats` | Tempo, beat and downbeat times of a song | `audio_path`, `start_offset?` |
| `remove_silences` | Jump-cut out pauses and dead air | `noise_db`, `min_silence`, `padding` |
| `export_for_platform` | Upload-ready file: right size, H.264/AAC, fast-start, −14 LUFS | `platform` (`instagram_reel`, `tiktok`, `youtube_shorts`, …) |
| `render_preview` | Contact sheet of timestamped thumbnails to check an edit | `number_of_frames`, `timestamps?` |

### 🎬 Full video production

| Tool | What it does |
| --- | --- |
| `get_editing_capabilities` | Lists every format, platform, style, colour preset, transition and position the tools accept |
| `render_composition` | Renders a whole edit from a JSON timeline: per-clip trim → speed → reframe → zoom → colour, joined with transitions, then captions, titles, logos, music and platform export. `dry_run=true` returns the resolved timeline without rendering |
| `make_reel_from_clips` | One call: videos/photos → captioned, titled, transitioned 9:16 Reel with music |
| `beat_sync_montage` | One call: cuts between clips exactly on the song's beats, with pulse zooms on downbeats |
| `talking_head_reel` | One call: talking-to-camera recording → vertical crop, karaoke captions, punch-ins, optional jump cuts, ducked music |

Example `render_composition` spec:

```json
{
  "format": "reel",
  "clips": [
    {"path": "/videos/hook.mp4", "end": 4, "zoom": [{"start": 1.5, "end": 4, "zoom": 1.2, "ease": "snap"}]},
    {"path": "/videos/broll.mp4", "start": 2, "end": 6, "speed_ramp": [{"start": 1, "end": 3, "speed": 0.4}], "color": "cinematic"},
    {"path": "/photos/product.jpg", "image_duration": 2.5, "transition_in": {"type": "slideup", "duration": 0.3}}
  ],
  "default_transition": {"type": "fade", "duration": 0.4},
  "text_overlays": [{"text": "3 editing tricks", "start": 0, "duration": 2.5, "style": "title", "animation": "slide_up"}],
  "image_overlays": [{"path": "/brand/logo.png", "position": "top_right", "width": 160, "opacity": 0.9}],
  "captions": {"style": "karaoke", "mode": "phrase_highlight"},
  "music": {"path": "/music/track.mp3", "volume": 0.25, "duck": true},
  "export": {"platform": "instagram_reel"}
}
```

Times: clip `start`/`end` and `speed_ramp` are in source seconds; `zoom` is in seconds within the clip's output; text/image overlays are on the final timeline. Auto-generated transcripts are saved to the `transcripts/` folder in the output directory. Fix any misheard words in the JSON and pass it back as `captions.transcript_path`.

> Text and captions are rendered with Pillow using the bundled [Montserrat](https://github.com/yubraaj11/ffmpeg-mcp/blob/main/ffmpeg_mcp/assets/fonts/OFL.txt) font, so they work even on FFmpeg builds without `libass`/`freetype`. The first caption run downloads the faster-whisper model (~145 MB for `base`).

---

## 📦 Requirements

- **Python 3.12+**
- **[FFmpeg](https://ffmpeg.org/download.html)** installed and on your `PATH` (provides `ffmpeg` + `ffprobe`)
- **[uv](https://docs.astral.sh/uv/)** package manager

Verify FFmpeg is available:

```bash
ffmpeg -version
```

---

## 🚀 Quick Start

### Option A: run with `uvx` (recommended)

No clone needed. [`uvx`](https://docs.astral.sh/uv/guides/tools/) downloads and runs the server in an isolated environment:

```bash
uvx ffmpeg-mcp-studio
```

Add it to your MCP client:

<details open>
<summary><b>Claude Desktop / Cursor / Windsurf</b> (<code>claude_desktop_config.json</code>, <code>.cursor/mcp.json</code>, ...)</summary>

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "uvx",
      "args": ["ffmpeg-mcp-studio"],
      "env": { "FFMPEG_MCP_OUTPUT_DIR": "/Users/you/Movies/ffmpeg-mcp" }
    }
  }
}
```

</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add ffmpeg-mcp -- uvx ffmpeg-mcp-studio
```

</details>

<details>
<summary><b>Cline</b> (VS Code)</summary>

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "uvx",
      "args": ["ffmpeg-mcp-studio"],
      "timeout": 600,
      "transportType": "stdio"
    }
  }
}
```

</details>

To run the latest unreleased code straight from GitHub: `uvx --from git+https://github.com/yubraaj11/ffmpeg-mcp ffmpeg-mcp-studio`. You can also `pip install ffmpeg-mcp-studio` and run `ffmpeg-mcp-studio`.

### Option B: run from source (for development)

```bash
git clone https://github.com/yubraaj11/ffmpeg-mcp.git
cd ffmpeg-mcp
uv sync --frozen
```

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/ffmpeg-mcp", "run", "ffmpeg-mcp-studio"]
    }
  }
}
```

### Where outputs go

| Setting | Output folder |
| --- | --- |
| `FFMPEG_MCP_OUTPUT_DIR` env var set | that folder |
| Installed via `uvx` / `pip` | `~/ffmpeg-mcp-output/` |
| Running from a source checkout | `ffmpeg_mcp/processed_elements/` |

> Long renders (captions, full compositions) can take a minute or more. If your client has a tool timeout, raise it (e.g. `"timeout": 600` in Cline).

### Restart your client and start editing

> *"Extract 5 evenly-spaced frames from `intro.mp4`."*
>
> *"Make a 3-second GIF from `clip.mov` starting at 12s."*
>
> *"Concatenate `a.mp4`, `b.mp4`, and `c.mp4` with a 1-second `wipeleft` transition between them."*
>
> *"Turn `talk.mov` into a Reel with karaoke captions, cut out the pauses, and put `lofi.mp3` quietly underneath."*
>
> *"Make a 15-second beat-synced montage of everything in `~/trip/` to `song.mp3`, starting at the drop at 0:42."*

---

## 🧰 Project Layout

```
ffmpeg_mcp/
├── main.py              # MCP server entry point — registers all tools
├── services/            # one module per tool
├── core/                # paths, probing, ffmpeg runner, text rendering, styles, transcription, beats
├── effects/             # reusable filter builders: reframe, speed, zoom, color, audio, text
├── composition/         # timeline models, multi-stage renderer, preset recipes
├── utils/               # validation decorators & helpers
├── assets/fonts/        # bundled OFL font for titles and captions
├── configs/             # colored logging setup
└── exceptions/          # structured error messages
tests/                   # pytest suite on synthetic media
server.json              # MCP Registry manifest
```

Single-effect tools and the composition renderer share the same filter builders in `effects/`, so each effect has a single implementation.

Every tool returns either the output file path or a structured JSON error (`status`, `error_type`, `message`, `time`), so failures are easy for the model to read and recover from.

---

## ❓ FAQ

**How do I add automatic captions or subtitles to a video with Claude?**
Install the server, then ask: *"Add karaoke captions to `/path/talk.mp4`"*. It transcribes locally with Whisper (`add_captions`) and burns in word-synced captions. Use `transcribe_audio` if you only want an `.srt` file.

**Can it make Instagram Reels, YouTube Shorts or TikToks?**
Yes. `make_reel_from_clips`, `talking_head_reel` and `beat_sync_montage` output 1080×1920 videos, and `export_for_platform` produces upload-ready files (H.264/AAC, fast-start, −14 LUFS) for `instagram_reel`, `tiktok`, `youtube_shorts` and more.

**Does it upload my videos anywhere?**
No. Everything, including speech-to-text, runs locally with FFmpeg. Only the Whisper model is downloaded once from Hugging Face.

**Which MCP clients does it work with?**
Any client that supports stdio MCP servers: Claude Desktop, Claude Code, Cursor, Windsurf, Cline, Continue, Zed and others.

**Do I need FFmpeg installed?**
Yes. Install `ffmpeg` (which includes `ffprobe`) and make sure it is on your `PATH` (`brew install ffmpeg`, `apt install ffmpeg`, or `winget install ffmpeg`).

**Is it an alternative to CapCut or Instagram Edits?**
It covers many of the same creator features (captions, beat sync, speed ramps, zooms, transitions, music), driven by your AI assistant and scriptable through a JSON timeline instead of a GUI.

---

## 🤝 Contributing

Contributions are very welcome! Adding a tool is roughly:

1. Write a function in `ffmpeg_mcp/services/your_tool.py`.
2. Export it from `ffmpeg_mcp/services/__init__.py`.
3. Register it in `main.py` with `mcp.tool(name_or_fn=your_tool)`.

Please run the linter and tests before opening a PR:

```bash
uv run ruff check .
uv run pytest
```

### Releasing (maintainers)

1. Bump `version` in `pyproject.toml` and both `version` fields in `server.json`.
2. Merge to `main`, then tag: `git tag v0.2.0 && git push origin v0.2.0`.
3. The **Release** workflow checks the versions match, builds, publishes to PyPI (using the `PYPI_API_TOKEN` secret) and then to the MCP Registry.

Found a bug or have an idea? [Open an issue](https://github.com/yubraaj11/ffmpeg-mcp/issues) — and if this project saves you from another `ffmpeg` man-page dive, consider leaving a ⭐.

---

## 📄 License

[MIT](https://github.com/yubraaj11/ffmpeg-mcp/blob/main/LICENSE). The bundled Montserrat font is licensed under the [SIL Open Font License](https://github.com/yubraaj11/ffmpeg-mcp/blob/main/ffmpeg_mcp/assets/fonts/OFL.txt).

---

## 📚 Built With

- [`fastmcp`](https://github.com/jlowin/fastmcp) — the MCP server framework
- [`ffmpeg-python`](https://github.com/kkroening/ffmpeg-python) — Python bindings for FFmpeg
- [`pydantic`](https://docs.pydantic.dev/) — data validation
- [`colorlog`](https://github.com/borntyping/python-colorlog) — colored logs
- [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) — local speech-to-text for captions
- [`librosa`](https://librosa.org/) — beat tracking
- [`Pillow`](https://python-pillow.org/) — title and caption rendering
</content>
