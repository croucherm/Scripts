# macOS Package Downloader

A convenient zsh script for macOS that provides a GUI for downloading multiple applications at once.

## Overview

This script streamlines the process of downloading commonly-used macOS applications by presenting a user-friendly multi-select dialog. Instead of manually visiting each application's download page, you can select multiple apps and download them all in sequence.

## Key Features

- **Application Library**: 90+ pre-configured macOS applications with direct download links
- **Multi-Select GUI**: Choose multiple applications to download simultaneously
- **Download Confirmation**: Confirm each download before proceeding
- **Time Tracking**: Reports total elapsed time after all downloads complete

## Supported Applications

The script includes two categories of applications:

### Direct/Redirect Links
Applications with direct download links (DMG, PKG, ZIP files):
- Microsoft Office Suite (Word, Excel, PowerPoint, Teams, Outlook, OneNote, OneDrive, Defender, Edge, Intune, etc.)
- Browsers (Chrome, Firefox, Edge, Brave, Opera, Vivaldi)
- Communication (Discord, Slack, Telegram, TeamViewer, GoToMeeting, Zoom)
- Development (Docker, GitKraken, Postman)
- Utilities (DBeaver, VLC, The Unarchiver, iLok License Manager, ESET)
- And many more...

### Landing Pages
Applications requiring navigation to download pages:
- IDEs & Editors (VS Code, IntelliJ IDEA, Sublime Text, TextMate)
- Development Tools (Google Android Studio, Git)
- Creative Software (GIMP, Blender, DaVinci Resolve, Audacity, Handbrake)
- Productivity (Evernote, LastPass, Alfred, Musescore, RStudio)
- System Utilities (AppCleaner, CCleaner, VirtualBox, VMware Fusion)
- And more...

## How to Use

1. Open the script in Terminal or make it executable:
   ```bash
   chmod +x DownloadApps.command
   ```

2. Run the script:
   ```bash
   ./DownloadApps.command
   ```

3. A dialog box will appear with all available applications

4. Select the applications you want to download (use Cmd+Click for multiple selections)

5. Click OK, then confirm each download when prompted

6. The script will open download links in your default browser/handler

7. A final dialog shows the total time spent (in minutes)

## Requirements

- macOS with zsh (default shell in macOS Catalina and later)
- Internet connection
- Default web browser configured

## Technical Details

- **Language**: zsh
- **GUI Framework**: AppleScript (osascript)
- **Download Method**: Uses macOS `open` command to launch URLs in default handlers

## Notes

- Direct links open downloads immediately to your Downloads folder
- Landing pages open in your browser where you can manually select the appropriate version/options
- Some applications may require authentication or additional steps during installation
- Download links are current as of script creation but may change over time
