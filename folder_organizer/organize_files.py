#!/usr/bin/env python3
"""Organize files into subfolders based on file type."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
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


INVALID_FOLDER_CHARS = re.compile(r'[<>:"/\\|?*]')


@dataclass(frozen=True)
class MovePlan:
    """A single planned file move."""

    source: Path
    category: str
    destination: Path


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


def clean_folder_name(folder_name: str) -> str:
    """Return a Windows-safe folder name."""
    cleaned = INVALID_FOLDER_CHARS.sub("-", folder_name).strip().strip(".")
    return cleaned or "Other"


def parse_extensions(raw_extensions: str) -> set[str]:
    """Convert user input like '.jpg, png txt' into normalized extensions."""
    extensions: set[str] = set()

    for item in re.split(r"[\s,;]+", raw_extensions.lower()):
        item = item.strip()
        if not item:
            continue
        if not item.startswith("."):
            item = f".{item}"
        extensions.add(item)

    return extensions


def get_custom_category(file_path: Path, rules: dict[str, set[str]]) -> str:
    """Return the custom folder name for a file based on extension rules."""
    extension = file_path.suffix.lower()

    for folder_name, extensions in rules.items():
        if extension in extensions:
            return folder_name

    return "Other"


def unique_destination(destination: Path, reserved: set[Path] | None = None) -> Path:
    """Return a non-conflicting path by appending a number when needed."""
    reserved = reserved or set()

    # If there is no file with this name already, use the original name.
    if not destination.exists() and destination not in reserved:
        return destination

    # If a file already exists, keep trying names like:
    # "report (1).pdf", "report (2).pdf", and so on.
    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1

    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists() and candidate not in reserved:
            return candidate
        counter += 1


def iter_files(
    folder: Path,
    recursive: bool,
    category_names: set[str] | None = None,
) -> list[Path]:
    """Collect files to organize, skipping already-created category folders."""
    # Used to avoid reorganizing files that are already inside output folders.
    output_folder_names = category_names or (set(FILE_CATEGORIES) | {"Other"})

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
        if any(part in output_folder_names for part in path.relative_to(folder).parts[:-1]):
            continue

        files.append(path)

    return files


def build_move_plans(
    folder: Path,
    recursive: bool = False,
    rules: dict[str, set[str]] | None = None,
) -> list[MovePlan]:
    """Build the exact file moves that preview/apply should display or run."""
    reserved_destinations: set[Path] = set()
    plans: list[MovePlan] = []

    if rules is None:
        category_names = set(FILE_CATEGORIES) | {"Other"}
    else:
        category_names = set(rules) | {"Other"}

    for file_path in iter_files(folder, recursive, category_names=category_names):
        if rules is None:
            category = get_category(file_path)
        else:
            category = get_custom_category(file_path, rules)

        target_folder = folder / category
        destination = unique_destination(target_folder / file_path.name, reserved_destinations)
        reserved_destinations.add(destination)
        plans.append(MovePlan(file_path, category, destination))

    return plans


def execute_move_plans(
    plans: list[MovePlan],
    dry_run: bool = False,
    log: Callable[[str], None] = print,
) -> int:
    """Preview or apply an already-built list of file moves."""
    moved = 0

    for plan in plans:
        if dry_run:
            log(f"Would move: {plan.source} -> {plan.destination}")
        else:
            plan.destination.parent.mkdir(exist_ok=True)
            shutil.move(str(plan.source), str(plan.destination))
            log(f"Moved: {plan.source} -> {plan.destination}")

        moved += 1

    return moved


def organize(
    folder: Path,
    recursive: bool = False,
    dry_run: bool = False,
    log: Callable[[str], None] = print,
) -> int:
    """Move files into category folders and return the number of moved files."""
    return execute_move_plans(build_move_plans(folder, recursive), dry_run, log)


def organize_with_custom_rules(
    folder: Path,
    rules: dict[str, set[str]],
    recursive: bool = False,
    dry_run: bool = False,
    log: Callable[[str], None] = print,
) -> int:
    """Move files using user-created extension-to-folder rules."""
    return execute_move_plans(
        build_move_plans(folder, recursive, rules=rules),
        dry_run,
        log,
    )


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
    root.geometry("940x780")
    root.minsize(800, 680)
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
    style.configure("TRadiobutton", background="#ffffff", foreground="#1f2937")
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
    recursive_var = tk.BooleanVar(value=False)
    mode_var = tk.StringVar(value="default")
    extension_var = tk.StringVar()
    custom_folder_var = tk.StringVar()
    status_var = tk.StringVar(value="Ready. Preview files before applying changes.")
    custom_rules: dict[str, set[str]] = {}
    preview_signature: str | None = None
    preview_plans: list[MovePlan] = []

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
        invalidate_preview()

    ttk.Button(
        setup_panel,
        text="Browse...",
        command=browse_folder,
        style="Secondary.TButton",
    ).grid(row=2, column=2, sticky="e", padx=(10, 0))

    options_panel = ttk.Frame(root, style="App.TFrame", padding=(22, 0))
    options_panel.grid(row=2, column=0, sticky="nsew")
    options_panel.columnconfigure(0, weight=1)
    options_panel.rowconfigure(2, weight=1)

    choice_panel = ttk.Frame(options_panel, style="Panel.TFrame", padding=(20, 16))
    choice_panel.grid(row=0, column=0, sticky="ew", pady=(0, 16))
    choice_panel.columnconfigure(2, weight=1)

    ttk.Label(choice_panel, text="Run options", style="PanelTitle.TLabel").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
    )
    ttk.Checkbutton(
        choice_panel,
        text="Include nested folders",
        variable=recursive_var,
    ).grid(row=1, column=0, sticky="w")

    mode_panel = ttk.Frame(options_panel, style="Panel.TFrame", padding=(20, 16))
    mode_panel.grid(row=1, column=0, sticky="ew", pady=(0, 16))
    mode_panel.columnconfigure(1, weight=1)

    ttk.Label(mode_panel, text="Organization mode", style="PanelTitle.TLabel").grid(
        row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
    )
    ttk.Radiobutton(
        mode_panel,
        text="Default file-type folders",
        value="default",
        variable=mode_var,
    ).grid(row=1, column=0, sticky="w", padx=(0, 28))
    ttk.Radiobutton(
        mode_panel,
        text="Custom extension rules",
        value="custom",
        variable=mode_var,
    ).grid(row=1, column=1, sticky="w")

    rule_frame = ttk.Frame(mode_panel, style="Panel.TFrame")
    rule_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(14, 0))
    rule_frame.columnconfigure(1, weight=1)
    rule_frame.columnconfigure(3, weight=1)

    ttk.Label(rule_frame, text="Files ending in:", background="#ffffff").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )
    extension_entry = ttk.Entry(rule_frame, textvariable=extension_var)
    extension_entry.grid(row=0, column=1, sticky="ew", ipady=3, padx=(0, 12))

    ttk.Label(rule_frame, text="go into folder:", background="#ffffff").grid(
        row=0, column=2, sticky="w", padx=(0, 8)
    )
    folder_entry = ttk.Entry(rule_frame, textvariable=custom_folder_var)
    folder_entry.grid(row=0, column=3, sticky="ew", ipady=3, padx=(0, 12))

    rules_table = ttk.Treeview(
        mode_panel,
        columns=("extensions", "folder"),
        show="headings",
        height=4,
    )
    rules_table.heading("extensions", text="File endings")
    rules_table.heading("folder", text="Folder")
    rules_table.column("extensions", width=380, anchor="w")
    rules_table.column("folder", width=220, anchor="w")
    rules_table.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(12, 0))

    def refresh_rules_table() -> None:
        for item in rules_table.get_children():
            rules_table.delete(item)

        for folder_name, extensions in custom_rules.items():
            rules_table.insert(
                "",
                "end",
                values=(", ".join(sorted(extensions)), folder_name),
            )

    def current_signature() -> str:
        """Track the setup that was previewed before applying changes."""
        normalized_rules = tuple(
            (folder_name, tuple(sorted(extensions)))
            for folder_name, extensions in sorted(custom_rules.items())
        )
        return repr(
            (
                str(Path(selected_folder.get()).expanduser().resolve()),
                recursive_var.get(),
                mode_var.get(),
                normalized_rules,
            )
        )

    def invalidate_preview(*_args: object) -> None:
        nonlocal preview_signature, preview_plans
        preview_signature = None
        preview_plans = []
        clear_preview_table()
        apply_button.configure(state="disabled")
        status_var.set("Preview needed before applying changes.")

    def add_rule() -> None:
        extensions = parse_extensions(extension_var.get())
        folder_name = clean_folder_name(custom_folder_var.get())

        if not extensions:
            messagebox.showerror(
                "Missing file endings",
                "Enter at least one file ending, such as .jpg or pdf.",
            )
            return

        if not custom_folder_var.get().strip():
            messagebox.showerror(
                "Missing folder name",
                "Enter the folder name for these files.",
            )
            return

        custom_rules.setdefault(folder_name, set()).update(extensions)
        extension_var.set("")
        custom_folder_var.set("")
        mode_var.set("custom")
        refresh_rules_table()
        invalidate_preview()
        status_var.set(f"Added custom rule for {folder_name}.")

    def remove_selected_rule() -> None:
        selected_items = rules_table.selection()
        if not selected_items:
            status_var.set("Select a custom rule to remove.")
            return

        for item in selected_items:
            folder_name = rules_table.item(item, "values")[1]
            custom_rules.pop(folder_name, None)

        refresh_rules_table()
        invalidate_preview()
        status_var.set("Removed selected custom rule.")

    ttk.Button(
        rule_frame,
        text="Add rule",
        command=add_rule,
        style="Secondary.TButton",
    ).grid(row=0, column=4, sticky="e")
    ttk.Button(
        mode_panel,
        text="Remove selected rule",
        command=remove_selected_rule,
        style="Secondary.TButton",
    ).grid(row=4, column=0, sticky="w", pady=(10, 0))

    results_panel = ttk.Frame(options_panel, style="Panel.TFrame", padding=(20, 16))
    results_panel.grid(row=2, column=0, sticky="nsew")
    results_panel.columnconfigure(0, weight=1)
    results_panel.rowconfigure(1, weight=1)
    results_panel.rowconfigure(3, weight=1)

    ttk.Label(results_panel, text="Preview", style="PanelTitle.TLabel").grid(
        row=0, column=0, sticky="w", pady=(0, 10)
    )

    preview_table = ttk.Treeview(
        results_panel,
        columns=("file", "folder", "destination"),
        show="headings",
        height=8,
    )
    preview_table.heading("file", text="File that will change")
    preview_table.heading("folder", text="Going into folder")
    preview_table.heading("destination", text="Final filename")
    preview_table.column("file", width=360, anchor="w")
    preview_table.column("folder", width=180, anchor="w")
    preview_table.column("destination", width=260, anchor="w")
    preview_table.grid(row=1, column=0, sticky="nsew")

    ttk.Label(results_panel, text="Activity log", style="PanelTitle.TLabel").grid(
        row=2, column=0, sticky="w", pady=(14, 10)
    )

    output = scrolledtext.ScrolledText(
        results_panel,
        wrap="word",
        height=8,
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
    output.grid(row=3, column=0, sticky="nsew")
    output.insert("end", "Preview results will appear here before anything is moved.\n")
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
        elif message.endswith("file(s).") or message.startswith("Preview"):
            tag = "summary"

        output.configure(state="normal")
        output.insert("end", message + "\n", tag)
        output.see("end")
        output.configure(state="disabled")

    def clear_output() -> None:
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.configure(state="disabled")

    def clear_preview_table() -> None:
        for item in preview_table.get_children():
            preview_table.delete(item)

    def show_preview_table(folder: Path, plans: list[MovePlan]) -> None:
        clear_preview_table()

        for plan in plans:
            preview_table.insert(
                "",
                "end",
                values=(
                    str(plan.source.relative_to(folder)),
                    plan.category,
                    plan.destination.name,
                ),
            )

    def run_organizer(dry_run: bool) -> None:
        nonlocal preview_signature, preview_plans
        folder = Path(selected_folder.get()).expanduser().resolve()

        if not folder.exists() or not folder.is_dir():
            messagebox.showerror("Invalid folder", f"Please choose a valid folder:\n{folder}")
            status_var.set("Choose a valid folder before running.")
            return

        if mode_var.get() == "custom" and not custom_rules:
            messagebox.showerror(
                "No custom rules",
                "Add at least one custom rule, or switch back to default file-type folders.",
            )
            status_var.set("Add a custom rule before running custom mode.")
            return

        signature = current_signature()
        if not dry_run and signature != preview_signature:
            messagebox.showerror(
                "Preview required",
                "Preview the current setup before applying changes.",
            )
            status_var.set("Preview needed before applying changes.")
            return

        clear_output()
        status_var.set("Previewing files..." if dry_run else "Applying changes...")
        root.update_idletasks()

        try:
            if dry_run:
                rules = custom_rules if mode_var.get() == "custom" else None
                plans = build_move_plans(folder, recursive=recursive_var.get(), rules=rules)
            else:
                plans = preview_plans

            moved = execute_move_plans(plans, dry_run=dry_run, log=write_output)
        except OSError as error:
            messagebox.showerror("Organizer error", str(error))
            write_output(f"Error: {error}")
            status_var.set("Stopped because an error occurred.")
            return

        action = "Would move" if dry_run else "Moved"
        write_output("")
        write_output(f"{action} {moved} file(s).")

        if dry_run:
            preview_signature = signature
            preview_plans = plans
            show_preview_table(folder, preview_plans)
            apply_button.configure(state="normal")
            write_output("Preview complete. No files were changed.")
            status_var.set(f"Preview complete: {moved} file(s) found.")
        else:
            show_preview_table(folder, preview_plans)
            write_output("Organization complete.")
            preview_signature = None
            preview_plans = []
            apply_button.configure(state="disabled")
            status_var.set(f"Done: moved {moved} file(s).")

    ttk.Label(button_frame, textvariable=status_var, style="Status.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    ttk.Button(
        button_frame,
        text="Preview Files",
        command=lambda: run_organizer(dry_run=True),
        style="Secondary.TButton",
    ).grid(row=0, column=1, sticky="e", padx=(0, 10))
    apply_button = ttk.Button(
        button_frame,
        text="Apply Changes",
        command=lambda: run_organizer(dry_run=False),
        style="Primary.TButton",
    )
    apply_button.grid(row=0, column=2, sticky="e")
    apply_button.configure(state="disabled")

    selected_folder.trace_add("write", invalidate_preview)
    recursive_var.trace_add("write", invalidate_preview)
    mode_var.trace_add("write", invalidate_preview)

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
