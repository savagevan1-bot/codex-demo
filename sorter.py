"""Utilities for selecting image files matching a CSV list.

This module exposes a small command-line program that moves image files
from a target directory tree into a ``Sorting`` subdirectory when the file
names appear in a CSV file.  See ``python sorter.py --help`` for details.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path
from typing import Iterable, Set, Tuple


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def load_target_names(csv_path: Path) -> Tuple[Set[str], Set[str]]:
    """Return the normalized file names listed in ``csv_path``.

    The CSV file may contain names with or without extensions.  Both the full
    filename and the stem (portion before the first extension) are stored in a
    case-insensitive manner.  Empty cells are ignored.
    """

    normalized_names: Set[str] = set()
    normalized_stems: Set[str] = set()

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            for cell in row:
                name = cell.strip()
                if not name:
                    continue
                normalized = name.lower()
                normalized_names.add(normalized)
                stem = Path(name).stem.lower()
                normalized_stems.add(stem)

    return normalized_names, normalized_stems


def iter_image_files(root: Path) -> Iterable[Path]:
    """Yield all image files in ``root`` and its subdirectories."""

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def ensure_unique_destination(dest_dir: Path, filename: str) -> Path:
    """Return a destination path that will not overwrite an existing file."""

    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_matching_images(target_dir: Path, csv_path: Path) -> int:
    """Move matching image files into ``Sorting`` directory.

    Returns the number of files moved.
    """

    if not target_dir.exists():
        raise FileNotFoundError(f"Target directory does not exist: {target_dir}")
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file does not exist: {csv_path}")

    names, stems = load_target_names(csv_path)
    sorting_dir = target_dir / "Sorting"
    sorting_dir.mkdir(exist_ok=True)

    moved = 0
    for file_path in iter_image_files(target_dir):
        # Avoid re-processing files already in the Sorting directory.
        if sorting_dir in file_path.parents:
            continue

        filename = file_path.name.lower()
        filestem = file_path.stem.lower()
        if filename in names or filestem in stems:
            destination = ensure_unique_destination(sorting_dir, file_path.name)
            shutil.move(str(file_path), str(destination))
            moved += 1

    return moved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Move selected images into a Sorting folder.")
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Directory containing the images (the Sorting folder will be created here).",
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="CSV file with the image file names (with or without extensions).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    moved = move_matching_images(args.target_dir, args.csv_path)
    print(f"Moved {moved} file(s) into {args.target_dir / 'Sorting'}")


if __name__ == "__main__":
    main()
