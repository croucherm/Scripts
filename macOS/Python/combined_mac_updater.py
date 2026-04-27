#!/usr/bin/env python3
"""
Combined Mac Package Updater
Merges functionality from:
1. download_from_rtf_doubleclick_v2.py - RTF parsing and guided downloads
2. extract_mac_updates_Version7.py - Email extraction and RTF generation
3. DownloadApps.command - Interactive app selection

This unified script provides a complete workflow for managing macOS package updates.
"""

import json
import logging
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

FOLDER_PATH = Path(os.path.expanduser('~/Desktop/email'))
DEFAULT_RTF_PATH = FOLDER_PATH / 'Mac Package Updates.rtf'
RAW_EMAIL_PATH = FOLDER_PATH / 'raw_email.txt'
EXCLUSION_FILE_PATH = FOLDER_PATH / 'excluded_titles.txt'
LOG_FILE_PATH = FOLDER_PATH / 'script_log.txt'
USER_NAME = "Mike"

FOLDER_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE_PATH),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MOZILLA_FIREFOX_VERSIONS_URL = 'https://product-details.mozilla.org/1.0/firefox_versions.json'
MOZILLA_THUNDERBIRD_VERSIONS_URL = 'https://product-details.mozilla.org/1.0/thunderbird_versions.json'

# ============================================================================
# DOWNLOAD URL MAPPINGS
# ============================================================================

DOWNLOAD_URLS: Dict[str, str] = {
    # Browser / direct links
    'adobe acrobat pro': 'https://helpx.adobe.com/acrobat/kb/acrobat-dc-downloads.html',
    'adobe acrobat reader': 'https://get.adobe.com/reader/direct/',
    'brave browser': 'https://laptop-updates.brave.com/latest/osx',
    'citrix workspace': 'https://www.citrix.com/downloads/workspace-app/mac/workspace-app-for-mac-latest.html#ctx-dl-eula',
    'cyberduck': 'https://version.cyberduck.io/Cyberduck-latest.zip',
    'dbeaver ce': 'https://dbeaver.io/files/dbeaver-ce-latest-macos.dmg',
    'discord': 'https://discordapp.com/api/download?platform=osx',
    'docker': 'https://desktop.docker.com/mac/stable/Docker.dmg',
    'dropbox': 'https://www.dropbox.com/downloading?type=full',
    'duet': 'https://updates.duetdisplay.com/latestMac',
    'eset': 'https://download.eset.com/com/eset/apps/business/eea/mac/latest/eea_osx_en.dmg',
    'gitkraken': 'https://release.gitkraken.com/darwin/installGitKraken.dmg',
    'goto meeting': 'https://link.gotomeeting.com/latest-dmg',
    'gotomeeting': 'https://link.gotomeeting.com/latest-dmg',
    'google chrome': 'https://chromeenterprise.google/download/',
    'grammarly': 'https://download-editor.grammarly.com/osx/Grammarly.dmg',
    'ilok license manager': 'https://installers.ilok.com/iloklicensemanager/LicenseSupportInstallerMac.zip',
    'keka': 'https://d.keka.io/',
    'mendeley': 'https://www.mendeley.com/autoupdates/installer/Mac-x64/stable-incoming',
    'microsoft autoupdate': 'https://go.microsoft.com/fwlink/?linkid=830196',
    'microsoft azure storage explorer': 'https://go.microsoft.com/fwlink/?linkid=708342',
    'microsoft defender': 'https://go.microsoft.com/fwlink/?linkid=2097502',
    'microsoft edge': 'https://go.microsoft.com/fwlink/?linkid=2093504',
    'microsoft excel': 'https://go.microsoft.com/fwlink/?linkid=525135',
    'microsoft intune company portal': 'https://go.microsoft.com/fwlink/?linkid=869655',
    'microsoft onedrive': 'https://go.microsoft.com/fwlink/?linkid=823060',
    'microsoft onenote': 'https://go.microsoft.com/fwlink/?linkid=820886',
    'microsoft outlook': 'https://go.microsoft.com/fwlink/?linkid=525137',
    'microsoft powerpoint': 'https://go.microsoft.com/fwlink/?linkid=525136',
    'microsoft teams': 'https://go.microsoft.com/fwlink/?linkid=869428',
    'microsoft word': 'https://go.microsoft.com/fwlink/?linkid=525134',
    'postman': 'https://dl.pstmn.io/download/latest/osx',
    'rectangle': 'https://rectangleapp.com/download',
    'slack': 'https://slack.com/ssb/download-osx-universal',
    'teamviewer': 'https://download.teamviewer.com/download/TeamViewer.dmg',
    'teamviewer qs': 'https://download.teamviewer.com/download/TeamViewerQS.dmg',
    'telegram': 'https://telegram.org/dl/macos',
    'the unarchiver': 'https://dl.devmate.com/com.macpaw.site.theunarchiver/TheUnarchiver.dmg',
    'vlc': 'https://www.videolan.org/vlc/download-macosx.html',
    'zotero': 'https://www.zotero.org/download/client/dl?channel=release&platform=mac',
    'zoom': 'https://zoom.us/client/latest/ZoomInstallerIT.pkg',
    # Landing pages
    'alfred': 'https://www.alfredapp.com',
    'appcleaner': 'https://freemacsoft.net/appcleaner/',
    'aquamacs': 'https://aquamacs.org/download.html',
    'audacity': 'https://www.audacityteam.org/download/mac/',
    'blender': 'https://www.blender.org/download/',
    'ccleaner': 'https://www.ccleaner.com/ccleaner/download?mac',
    'coconutbattery': 'https://coconut-flavour.com/coconutbattery/',
    'db browser': 'https://sqlitebrowser.org/dl/',
    'davinci resolve': 'https://www.blackmagicdesign.com/products/davinciresolve/',
    'dragonframe': 'https://dragonframe.com/downloads/',
    'evernote': 'https://evernote.com/download',
    'filezilla': 'https://filezilla-project.org/download.php?platform=osx',
    'gimp': 'https://www.gimp.org/downloads/',
    'github desktop': 'https://desktop.github.com/',
    'google android studio': 'https://developer.android.com/studio',
    'google earth pro': 'https://www.google.com/earth/versions/#earth-pro',
    'grandperspective': 'https://sourceforge.net/projects/grandperspectiv/files/latest/download',
    'handbrake': 'https://handbrake.fr/downloads.php',
    'intellij idea': 'https://www.jetbrains.com/idea/download/#section=mac',
    'lastpass': 'https://lastpass.com/misc_download2.php',
    'microsoft skype': 'https://www.skype.com/en/get-skype/',
    'microsoft visual studio code': 'https://code.visualstudio.com/download',
    'musescore': 'https://musescore.org/en',
    'omnissa horizon client': 'https://customerconnect.omnissa.com/downloads/info/slug/virtual_desktop_and_apps/omnissa_horizon_clients/8',
    'openoffice': 'https://www.openoffice.org/download/',
    'opera': 'http://www.opera.com/download/get/?partner=www&opsys=MacOS',
    'qgis': 'https://www.qgis.org/en/site/forusers/download.html',
    'r': 'https://cran.r-project.org/bin/macosx/',
    'rstudio': 'https://posit.co/download/rstudio-desktop/',
    'skim': 'https://skim-app.sourceforge.io',
    'solstice': 'https://www.mersive.com/download/',
    'sublime text': 'https://www.sublimetext.com/download',
    'textmate': 'https://macromates.com/download',
    'vmware fusion': 'https://www.vmware.com/products/fusion/fusion-evaluation.html',
    'virtualbox': 'https://www.virtualbox.org/wiki/Downloads',
    'vivaldi': 'https://vivaldi.com/download/',
    'wireshark': 'https://www.wireshark.org/download.html',
    'xquartz': 'https://www.xquartz.org/',
}

TITLE_ALIASES: Dict[str, str] = {
    'filezilla client': 'filezilla',
    'microsoft defender atp': 'microsoft defender',
    'microsoft excel 365': 'microsoft excel',
    'microsoft onedrive 365': 'microsoft onedrive',
    'microsoft onenote 365': 'microsoft onenote',
    'microsoft outlook 365': 'microsoft outlook',
    'microsoft powerpoint 365': 'microsoft powerpoint',
    'microsoft teams classic': 'microsoft teams',
    'microsoft word 365': 'microsoft word',
    'ms autoupdate': 'microsoft autoupdate',
    'ms defender': 'microsoft defender',
    'ms edge': 'microsoft edge',
    'ms excel': 'microsoft excel',
    'ms intune company portal': 'microsoft intune company portal',
    'ms onedrive': 'microsoft onedrive',
    'ms onenote': 'microsoft onenote',
    'ms outlook': 'microsoft outlook',
    'ms powerpoint': 'microsoft powerpoint',
    'ms teams': 'microsoft teams',
    'ms word': 'microsoft word',
    'ms azure storage explorer': 'microsoft azure storage explorer',
    'open office': 'openoffice',
    'visual studio code': 'microsoft visual studio code',
    'vs code': 'microsoft visual studio code',
    'x quartz': 'xquartz',
}

TITLE_CANDIDATES: List[str] = sorted(
    set(list(DOWNLOAD_URLS.keys()) + list(TITLE_ALIASES.keys()) + [
        'mozilla firefox',
        'mozilla firefox esr',
        'mozilla thunderbird',
    ]),
    key=len,
    reverse=True,
)

_VERSION_CACHE: Dict[str, Dict[str, str]] = {}

# ============================================================================
# APPLESCRIPT UTILITIES
# ============================================================================

def run_applescript(script: str, env: Optional[Dict[str, str]] = None) -> str:
    """Execute an AppleScript and return stdout."""
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or 'AppleScript execution failed')
    return result.stdout.strip()


def show_popup(message: str) -> None:
    """Display a simple dialog popup."""
    env = os.environ.copy()
    env['POPUP_TEXT'] = message
    script = r'''
set popupText to system attribute "POPUP_TEXT"
display dialog popupText with title "Mac Package Updates" buttons {"OK"} default button "OK"
'''
    run_applescript(script, env=env)


def prompt_download_action(title: str, version: str, has_url: bool) -> str:
    """Prompt user for download action (Open, Skip, or Cancel Remaining)."""
    env = os.environ.copy()
    env['APP_TITLE'] = title
    env['APP_VERSION'] = version
    env['HAS_URL'] = '1' if has_url else '0'
    script = r'''
set appTitle to system attribute "APP_TITLE"
set appVersion to system attribute "APP_VERSION"
set hasURL to system attribute "HAS_URL"

if hasURL is "1" then
    set promptText to "Open download page for " & appTitle & " " & appVersion & "?"
    set theButtons to {"Cancel Remaining", "Skip", "Open"}
    set defaultButton to "Open"
else
    set promptText to "No download mapping was found for " & appTitle & " " & appVersion & "."
    set theButtons to {"Cancel Remaining", "Skip"}
    set defaultButton to "Skip"
end if

set buttonChoice to button returned of (display dialog promptText with title "Mac Package Updates" buttons theButtons default button defaultButton)
return buttonChoice
'''
    return run_applescript(script, env=env)


def extract_emails_from_mail() -> None:
    """Extract emails from Mail app and save to raw_email.txt."""
    apple_script = '''
tell application "Mail"
    set senderEmail to "oit-macmgmt-sa@ohio.edu"
    set rawEmailContent to ""
    set desktopPath to POSIX path of (path to desktop)
    set outputFolder to desktopPath & "email/"
    set rawFilePath to outputFolder & "raw_email.txt"

    do shell script "mkdir -p " & quoted form of outputFolder

    try
        set targetMailbox to mailbox "Mac Package Updates" of mailbox "Jamf" of account "Exchange"
    on error
        display dialog "Error: Could not find 'Mac Package Updates' under 'Jamf' in account 'Exchange'."
        return
    end try

    set msgList to (messages of targetMailbox whose sender contains senderEmail)

    if (count of msgList) = 0 then
        display dialog "Error: No emails found from " & senderEmail & " in 'Mac Package Updates'."
        return
    end if

    repeat with msg in msgList
        set emailSource to source of msg
        if emailSource is not missing value and emailSource is not "" then
            set rawEmailContent to rawEmailContent & emailSource & "\\n\\n"
            set read status of msg to true
        end if
    end repeat

    set fileRef to open for access POSIX file rawFilePath with write permission
    set eof of fileRef to 0
    write rawEmailContent to fileRef
    close access fileRef
end tell
'''
    logging.info("Extracting emails from Mail app...")
    result = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error executing AppleScript: {result.stderr}")
        raise RuntimeError("AppleScript execution failed")


def version_key(version: str) -> Tuple:
    """Return a comparison key that treats numeric chunks numerically."""
    parts = re.findall(r"\d+|[A-Za-z]+", version)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part.lower()))
    return tuple(key)


# ============================================================================
# EMAIL EXTRACTION & RTF GENERATION
# ============================================================================

def extract_and_generate_rtf() -> None:
    """Extract titles/versions from raw email and generate RTF file."""
    logging.info("Starting email extraction and RTF generation...")
    
    # Extract emails from Mail
    extract_emails_from_mail()
    
    # Load exclusion list
    try:
        with open(EXCLUSION_FILE_PATH, 'r') as f:
            excluded_titles = {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        logging.warning(f"Exclusion file not found at {EXCLUSION_FILE_PATH}")
        excluded_titles = set()
    
    # Load raw email content
    try:
        with open(RAW_EMAIL_PATH, 'r') as f:
            email_content = f.read()
    except FileNotFoundError:
        logging.error(f"Raw email file not found at {RAW_EMAIL_PATH}")
        raise
    
    # Extract title and version
    title_version_pattern = r"Title:\s*(.*?)<br>Version:\s*(.*?)<br>"
    matches = re.findall(title_version_pattern, email_content)
    
    title_version_dict = {}
    for title, version in matches:
        version = version.strip()
        if title in excluded_titles:
            continue
        if title in title_version_dict:
            if version_key(version) > version_key(title_version_dict[title]):
                title_version_dict[title] = version
        else:
            title_version_dict[title] = version
    
    # Sort titles alphabetically
    sorted_titles = sorted(title_version_dict.items())
    
    # List of titles that should be prefixed with "Install Latest "
    install_prefix_keywords = [
        "visual studio code",
        "iterm2",
        "postman",
        "github desktop",
    ]
    
    # List of titles that should have the auto-install note appended
    auto_install_keywords = [
        "jamf protect",
        "microsoft autoupdate",
        "microsoft defender atp",
        "self service",
    ]
    
    # Get current date
    current_date = datetime.now().strftime("%d%b%Y")
    
    # Write output as RTF
    with open(DEFAULT_RTF_PATH, 'w') as out_file:
        out_file.write("{\\rtf1\\ansi\\deff0\n")
        out_file.write("{\\b The following applications have been added to Patch Management.}\\par\n\n")
        for title, version in sorted_titles:
            lower_title = title.lower()
            # Append " (installing automatically)" for matching auto-install titles
            auto_text = " (installing automatically)" if any(k in lower_title for k in auto_install_keywords) else ""
            line_body = f"{title} {version}{auto_text}\\par\n"
            if any(keyword in lower_title for keyword in install_prefix_keywords):
                # Only "Install Latest" is bold in the RTF; package name and version remain normal.
                out_file.write("{\\b Install Latest} " + line_body)
            else:
                out_file.write(line_body)
        out_file.write(f"\\par Downloaded, repackaged, and signed on {current_date} by {USER_NAME}\\par\n")
        out_file.write(f"Downloaded on {current_date} by {USER_NAME}\\par\n")
        out_file.write("}")
    
    # Delete raw_email.txt
    try:
        os.remove(RAW_EMAIL_PATH)
        logging.info("Deleted raw_email.txt after processing.")
    except Exception as e:
        logging.warning(f"Could not delete raw_email.txt: {e}")
    
    logging.info(f"RTF file generated with {len(sorted_titles)} applications.")
    show_popup(f"RTF file generated with {len(sorted_titles)} applications.")


# ============================================================================
# RTF PARSING & URL RESOLUTION
# ============================================================================

def normalize_title(title: str) -> str:
    """Normalize a title for comparison."""
    text = title.strip().lower()
    text = text.replace('&', 'and')
    text = re.sub(r'\s+', ' ', text)
    return text


def fetch_json(url: str) -> Dict[str, str]:
    """Fetch JSON from URL with caching."""
    if url in _VERSION_CACHE:
        return _VERSION_CACHE[url]

    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode('utf-8'))
        _VERSION_CACHE[url] = payload
        return payload


def get_mozilla_download_url(canonical: str) -> Optional[str]:
    """Get download URL for Mozilla products."""
    try:
        if canonical == 'mozilla firefox':
            versions = fetch_json(MOZILLA_FIREFOX_VERSIONS_URL)
            version = versions.get('LATEST_FIREFOX_VERSION', '').strip()
            if version:
                return f'https://archive.mozilla.org/pub/firefox/releases/{version}/mac/en-US/'
        elif canonical == 'mozilla firefox esr':
            versions = fetch_json(MOZILLA_FIREFOX_VERSIONS_URL)
            version = versions.get('FIREFOX_ESR', '').strip()
            if version:
                return f'https://archive.mozilla.org/pub/firefox/releases/{version}/mac/en-US/'
        elif canonical == 'mozilla thunderbird':
            versions = fetch_json(MOZILLA_THUNDERBIRD_VERSIONS_URL)
            version = versions.get('LATEST_THUNDERBIRD_VERSION', '').strip()
            if version:
                return f'https://archive.mozilla.org/pub/thunderbird/releases/{version}/mac/en-US/'
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        logging.warning('Could not build Mozilla URL for %s: %s', canonical, exc)

    fallback_urls = {
        'mozilla firefox': 'https://ftp.mozilla.org/pub/firefox/releases/',
        'mozilla firefox esr': 'https://ftp.mozilla.org/pub/firefox/releases/',
        'mozilla thunderbird': 'https://archive.mozilla.org/pub/thunderbird/releases/',
    }
    return fallback_urls.get(canonical)


def resolve_download_url(title: str) -> Optional[str]:
    """Resolve a title to its download URL."""
    normalized = normalize_title(title)
    canonical = TITLE_ALIASES.get(normalized, normalized)

    if canonical in {'mozilla firefox', 'mozilla firefox esr', 'mozilla thunderbird'}:
        return get_mozilla_download_url(canonical)

    return DOWNLOAD_URLS.get(canonical)


def convert_rtf_to_text(rtf_path: Path) -> str:
    """Convert RTF to plain text."""
    if not rtf_path.exists():
        raise FileNotFoundError(f'RTF file not found: {rtf_path}')

    textutil = shutil.which('textutil')
    if textutil:
        result = subprocess.run(
            [textutil, '-convert', 'txt', '-stdout', str(rtf_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout

    raw = rtf_path.read_text(encoding='utf-8', errors='ignore')
    raw = re.sub(r'\\[a-z]+-?\d* ?', '', raw)
    raw = raw.replace('{', '').replace('}', '')
    raw = raw.replace('\\', '\n')
    return raw


def clean_text_lines(text: str) -> List[str]:
    """Clean and split text into lines."""
    lines: List[str] = []
    for line in text.splitlines():
        cleaned = line.strip().replace('\xa0', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        if not cleaned:
            continue
        lines.append(cleaned)
    return lines


def is_footer_or_heading(line: str) -> bool:
    """Check if a line is a footer or heading."""
    lower = line.lower()
    return (
        lower == 'the following applications have been added to patch management.'
        or lower.startswith('downloaded, repackaged, and signed on ')
        or lower.startswith('downloaded on ')
    )


def parse_app_line(line: str) -> Optional[Tuple[str, str]]:
    """Parse an application line from RTF."""
    cleaned = line.strip()
    if cleaned.lower().startswith('install latest '):
        cleaned = cleaned[len('Install Latest '):].strip()
    cleaned = re.sub(r'\s*\(installing automatically\)$', '', cleaned, flags=re.IGNORECASE)

    normalized_line = normalize_title(cleaned)
    for candidate in TITLE_CANDIDATES:
        if normalized_line == candidate or normalized_line.startswith(candidate + ' '):
            title_len = len(candidate)
            original_title = cleaned[:title_len]
            remainder = cleaned[title_len:].strip()
            if remainder:
                return original_title, remainder
            return original_title, ''

    match = re.match(r'^(.*?)(\d[\w.\- ]*)$', cleaned)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None


def extract_titles_from_rtf(rtf_path: Path) -> List[Tuple[str, str]]:
    """Extract application titles and versions from RTF."""
    text = convert_rtf_to_text(rtf_path)
    lines = clean_text_lines(text)

    titles: List[Tuple[str, str]] = []
    for line in lines:
        if is_footer_or_heading(line):
            continue
        parsed = parse_app_line(line)
        if parsed:
            titles.append(parsed)
        else:
            logging.warning('Could not parse RTF line: %s', line)
    return titles


def open_download_url(url: str) -> None:
    """Open a URL in the default browser."""
    subprocess.run(['open', url], check=False)


# ============================================================================
# GUIDED DOWNLOADS
# ============================================================================

def start_guided_downloads(items: Sequence[Tuple[str, str]]) -> None:
    """Start interactive download workflow."""
    logging.info('Starting guided downloads for %s titles from RTF.', len(items))
    opened_count = 0
    skipped_count = 0
    unmapped_titles: List[str] = []

    for title, version in items:
        url = resolve_download_url(title)
        choice = prompt_download_action(title, version, has_url=bool(url))

        if choice == 'Open' and url:
            logging.info('Opening download URL for %s: %s', title, url)
            open_download_url(url)
            opened_count += 1
        elif choice == 'Skip':
            logging.info('Skipped download for %s', title)
            skipped_count += 1
            if not url:
                unmapped_titles.append(title)
        elif choice == 'Cancel Remaining':
            logging.info('User cancelled remaining downloads.')
            break

    if unmapped_titles:
        logging.warning('No download mapping found for: %s', ', '.join(unmapped_titles))

    logging.info(
        'Guided downloads finished. Opened=%s, Skipped=%s, Unmapped=%s',
        opened_count,
        skipped_count,
        len(unmapped_titles),
    )
    show_popup('Downloads Completed.')


# ============================================================================
# MENU & MAIN WORKFLOW
# ============================================================================

def show_main_menu() -> str:
    """Display main menu and return user choice."""
    env = os.environ.copy()
    script = r'''
set menuChoice to button returned of (display dialog "Mac Package Update Manager" buttons {"Extract & Generate RTF", "Download from RTF", "Cancel"} default button "Download from RTF")
return menuChoice
'''
    return run_applescript(script, env=env)


def main() -> None:
    """Main entry point."""
    logging.info("Mac Package Update Manager started.")
    
    try:
        choice = show_main_menu()
        
        if choice == "Extract & Generate RTF":
            logging.info("User selected: Extract & Generate RTF")
            extract_and_generate_rtf()
        
        elif choice == "Download from RTF":
            logging.info("User selected: Download from RTF")
            if not DEFAULT_RTF_PATH.exists():
                show_popup(f"RTF file not found at:\n{DEFAULT_RTF_PATH}\n\nPlease generate it first using Extract & Generate RTF.")
                return
            
            logging.info('Reading RTF file from %s', DEFAULT_RTF_PATH)
            items = extract_titles_from_rtf(DEFAULT_RTF_PATH)
            if not items:
                raise RuntimeError('No application lines were found in the RTF file.')
            start_guided_downloads(items)
        
        elif choice == "Cancel":
            logging.info("User cancelled operation.")
            return
    
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        show_popup(f"An error occurred:\n{str(e)}\n\nCheck the log file for details.")


if __name__ == '__main__':
    main()
