import logging

from fastmcp import FastMCP

from ffmpeg_mcp.configs import setup_logging
from ffmpeg_mcp.services import extract_frames

setup_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP(name='ffmpeg-mcp', version='0.1.0')
mcp.tool(name_or_fn=extract_frames)


def main():
	logger.info('Server running...')
	mcp.run(transport='stdio')


if __name__ == '__main__':
	main()
