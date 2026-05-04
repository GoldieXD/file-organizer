@echo off
cd /d "%~dp0"
python organize_files.py
if errorlevel 1 pause
