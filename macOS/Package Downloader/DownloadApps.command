#!/bin/zsh

################################################################################
# Download Apps Script
# Purpose: Interactive macOS application downloader
# Description: Displays a dialog to select multiple applications, then opens
#              their download links in the default browser.
# Usage: ./DownloadApps.command
# Requirements: macOS, zsh, osascript
################################################################################

# --- Configuration ---
declare -r -A apps=(

    # --- Direct/Redirect Links ---
    ["Adobe Acrobat Reader"]="https://get.adobe.com/reader/direct/"
    ["Adobe Acrobat Pro"]="https://helpx.adobe.com/acrobat/kb/acrobat-dc-downloads.html"
    ["Brave Browser"]="https://laptop-updates.brave.com/latest/osx/release"
    ["Citrix Workspace"]="https://www.citrix.com/downloads/workspace-app/mac/workspace-app-for-mac-latest.html#ctx-dl-eula"
    ["DBeaver CE"]="https://dbeaver.io/files/dbeaver-ce-latest-macos.dmg"
    ["Discord"]="https://discordapp.com/api/download?platform=osx"
    ["Docker"]="https://desktop.docker.com/mac/stable/Docker.dmg"
    ["Dropbox"]="https://www.dropbox.com/downloading?type=full"
    ["Duet"]="https://updates.duetdisplay.com/latestMac"
    ["ESET"]="https://download.eset.com/com/eset/apps/business/eea/mac/latest/eea_osx_en.dmg"
    ["GitKraken"]="https://release.gitkraken.com/darwin/installGitKraken.dmg"
    ["GoToMeeting"]="https://link.gotomeeting.com/latest-dmg"
    ["Google Chrome"]="https://dl.google.com/chrome/mac/stable/accept_tos%3Dhttps%253A%252F%252Fwww.google.com%252Fintl%252Fen_ph%252Fchrome%252Fterms%252F%26_and_accept_tos%3Dhttps%253A%252F%252Fpolicies.google.com%252Fterms"
    ["Grammarly"]="["Grammarly"]="https://www.grammarly.com/service/download/direct?default=true""
    ["iLok License Manager"]="https://installers.ilok.com/iloklicensemanager/LicenseSupportInstallerMac.zip"
    ["Iterate Cyberduck"]="https://version.cyberduck.io/Cyberduck-latest.zip"
    ["Keka"]="https://d.keka.io/"
    ["Mendeley"]="https://www.mendeley.com/autoupdates/installer/Mac-x64/stable-incoming"
    ["Microsoft AutoUpdate"]="https://go.microsoft.com/fwlink/?linkid=830196"
    ["Microsoft Defender"]="https://go.microsoft.com/fwlink/?linkid=2097502"
    ["Microsoft Edge"]="https://go.microsoft.com/fwlink/?linkid=2093504"
    ["Microsoft Excel"]="https://go.microsoft.com/fwlink/?linkid=525135"
    ["Microsoft OneNote"]="https://go.microsoft.com/fwlink/?linkid=820886"
    ["Microsoft Outlook"]="https://go.microsoft.com/fwlink/?linkid=525137"
    ["Microsoft PowerPoint"]="https://go.microsoft.com/fwlink/?linkid=525136"
    ["Microsoft Teams"]="https://go.microsoft.com/fwlink/?linkid=869428"
    ["Microsoft Word"]="https://go.microsoft.com/fwlink/?linkid=525134"
    ["Microsoft OneDrive"]="https://go.microsoft.com/fwlink/?linkid=823060"
    ["Microsoft Azure Storage Explorer"]="https://go.microsoft.com/fwlink/?linkid=708342"
    ["Microsoft Intune Company Portal"]="https://go.microsoft.com/fwlink/?linkid=869655"
    ["Mozilla Firefox"]="https://download.mozilla.org/?product=firefox-latest-ssl&os=osx&lang=en-US"
    ["Mozilla Firefox ESR"]="https://download.mozilla.org/?product=firefox-esr-latest-ssl&os=osx&lang=en-US"
    ["Mozilla Thunderbird"]="https://download.mozilla.org/?product=thunderbird-latest-ssl&os=osx&lang=en-US"
    ["Opera"]="https://www.opera.com/download/get/?partner=www&opsys=MacOS"
    ["Postman"]="https://dl.pstmn.io/download/latest/osx"
    ["Rectangle"]="https://rectangleapp.com/download"
    ["Slack"]="https://slack.com/ssb/download-osx-universal"
    ["TeamViewer"]="https://download.teamviewer.com/download/TeamViewer.dmg"
    ["TeamViewer QS"]="https://download.teamviewer.com/download/TeamViewerQS.dmg"
    ["Telegram"]="https://telegram.org/dl/macos"
    ["The Unarchiver"]="https://dl.devmate.com/com.macpaw.site.theunarchiver/TheUnarchiver.dmg"
    ["Zotero"]="https://www.zotero.org/download/client/dl?channel=release&platform=mac"
    ["Zoom"]="https://zoom.us/client/latest/ZoomInstallerIT.pkg"

    # --- Landing Pages ---
    ["Alfred"]="https://www.alfredapp.com"
    ["Apache OpenOffice"]="https://www.openoffice.org/download/"
    ["AppCleaner"]="https://freemacsoft.net/appcleaner/"
    ["Aquamacs"]="https://aquamacs.org/download.html"
    ["Audacity"]="https://www.audacityteam.org/download/mac/"
    ["Blender"]="https://www.blender.org/download/"
    ["CCleaner"]="https://www.ccleaner.com/ccleaner/download?mac"
    ["coconutBattery"]="https://coconut-flavour.com/coconutbattery/"
    ["DB Browser"]="https://sqlitebrowser.org/dl/"
    ["DaVinci Resolve"]="https://www.blackmagicdesign.com/products/davinciresolve/"
    ["Dragonframe"]="https://dragonframe.com/downloads/"
    ["Evernote"]="https://evernote.com/download"
    ["FileZilla"]="https://filezilla-project.org/download.php?platform=osx"
    ["GIMP"]="https://www.gimp.org/downloads/"
    ["GitHub Desktop"]="https://desktop.github.com/"
    ["Google Android Studio"]="https://developer.android.com/studio"
    ["Google Earth Pro"]="https://www.google.com/earth/versions/#earth-pro"
    ["GrandPerspective"]="https://sourceforge.net/projects/grandperspectiv/files/latest/download"
    ["HandBrake"]="https://handbrake.fr/downloads.php"
    ["IntelliJ IDEA"]="https://www.jetbrains.com/idea/download/#section=mac"
    ["LastPass"]="https://lastpass.com/misc_download2.php"
    ["Microsoft Skype"]="https://www.skype.com/en/get-skype/"
    ["Microsoft Visual Studio Code"]="https://code.visualstudio.com/download"
    ["Musescore"]="https://musescore.org/en"
    ["Omnissa Horizon Client"]="https://customerconnect.omnissa.com/downloads/info/slug/virtual_desktop_and_apps/omnissa_horizon_clients/8"
    ["QGIS"]="https://www.qgis.org/en/site/forusers/download.html"
    ["R"]="https://cran.r-project.org/bin/macosx/"
    ["RStudio"]="https://posit.co/download/rstudio-desktop/"
    ["Skim"]="https://skim-app.sourceforge.io"
    ["Solstice"]="https://www.mersive.com/download/"
    ["Sublime Text"]="https://www.sublimetext.com/download"
    ["TextMate"]="https://macromates.com/download"
    ["VMware Fusion"]="https://www.vmware.com/products/fusion/fusion-evaluation.html"
    ["VirtualBox"]="https://www.virtualbox.org/wiki/Downloads"
    ["Vivaldi"]="https://vivaldi.com/download/"
    ["VLC"]="https://www.videolan.org/vlc/download-macosx.html"
    ["Wireshark"]="https://www.wireshark.org/download.html"
    ["xQuartz"]="https://www.xquartz.org/"
)

# --- Timing ---
startTime=$(date +%s)

# --- Functions ---
# Display a confirmation dialog before opening a download link
confirm_next() {
    local app_name="$1"
    local response

    response=$(osascript 2>/dev/null <<EOF
display dialog "Download $app_name?" with title "Download Manager" buttons {"Cancel", "OK"} default button "OK" cancel button "Cancel"
return button returned of result
EOF
)

    [[ "$response" == "OK" ]]
}

# Display an informational dialog
popup() {
    local message="$1"
    osascript 2>/dev/null <<EOF
    display dialog "$message" buttons {"OK"} default button "OK"
EOF
}

# --- Selection Logic ---
# Build comma-separated list of app names for AppleScript
joined=$(printf '"%s", ' "${(ko)apps[@]}" | sed 's|, $||g')

# Display selection dialog
theSelection=$(osascript 2>/dev/null <<EOF
set theList to { $joined }
set AppsToDownload to choose from list theList with prompt "Select the apps you need to download:" with multiple selections allowed
return AppsToDownload
EOF
)

# Check if user cancelled
if [[ $theSelection == "false" || -z $theSelection ]]; then
    exit 0
fi

# Parse AppleScript list output, removing quotes and extra whitespace
selectionList=$(echo "$theSelection" | tr ',' '\n' | sed 's/^[[:space:]"]*//;s/[[:space:]"]*$//')

# --- Main Loop ---
# Process each selected application
while IFS= read -r app; do
    # Skip empty lines and validate app exists in configuration
    if [[ -n "$app" && -n "${apps[$app]}" ]]; then
        # Confirm before opening download link
        if confirm_next "$app"; then
            echo "Opening: $app"
            open "${apps[$app]}"
        else
            echo "User cancelled download for: $app"
        fi
    fi
done <<< "$selectionList"

# --- Completion Message ---
popup "All downloads complete. Click OK when you're done patching."

endTime=$(date +%s)
elapsedTime=$(($endTime - $startTime))
minutes=$(($elapsedTime / 60))
seconds=$(($elapsedTime % 60))

popup "Time spent patching: $minutes minute(s) and $seconds second(s)."
