#!/usr/bin/env python3
"""Organize files into subfolders based on file type."""

from __future__ import annotations

import argparse
import shutil
import sys
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk


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
    """Open a polished desktop GUI for choosing and organizing a folder."""
    root = tk.Tk()
    root.title("Folder Organizer")
    root.geometry("900x680")
    root.minsize(760, 560)
    root.configure(bg="#f4f7fb")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", font=("Segoe UI", 10), background="#f4f7fb", foreground="#1f2937")
    style.configure("App.TFrame", background="#f4f7fb")
    style.configure("Panel.TFrame", background="#ffffff", relief="flat")
    style.configure("Header.TFrame", background="#26364d")
    style.configure(
        "Title.TLabel",
        background="#26364d",
        foreground="#ffffff",
        font=("Segoe UI", 22, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        background="#26364d",
        foreground="#dbeafe",
        font=("Segoe UI", 10),
    )
    style.configure(
        "PanelTitle.TLabel",
        background="#ffffff",
        foreground="#111827",
        font=("Segoe UI", 12, "bold"),
    )
    style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b")
    style.configure("Status.TLabel", background="#f4f7fb", foreground="#475569")
    style.configure("TCheckbutton", background="#ffffff", foreground="#1f2937")
    style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff")
    style.configure(
        "Primary.TButton",
        background="#2563eb",
        foreground="#ffffff",
        borderwidth=0,
        focusthickness=0,
        padding=(18, 10),
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Primary.TButton",
        background=[("active", "#1d4ed8"), ("pressed", "#1e40af")],
        foreground=[("disabled", "#e5e7eb")],
    )
    style.configure("Secondary.TButton", padding=(14, 8), background="#e2e8f0")
    style.map("Secondary.TButton", background=[("active", "#cbd5e1"), ("pressed", "#94a3b8")])

    folder_choices = common_folders()
    selected_folder = tk.StringVar(value=folder_choices[0] if folder_choices else str(Path.cwd()))
    dry_run_var = tk.BooleanVar(value=True)
    recursive_var = tk.BooleanVar(value=False)
    status_var = tk.StringVar(value="Ready. Choose a folder and preview the changes first.")

    root.columnconfigure(0, weight=1)
    root.rowconfigure(2, weight=1)

    header = ttk.Frame(root, style="Header.TFrame", padding=(28, 24))
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(0, weight=1)

    ttk.Label(header, text="Folder Organizer", style="Title.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    ttk.Label(
        header,
        text="Sort loose files into clean folders in one careful pass.",
        style="Subtitle.TLabel",
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    content = ttk.Frame(root, style="App.TFrame", padding=(22, 20))
    content.grid(row=1, column=0, sticky="ew")
    content.columnconfigure(0, weight=1)

    setup_panel = ttk.Frame(content, style="Panel.TFrame", padding=(20, 18))
    setup_panel.grid(row=0, column=0, sticky="ew")
    setup_panel.columnconfigure(1, weight=1)

    ttk.Label(setup_panel, text="Select folder", style="PanelTitle.TLabel").grid(
        row=0, column=0, columnspan=3, sticky="w"
    )
    ttk.Label(
        setup_panel,
        text="Pick a common folder from the dropdown or browse to another location.",
        style="Muted.TLabel",
    ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(3, 14))

    ttk.Label(setup_panel, text="Folder:", background="#ffffff").grid(
        row=2, column=0, sticky="w", padx=(0, 10)
    )
    folder_combo = ttk.Combobox(
        setup_panel,
        textvariable=selected_folder,
        values=folder_choices,
        state="normal",
    )
    folder_combo.grid(row=2, column=1, sticky="ew", ipady=4)

    def browse_folder() -> None:
        chosen = filedialog.askdirectory(title="Choose a folder to organize")
        if not chosen:
            return

        selected_folder.set(chosen)
        current_values = list(folder_combo["values"])
        if chosen not in current_values:
            folder_combo["values"] = [chosen, *current_values]

    ttk.Button(
        setup_panel,
        text="Browse...",
        command=browse_folder,
        style="Secondary.TButton",
    ).grid(row=2, column=2, sticky="e", padx=(10, 0))

    options_panel = ttk.Frame(root, style="App.TFrame", padding=(22, 0))
    options_panel.grid(row=2, column=0, sticky="nsew")
    options_panel.columnconfigure(0, weight=1)
    options_panel.rowconfigure(1, weight=1)

    choice_panel = ttk.Frame(options_panel, style="Panel.TFrame", padding=(20, 16))
    choice_panel.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    choice_panel.columnconfigure(2, weight=1)

    ttk.Label(choice_panel, text="Run options", style="PanelTitle.TLabel").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
    )
    ttk.Checkbutton(choice_panel, text="Dry run first", variable=dry_run_var).grid(
        row=1, column=0, sticky="w", padx=(0, 26)
    )
    ttk.Checkbutton(
        choice_panel,
        text="Include nested folders",
        variable=recursive_var,
    ).grid(row=1, column=1, sticky="w")

    results_panel = ttk.Frame(options_panel, style="Panel.TFrame", padding=(20, 16))
    results_panel.grid(row=1, column=0, sticky="nsew")
    results_panel.columnconfigure(0, weight=1)
    results_panel.rowconfigure(1, weight=1)

    ttk.Label(results_panel, text="Results", style="PanelTitle.TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 10)
    )

    output = scrolledtext.ScrolledText(
        results_panel,
        wrap="word",
        height=16,
        borderwidth=0,
        relief="flat",
        bg="#f8fafc",
        fg="#0f172a",
        insertbackground="#0f172a",
        font=("Consolas", 10),
        padx=12,
        pady=12,
    )
    output.tag_configure("preview", foreground="#1d4ed8")
    output.tag_configure("moved", foreground="#047857")
    output.tag_configure("error", foreground="#b91c1c")
    output.tag_configure("summary", foreground="#111827", font=("Consolas", 10, "bold"))
    output.grid(row=1, column=0, sticky="nsew")
    output.insert("end", "Results will appear here after you click Organize Folder.\n")
    output.configure(state="disabled")

    button_frame = ttk.Frame(root, style="App.TFrame", padding=(22, 16))
    button_frame.grid(row=3, column=0, sticky="ew")
    button_frame.columnconfigure(0, weight=1)

    def write_output(message: str) -> None:
        tag = ""
        if message.startswith("Would move:"):
            tag = "preview"
        elif message.startswith("Moved:") or message == "Organization complete.":
            tag = "moved"
        elif message.startswith("Error:"):
            tag = "error"
        elif message.endswith("file(s).") or message.startswith("Dry run"):
            tag = "summary"

        output.configure(state="normal")
        output.insert("end", message + "\n", tag)
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
            status_var.set("Choose a valid folder before running.")
            return

        clear_output()
        status_var.set("Scanning files...")
        root.update_idletasks()

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
            status_var.set("Stopped because an error occurred.")
            return

        action = "Would move" if dry_run_var.get() else "Moved"
        write_output("")
        write_output(f"{action} {moved} file(s).")

        if dry_run_var.get():
            write_output("Dry run was enabled, so no files were changed.")
            status_var.set(f"Preview complete: {moved} file(s) found.")
        else:
            write_output("Organization complete.")
            status_var.set(f"Done: moved {moved} file(s).")

    ttk.Label(button_frame, textvariable=status_var, style="Status.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    ttk.Button(
        button_frame,
        text="Organize Folder",
        command=run_organizer,
        style="Primary.TButton",
    ).grid(
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
    if len(sys.argv) == 1:
        launch_gui()
        return

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
