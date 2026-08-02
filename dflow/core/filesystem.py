import shutil
from pathlib import Path


def create_directory(path: Path):
    """Create a directory if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def create_text_file(path: Path, content: str):
    """Create a text file and any missing parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def validate_removal_path(path: Path, allowed_root: Path) -> Path:
    """Return a deletion target after proving it stays within allowed_root."""
    root = allowed_root.resolve()
    candidate = path.absolute()

    if candidate == root or not candidate.is_relative_to(root):
        raise ValueError(f"Refusing to remove path outside project: {path}")

    # Unlinking the final symlink is safe; resolving it would inspect its target.
    if candidate.is_symlink():
        return candidate

    resolved_candidate = candidate.resolve(strict=False)
    if not resolved_candidate.is_relative_to(root):
        raise ValueError(f"Refusing to follow path outside project: {path}")

    return candidate


def remove_path(path: Path, allowed_root: Path) -> bool:
    """Remove a file or directory tree contained by allowed_root."""
    target = validate_removal_path(path, allowed_root)
    if not target.exists() and not target.is_symlink():
        return False

    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
    else:
        target.unlink()

    return True


def clear_directory(path: Path, allowed_root: Path) -> bool:
    """Remove a directory's contents while preserving the directory itself."""
    target = validate_removal_path(path, allowed_root)
    if not target.exists() and not target.is_symlink():
        return False

    if target.is_symlink() or not target.is_dir():
        return remove_path(target, allowed_root)

    removed_anything = False
    for child in target.iterdir():
        removed_anything = remove_path(child, allowed_root) or removed_anything

    return removed_anything
