![ffmpeg-mcp](/statics/ffmpeg-mcp.png)

# ffmpeg-mcp 🎬⚡

A **Python package** for media processing using **FFmpeg** and **FastMCP**.
It enables building **microservices** that handle video/audio tasks with clean, reusable interfaces.

---

## 📖 Overview

This project provides a framework for handling media processing tasks using:

1. **FFmpeg** — A powerful multimedia framework for processing audio and video files
2. **FastMCP** — A high-performance framework for building microservices

---

## 🛠️ Available Tools

### 1. Metadata & Frames

* **`get_video_metadata`**

  * param(s):

    * `input_video_path`: str

* **`extract_frames`**

  * params:

    * `input_video_path`: str | Path
    * `number_of_frames`: int
    * `frame_timestamps`: int (eg: 5s, 10s, 15s, ...)

---

### 2. Audio

* **`extract_audio`**

  * param(s):

    * `input_video_path`: str

---

### 3. Video Scaling & Resizing

* **`scale_video`**

  * params:

    * `input_video_path`: str
    * `resolution`: Optional\[str]

---

### 4. Overlay Operations

* **`overlay_image`**

  * params:

    * `input_video_path`: str
    * `overlay_image_path`: str
    * `positioning`: Literal\[top\_left, bottom\_left, top\_right, bottom\_right, center, top\_center, bottom\_center] = 'top\_right'
    * `scale`: tuple\[int, int] | None = (100, 100)
    * `keep_audio`: bool = True
    * `opacity`: float | None = None (range 0.0–1.0)
    * `start_time`: float = 0.0 (in seconds)
    * `duration`: float | None = None (in seconds; None = until end of video)

* **`overlays_video`**

  * params:

    * `input_video_path`: str
    * `overlay_video_path`: str
    * `positioning`: Literal\[top\_left, bottom\_left, top\_right, bottom\_right] = 'top\_left'

---

### 5. Video Editing

* **`clip_video`**

  * params:

    * `input_video_path`: str
    * `start_timestamp`
    * `duration`: int

* **`crop_video`**

  * params:

    * `input_video_path`
    * `safe_crop`: bool
    * `height`: int
    * `width`: int
    * `x_offset`: int
    * `y_offset`: int

* **`trim_and_concatenate`**

  * params:

    * `input_video_path`
    * `number_of_trims`: int
    * `trim_timestamp`: List\[(start, end), (start, end), ...]

* **`make_gif`**

  * params:

    * `input_video_path`
    * `start_timestamp`
    * `duration`

---

### 6. Concatenation & Transitions

* **`concatenate_videos`**

  * param(s):

    * `file_list`: list\[Path]

* **`normalize_video_clips`**

  * params:

    * `input_video_clips`: List\[str]
    * `resolution`: tuple default `(1280, 720)`
    * `frame_rate`: int default `30`
    * `crf`: int default `23`
    * `audio_bitrate`: str default `128k`
    * `preset`: str default `fast`

* **`concat_clips_with_transition`**

  * params:

    * `input_video_clips`: List\[str]
    * `transition_types`: str default `fade` (e.g., fade, wipeleft, rectcrop, coverup, etc.)
    * `transition_duration`: float default `2`

---

## 🧰 Utilities

The `utils` folder contains helper functions and decorators to enhance the functionality and robustness of the media processing tools.

### a. Decorators

* **`validate_input_video_path`**
  A decorator that checks if the video path exists, is non-empty, and is a valid video file.
  This ensures that all video processing functions receive a valid input file.

---

## 📦 Requirements

* Python **3.12 or higher**
* [uv](https://docs.astral.sh/uv/) (package manager)
* FFmpeg installed on the system

---

## 🚀 Usage

The package can be used to build media processing microservices that leverage the power of FFmpeg through a Python interface.

### 1. Clone this repo

```bash
git clone git@github.com:yubraaj11/ffmpeg-mcp.git
```

### 2. Sync the project

```bash
uv sync --frozen
```

### 3. Use via MCP - Cline config

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ffmpeg-mcp/ffmpeg_mcp",
        "run",
        "main.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/ffmpeg-mcp"
      },
      "transportType": "stdio"
    }
  }
}
```

---

## 📚 Dependencies

* `ffmpeg-python` — Python bindings for FFmpeg
* `fastmcp` — Framework for building microservices
* `colorlog` — Colored logging output
* `fastapi` — Web framework for building APIs
* `pydantic` — Data validation and settings management

---

