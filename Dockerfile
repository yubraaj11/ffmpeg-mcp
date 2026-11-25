FROM python:3.12-slim

RUN apt-get update \
	&& apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock .python-version README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project

COPY ffmpeg_mcp ./ffmpeg_mcp
RUN uv sync --frozen --no-dev

ENV FFMPEG_MCP_OUTPUT_DIR=/data
VOLUME ["/data"]
CMD ["uv", "run", "--frozen", "--no-dev", "ffmpeg-mcp-studio"]
