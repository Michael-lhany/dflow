from pathlib import Path

def create_directory(path: Path):
	"""Create a directory if it does not already exist"""
	path.mkdir(parents=True, exist_ok=True)


def create_text_file(path: Path, content: str):
	"""Create a text file and any missing parent directories."""
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(content, encoding="utf-8")
