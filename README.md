<div align="center">

![ffmpeg-mcp](statics/ffmpeg-mcp.png)

# ffmpeg-mcp 🎬⚡

**Edit video and audio by just talking to your AI assistant.**

`ffmpeg-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server that puts the full power of **FFmpeg** behind a clean set of tools your LLM can call — clip, crop, scale, overlay, concatenate with transitions, extract frames/audio, make GIFs, and more. No command-line flags to memorize.

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/built%20with-FastMCP-6E56CF.svg)](https://github.com/jlowin/fastmcp)
[![FFmpeg](https://img.shields.io/badge/powered%20by-FFmpeg-007808.svg)](https://ffmpeg.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-contributing)
[![Stars](https://img.shields.io/github/stars/yubraaj11/ffmpeg-mcp?style=social)](https://github.com/yubraaj11/ffmpeg-mcp)

</div>

---

## ✨ Why ffmpeg-mcp?

FFmpeg is incredibly powerful and incredibly hard to remember. `ffmpeg-mcp` hands that power to your AI assistant so you can say what you want in plain English:

> *"Grab the first 10 seconds of `demo.mov`, scale it to 1080p, slap my logo in the top-right corner, and turn it into a GIF."*

…and the model orchestrates the right tools for you. Each tool is a small, validated Python function — easy to read, reuse, and extend.

- 🗣️ **Natural-language video editing** — works in any MCP client (Claude Desktop, Cursor, Cline, …)
- 🧱 **12 focused tools** — composable building blocks instead of one giant black box
- ✅ **Input validation built in** — paths are checked for existence, emptiness, and validity before FFmpeg runs
- 🧩 **Hackable** — add a new tool by writing one function and registering it

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

### 1. Clone & install

```bash
git clone https://github.com/yubraaj11/ffmpeg-mcp.git
cd ffmpeg-mcp
uv sync --frozen
```

### 2. Connect it to your MCP client

Point your client at the server using the snippets below. Replace `/path/to/ffmpeg-mcp` with the **absolute path** to your clone.

<details open>
<summary><b>Claude Desktop / Cursor</b> (<code>claude_desktop_config.json</code> or <code>.cursor/mcp.json</code>)</summary>

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/ffmpeg-mcp/ffmpeg_mcp", "run", "main.py"],
      "env": { "PYTHONPATH": "/path/to/ffmpeg-mcp" }
    }
  }
}
```

</details>

<details>
<summary><b>Cline</b> (VS Code)</summary>

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "command": "uv",
      "args": ["--directory", "/path/to/ffmpeg-mcp/ffmpeg_mcp", "run", "main.py"],
      "env": { "PYTHONPATH": "/path/to/ffmpeg-mcp" },
      "transportType": "stdio"
    }
  }
}
```

</details>

### 3. Restart your client and start editing

> *"Extract 5 evenly-spaced frames from `intro.mp4`."*
>
> *"Make a 3-second GIF from `clip.mov` starting at 12s."*
>
> *"Concatenate `a.mp4`, `b.mp4`, and `c.mp4` with a 1-second `wipeleft` transition between them."*

Processed files are written under `ffmpeg_mcp/processed_elements/`.

---

## 🧰 Project Layout

```
ffmpeg_mcp/
├── main.py              # MCP server entry point — registers all tools
├── services/            # one module per tool
├── configs/             # colored logging setup
└── exceptions/          # structured error messages
utils/                   # validation decorators & helpers
```

Every tool returns either the output file path or a structured JSON error (`status`, `error_type`, `message`, `time`), so failures are easy for the model to read and recover from.

---

## 🤝 Contributing

Contributions are very welcome! Adding a tool is roughly:

1. Write a function in `ffmpeg_mcp/services/your_tool.py`.
2. Export it from `ffmpeg_mcp/services/__init__.py`.
3. Register it in `main.py` with `mcp.tool(name_or_fn=your_tool)`.

Please run the linter before opening a PR:

```bash
uv run ruff check .
```

Found a bug or have an idea? [Open an issue](https://github.com/yubraaj11/ffmpeg-mcp/issues) — and if this project saves you from another `ffmpeg` man-page dive, consider leaving a ⭐.

---

## 📚 Built With

- [`fastmcp`](https://github.com/jlowin/fastmcp) — the MCP server framework
- [`ffmpeg-python`](https://github.com/kkroening/ffmpeg-python) — Python bindings for FFmpeg
- [`pydantic`](https://docs.pydantic.dev/) — data validation
- [`colorlog`](https://github.com/borntyping/python-colorlog) — colored logs
</content>
