import sys

import typer

from dflow.core.filesystem import (
    clear_directory,
    remove_path,
    validate_removal_path,
)
from dflow.core.project import (
    CLEAN_CATEGORIES,
    find_project_root,
    iter_generated_paths,
)


def _selected_categories(
    only: list[str] | None,
    exclude: list[str] | None,
) -> set[str]:
    requested = set(only or CLEAN_CATEGORIES)
    excluded = set(exclude or [])
    unknown = (requested | excluded) - set(CLEAN_CATEGORIES)
    if unknown:
        choices = ", ".join(CLEAN_CATEGORIES)
        invalid = ", ".join(sorted(unknown))
        raise typer.BadParameter(
            f"unknown cleanup target(s): {invalid}. Choose from: {choices}."
        )
    return requested - excluded


def clean(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show generated paths without removing them.",
    ),
    only: list[str] | None = typer.Option(
        None,
        "--only",
        "-o",
        help=(
            "Clean only this category; repeat as needed. Choices: "
            + ", ".join(CLEAN_CATEGORIES)
            + "."
        ),
    ),
    exclude: list[str] | None = typer.Option(
        None,
        "--exclude",
        "-x",
        help=(
            "Preserve this category; repeat as needed. Choices: "
            + ", ".join(CLEAN_CATEGORIES)
            + "."
        ),
    ),
):
    """Remove generated build, simulation, and report artifacts."""
    project_root = find_project_root()
    selected_categories = _selected_categories(only, exclude)
    if not selected_categories:
        print("No cleanup categories selected.")
        return

    changed_anything = False
    failed = False

    for target in iter_generated_paths(project_root):
        if target.category not in selected_categories:
            continue
        try:
            relative_path = target.path.relative_to(project_root)
        except ValueError:
            relative_path = target.path

        operation = clear_directory if target.preserve_directory else remove_path
        action = "Cleared" if target.preserve_directory else "Removed"
        dry_run_action = "clear" if target.preserve_directory else "remove"

        try:
            validated_path = validate_removal_path(target.path, project_root)
            if dry_run:
                exists = validated_path.exists() or validated_path.is_symlink()
                has_contents = (
                    exists
                    and validated_path.is_dir()
                    and not validated_path.is_symlink()
                    and any(validated_path.iterdir())
                )
                if exists and (not target.preserve_directory or has_contents):
                    print(f"Would {dry_run_action} {relative_path}")
                    changed_anything = True
                continue

            changed = operation(target.path, project_root)
        except (OSError, ValueError) as error:
            print(f"Failed to clean {relative_path}: {error}", file=sys.stderr)
            failed = True
            continue

        if changed:
            print(f"{action} {relative_path}")
            changed_anything = True

    if not changed_anything and not failed:
        print("Nothing to clean.")

    if failed:
        raise typer.Exit(code=1)
