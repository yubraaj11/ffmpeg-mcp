import os
import shutil
import uuid
from contextlib import contextmanager
from datetime import datetime

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(PACKAGE_DIR, 'assets', 'fonts')


def _default_output_root() -> str:
	"""
	Where processed files go.

	FFMPEG_MCP_OUTPUT_DIR wins. When installed as a package (pip/uvx) the default is ~/ffmpeg-mcp-output, because
	site-packages is not a sensible place for user files; a source checkout keeps ffmpeg_mcp/processed_elements.
	"""
	configured = os.environ.get('FFMPEG_MCP_OUTPUT_DIR')
	if configured:
		return os.path.abspath(os.path.expanduser(configured))
	if 'site-packages' in PACKAGE_DIR or 'dist-packages' in PACKAGE_DIR:
		return os.path.join(os.path.expanduser('~'), 'ffmpeg-mcp-output')
	return os.path.join(PACKAGE_DIR, 'processed_elements')


PROCESSED_ROOT = _default_output_root()


def category_dir(category: str) -> str:
	"""Return (and create) the output folder for a tool category under processed_elements."""
	path = os.path.join(PROCESSED_ROOT, category)
	os.makedirs(path, exist_ok=True)
	return path


def output_path(category: str, output_filename: str | None, default_stem: str, ext: str = '.mp4') -> str:
	"""
	Build an absolute output path.

	A caller-provided filename is used as-is (an extension is added if missing). Otherwise a unique,
	timestamped name is generated so repeated calls never overwrite each other.
	"""
	folder = category_dir(category)
	if output_filename:
		name = os.path.basename(output_filename)
		if not os.path.splitext(name)[1]:
			name += ext
	else:
		stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		name = f'{default_stem}_{stamp}_{uuid.uuid4().hex[:6]}{ext}'
	return os.path.abspath(os.path.join(folder, name))


@contextmanager
def job_dir(prefix: str = 'job'):
	"""
	Temporary working directory for multi-stage renders.

	Removed when the block finishes without error; kept on failure so intermediate files can be inspected.
	"""
	path = os.path.join(PROCESSED_ROOT, 'jobs', f'{prefix}_{uuid.uuid4().hex[:10]}')
	os.makedirs(path, exist_ok=True)
	yield path
	shutil.rmtree(path, ignore_errors=True)
