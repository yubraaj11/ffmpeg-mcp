# ffmpeg-mcp

A Python package for media processing using FFmpeg and FastMCP.

## Overview

This project provides a framework for handling media processing tasks using:

1. **FFmpeg** - A powerful multimedia framework for processing audio and video files
2. **FastMCP** - A high-performance framework for building microservices

## Available Tools

- `extract_frames`
  - params:
    - `input_video_path`: str | Path
    - `number_of_frames`: int
    - `frame_timestamps`: int (eg: 5s, 10s, 15s, ...)
- `extract_audio`
  - params:
    - `input_video_path`: str
- `scale_video`
  - params:
    - `input_video_path`: str
    - `height`: Optional
    - `width`: Optional
    - `keep_aspect_ratio`: bool
- `overlay_image`
  - params:
    - `input_video_path`: str
    - `overlay_image_path`: str
    - `positioning`: Literal[top_left, bottom_left, top_right, bottom_right, center, top_center, bottom_center] = 'top_right' (default)
    - `scale`: tuple[int, int] | None = (100, 100) (default)
    - `keep_audio`: bool = True (default)
    - `opacity`: float | None = None (default) — range 0.0–1.0
    - `start_time`: float = 0.0 (default, in seconds)
    - `duration`: float | None = None (default, in seconds; None = until end of video)
- `overlays_video`
  - params:
    - `input_video_path`: str
    - `overlay_video_path`: str
    - `positioning`: Literal[top_left, bottom_left, top_right, bottom_right] = 'top_left' (default)
- `concatenate_videos`
  - params:
    - `file_list`: Path
- `clip_video`:
  - params:
    - `input_video_path`: str
    - `start_timestamp`:
    - `duration`: int
- `crop_video`:
  - params:
    - `input_video_path`
    - `safe_crop`: bool
    - `height`: int
    - `width`: int
    - `x_offset`: int
    - `y_offset`: int
- `trim_and_concatenate`:
  - params:
    - `input_video_path`
    - `number_of_trims`: int
    - `trim_timestamp`: List[(start, end), (start, end), ...]
- `make_gif`:
  - params:
    - `input_video_path`:
    - `start_timestamp`:
    - `duration`:
- `scale_video`:
  - params:
    - `input_video_path`: str
    - `resolution`: Optional[str]

## Utilities

The `utils` folder contains helper functions and decorators to enhance the functionality and robustness of the media processing tools.

### Decorators

- `validate_input_video_path`: A decorator that checks if the video path exists, is non-empty, and is a valid video file. This ensures that all video processing functions receive a valid input file.

## Requirements

- Python 3.12 or higher
- FFmpeg installed on the system

## Installation

```bash
pip install ffmpeg-mcp
```

## Usage

The package can be used to build media processing microservices that leverage the power of FFmpeg through a Python interface.

## Dependencies

- `ffmpeg-python` - Python bindings for FFmpeg
- `fastmcp` - Framework for building microservices
- `colorlog` - Colored logging output
- `fastapi` - Web framework for building APIs
- `pydantic` - Data validation and settings management
