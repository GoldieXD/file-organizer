#!/usr/bin/env python3
"""Organize files into subfolders based on file type."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


# Each key is the name of the folder that files will be moved into.
# Each value is a set of file extensions that belong in that folder.
# Add or remove extensions here if you want to customize the organizer.
FILE_CATEGORIES = {
    "Images": {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".webp",
        ".heic",
        ".svg",
    },
    "Videos": {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
    },
    "Documents": {
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
        ".md",
        ".pages",
    },
    "Spreadsheets": {
        ".xls",
        ".xlsx",
        ".csv",
        ".tsv",
        ".ods",
        ".numbers",
    },
    "Presentations": {
        ".ppt",
        ".pptx",
        ".key",
        ".odp",
    },
    "Audio": {
        ".mp3",
        ".wav",
        ".aac",
        ".flac",
        ".ogg",
        ".m4a",
        ".wma",
    },
    "Archives": {
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
    },
    "Code": {
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".sh",
        ".ps1",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
    },
    "Executables": {
        ".exe",
        ".msi",
        ".bat",
        ".cmd",
        ".app",
        ".dmg",
        ".pkg",
        ".deb",
        ".rpm",
    },
    "Fonts": {
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".eot",
    },
}


def get_category(file_path: Path) -> str:
    """Return the folder category for a file extension."""
    # suffix returns the file extension, such as ".jpg" or ".pdf".
    # lower() makes the check work for files like "PHOTO.JPG" too.
    extension = file_path.suffix.lower()

    # Look through every category until the extension is found.
    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category

    # Anything not listed above gets placed in the "Other" folder.
    return "Other"


def unique_destination(destination: Path) -> Path:
    """Return a non-conflicting path by appending a number when needed."""
    # If there is no file with this name already, use the original name.
    if not destination.exists():
        return destination

    # If a file already exists, keep trying names like:
    # "report (1).pdf", "report (2).pdf", and so on.
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1

    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def iter_files(folder: Path, recursive: bool) -> list[Path]:
    """Collect files to organize, skipping already-created category folders."""
    # Used to avoid reorganizing files that are already inside output folders.
    category_names = set(FILE_CATEGORIES) | {"Other"}

    # "*" scans only the selected folder.
    # "**/*" scans the selected folder and all folders inside it.
    pattern = "**/*" if recursive else "*"
    files: list[Path] = []

    for path in folder.glob(pattern):
        # Ignore folders. This script only moves files.
        if not path.is_file():
            continue

        # Do not move this organizer script if it is stored in the folder
        # being organized.
        if path.name == Path(__file__).name and path.parent == folder:
            continue

        # When running recursively, skip files that are already inside category
        # folders such as Images, Videos, Documents, or Other.
        if any(part in category_names for part in path.relative_to(folder).parts[:-1]):
            continue

        files.append(path)

    return files


def organize(folder: Path, recursive: bool = False, dry_run: bool = False) -> int:
    """Move files into category folders and return the number of moved files."""
    moved = 0

    for file_path in iter_files(folder, recursive):
        category = get_category(file_path)
        target_folder = folder / category
        destination = unique_destination(target_folder / file_path.name)

        # Dry run mode prints the planned move without changing any files.
        if dry_run:
            print(f"Would move: {file_path} -> {destination}")
        else:
            # Create the category folder if it does not already exist.
            target_folder.mkdir(exist_ok=True)

            # shutil.move works across folders and drives.
            shutil.move(str(file_path), str(destination))
            print(f"Moved: {file_path} -> {destination}")

        moved += 1

    return moved


def parse_args() -> argparse.Namespace:
    # argparse handles command-line options and automatically creates --help.
    parser = argparse.ArgumentParser(
        description="Organize files into subfolders based on file type."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder to organize. Defaults to the current folder.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Scan nested folders too.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without moving files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Convert the user-provided folder into a full absolute path.
    # expanduser() supports paths like "~/Downloads".
    folder = Path(args.folder).expanduser().resolve()

    # Stop early with a clear message if the target is invalid.
    if not folder.exists():
        raise SystemExit(f"Folder does not exist: {folder}")
    if not folder.is_dir():
        raise SystemExit(f"Path is not a folder: {folder}")

    moved = organize(folder, recursive=args.recursive, dry_run=args.dry_run)
    action = "Would move" if args.dry_run else "Moved"
    print(f"{action} {moved} file(s).")


if __name__ == "__main__":
    main()
