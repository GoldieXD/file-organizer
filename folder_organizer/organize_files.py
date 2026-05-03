#!/usr/bin/env python3
"""Organize files into subfolders based on file type."""

from __future__ import annotations

import argparse
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from collections.abc import Callable
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


def organize(
    folder: Path,
    recursive: bool = False,
    dry_run: bool = False,
    log: Callable[[str], None] = print,
) -> int:
    """Move files into category folders and return the number of moved files."""
    moved = 0

    for file_path in iter_files(folder, recursive):
        category = get_category(file_path)
        target_folder = folder / category
        destination = unique_destination(target_folder / file_path.name)

        # Dry run mode prints the planned move without changing any files.
        if dry_run:
            log(f"Would move: {file_path} -> {destination}")
        else:
            # Create the category folder if it does not already exist.
            target_folder.mkdir(exist_ok=True)

            # shutil.move works across folders and drives.
            shutil.move(str(file_path), str(destination))
            log(f"Moved: {file_path} -> {destination}")

        moved += 1

    return moved


def common_folders() -> list[str]:
    """Return useful folder choices for the GUI dropdown."""
    home = Path.home()
    candidates = [
        Path.cwd(),
        home / "Downloads",
        home / "Documents",
        home / "Desktop",
        home / "Pictures",
        home / "Videos",
        home / "Music",
    ]

    # Keep only folders that exist, preserving order and avoiding duplicates.
    choices: list[str] = []
    seen: set[Path] = set()
    for folder in candidates:
        resolved = folder.expanduser().resolve()
        if resolved.exists() and resolved.is_dir() and resolved not in seen:
            choices.append(str(resolved))
            seen.add(resolved)

    return choices


def launch_gui() -> None:
    """Open a small desktop GUI for choosing and organizing a folder."""
    root = tk.Tk()
    root.title("Folder Organizer")
    root.geometry("820x620")
    root.minsize(700, 520)

    folder_choices = common_folders()
    selected_folder = tk.StringVar(value=folder_choices[0] if folder_choices else str(Path.cwd()))
    dry_run_var = tk.BooleanVar(value=True)
    recursive_var = tk.BooleanVar(value=False)

    root.columnconfigure(0, weight=1)
    root.rowconfigure(4, weight=1)

    title = ttk.Label(root, text="Folder Organizer", font=("Segoe UI", 18, "bold"))
    title.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))

    instructions = (
        "1. Choose a folder from the dropdown, or click Browse to pick another folder.\n"
        "2. Leave Dry run checked first to preview where files will go without moving them.\n"
        "3. Click Organize Folder and review the results below.\n"
        "4. If the preview looks right, uncheck Dry run and click Organize Folder again.\n"
        "5. Check Include nested folders only if you want to scan folders inside the selected folder too."
    )
    instructions_label = ttk.Label(root, text=instructions, justify="left")
    instructions_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))

    folder_frame = ttk.Frame(root)
    folder_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=4)
    folder_frame.columnconfigure(1, weight=1)

    ttk.Label(folder_frame, text="Folder:").grid(row=0, column=0, sticky="w", padx=(0, 8))
    folder_combo = ttk.Combobox(
        folder_frame,
        textvariable=selected_folder,
        values=folder_choices,
        state="normal",
    )
    folder_combo.grid(row=0, column=1, sticky="ew")

    def browse_folder() -> None:
        chosen = filedialog.askdirectory(title="Choose a folder to organize")
        if not chosen:
            return

        selected_folder.set(chosen)
        current_values = list(folder_combo["values"])
        if chosen not in current_values:
            folder_combo["values"] = [chosen, *current_values]

    ttk.Button(folder_frame, text="Browse...", command=browse_folder).grid(
        row=0, column=2, sticky="e", padx=(8, 0)
    )

    options_frame = ttk.Frame(root)
    options_frame.grid(row=3, column=0, sticky="ew", padx=18, pady=8)

    ttk.Checkbutton(options_frame, text="Dry run first", variable=dry_run_var).grid(
        row=0, column=0, sticky="w", padx=(0, 18)
    )
    ttk.Checkbutton(
        options_frame,
        text="Include nested folders",
        variable=recursive_var,
    ).grid(row=0, column=1, sticky="w")

    output = scrolledtext.ScrolledText(root, wrap="word", height=18)
    output.grid(row=4, column=0, sticky="nsew", padx=18, pady=(4, 12))
    output.insert("end", "Results will appear here after you click Organize Folder.\n")
    output.configure(state="disabled")

    button_frame = ttk.Frame(root)
    button_frame.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 16))
    button_frame.columnconfigure(0, weight=1)

    def write_output(message: str) -> None:
        output.configure(state="normal")
        output.insert("end", message + "\n")
        output.see("end")
        output.configure(state="disabled")

    def clear_output() -> None:
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.configure(state="disabled")

    def run_organizer() -> None:
        folder = Path(selected_folder.get()).expanduser().resolve()

        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Invalid folder", f"Please choose a valid folder:\n{folder}")
            return

        clear_output()
        try:
            moved = organize(
                folder,
                recursive=recursive_var.get(),
                dry_run=dry_run_var.get(),
                log=write_output,
            )
        except OSError as error:
            messagebox.showerror("Organizer error", str(error))
            write_output(f"Error: {error}")
            return

        action = "Would move" if dry_run_var.get() else "Moved"
        write_output("")
        write_output(f"{action} {moved} file(s).")

        if dry_run_var.get():
            write_output("Dry run was enabled, so no files were changed.")
        else:
            write_output("Organization complete.")

    ttk.Button(button_frame, text="Organize Folder", command=run_organizer).grid(
        row=0, column=1, sticky="e"
    )

    root.mainloop()


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
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open the graphical folder organizer.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.gui:
        launch_gui()
        return

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
