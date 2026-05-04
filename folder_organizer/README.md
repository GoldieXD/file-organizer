# SmartSort v1.0

This tool organizes files into subfolders by file type, such as Images, Videos,
Documents, Spreadsheets, Audio, Archives, Code, Fonts, and Other.

## Use the App

If you have the packaged version, double-click:

```text
dist\SmartSort.exe
```

On Windows, double-click:

```text
SmartSort.bat
```

You can also run this command from the `folder_organizer` folder:

```bash
python organize_files.py
```

In the window:

1. Choose a folder from the dropdown, or click **Browse...** to pick another one.
2. Choose **Default file-type folders** or add your own **Custom extension rules**.
3. Click **Preview Files** to see exactly which files will change.
4. Review the preview table. It shows the file, the folder it will go into,
   and the final filename. No files are moved during preview.
5. If the preview looks correct, click **Apply Changes** to move the files.

Check **Include nested folders** if you also want to scan folders inside the
selected folder.

The **Apply Changes** button stays disabled until a preview is complete. If you
change the folder, mode, nested-folder setting, or custom rules, preview again
before applying.

## Organization Modes

Use **Default file-type folders** to organize files into the built-in folders:
Images, Videos, Documents, Spreadsheets, Presentations, Audio, Archives, Code,
Executables, Fonts, and Other.

Use **Custom extension rules** when you want to choose the folder names yourself.
For example:

```text
Files ending in: .jpg, .png
go into folder: Photos
```

Click **Add rule** for each custom rule. Files that do not match a custom rule
will go into **Other**.

## Use the Command Line

Preview changes first:

```bash
python organize_files.py "C:\Users\you\Downloads" --dry-run
```

Move the files:

```bash
python organize_files.py "C:\Users\you\Downloads"
```

Scan nested folders too:

```bash
python organize_files.py "C:\Users\you\Downloads" --recursive
```

Open the GUI explicitly:

```bash
python organize_files.py --gui
```

## Build the EXE

Install PyInstaller:

```bash
python -m pip install pyinstaller
```

Build a single-file Windows app:

```bash
python -m PyInstaller --onefile --windowed --name "SmartSort" organize_files.py
```

The executable will be created at:

```text
dist\SmartSort.exe
```
