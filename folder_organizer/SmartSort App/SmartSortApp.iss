[Setup]
AppName=SmartSort
AppVersion=1.0
AppPublisher=Aiden Goldsmith
DefaultDirName={pf}\SmartSort
DefaultGroupName=SmartSort
OutputDir=output
OutputBaseFilename=SmartSortInstaller
SetupIconFile=icon.ico

[Files]
Source: "D:\New folder\folder_organizer\dist\SmartSort.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\SmartSort"; Filename: "{app}\SmartSort.exe"; IconFilename: "{app}\SmartSort.exe"
Name: "{commondesktop}\SmartSort"; Filename: "{app}\SmartSort.exe"; IconFilename: "{app}\SmartSort.exe"