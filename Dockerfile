FROM python:3.12-slim

RUN apt-get update \
	&& apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
ENV PYTHONPATH=/app
CMD ["uv", "run", "--no-dev", "python", "-m", "ffmpeg_mcp.main"]
