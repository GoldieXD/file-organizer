# Folder Organizer

This tool organizes files into subfolders by file type, such as Images, Videos,
Documents, Spreadsheets, Audio, Archives, Code, Fonts, and Other.

## Use the App

On Windows, double-click:

```text
Folder Organizer.bat
```

You can also run this command from the `folder_organizer` folder:

```bash
python organize_files.py
```

In the window:

1. Choose a folder from the dropdown, or click **Browse...** to pick another one.
2. Keep **Dry run first** checked and click **Organize Folder**.
3. Review the preview in the results box. No files are moved during a dry run.
4. If the preview looks correct, uncheck **Dry run first**.
5. Click **Organize Folder** again to move the files.

Check **Include nested folders** if you also want to scan folders inside the
selected folder.

The app opens in dry-run mode by default so you can safely preview changes
before moving anything.

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
