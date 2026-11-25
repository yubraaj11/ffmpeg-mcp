import os
import shutil
import uuid
from contextlib import contextmanager
from datetime import datetime

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_ROOT = os.path.join(PACKAGE_DIR, 'processed_elements')
REPO_ROOT = os.path.dirname(PACKAGE_DIR)
FONTS_DIR = os.path.join(REPO_ROOT, 'statics', 'fonts')


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
