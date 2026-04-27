#!/usr/bin/env python3
import json
import logging
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# Default paths
FOLDER_PATH = Path(os.path.expanduser('~/Desktop/email'))
DEFAULT_RTF_PATH = FOLDER_PATH / 'Mac Package Updates.rtf'
LOG_FILE_PATH = FOLDER_PATH / 'script_log.txt'

FOLDER_PATH.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE_PATH),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MOZILLA_FIREFOX_VERSIONS_URL = 'https://product-details.mozilla.org/1.0/firefox_versions.json'
MOZILLA_THUNDERBIRD_VERSIONS_URL = 'https://product-details.mozilla.org/1.0/thunderbird_versions.json'


def normalize_title(title: str) -> str:
    text = title.strip().lower()
    text = text.replace('&', 'and')
    text = re.sub(r'\s+', ' ', text)
    return text


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


def run_applescript(script: str, env: Optional[Dict[str, str]] = None) -> str:
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
    env = os.environ.copy()
    env['POPUP_TEXT'] = message
    script = r'''
set popupText to system attribute "POPUP_TEXT"
display dialog popupText with title "Mac Package Updates" buttons {"OK"} default button "OK"
'''
    run_applescript(script, env=env)



def prompt_download_action(title: str, version: str, has_url: bool) -> str:
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



def open_download_url(url: str) -> None:
    subprocess.run(['open', url], check=False)



def fetch_json(url: str) -> Dict[str, str]:
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
    normalized = normalize_title(title)
    canonical = TITLE_ALIASES.get(normalized, normalized)

    if canonical in {'mozilla firefox', 'mozilla firefox esr', 'mozilla thunderbird'}:
        return get_mozilla_download_url(canonical)

    return DOWNLOAD_URLS.get(canonical)



def convert_rtf_to_text(rtf_path: Path) -> str:
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
    lines: List[str] = []
    for line in text.splitlines():
        cleaned = line.strip().replace('\xa0', ' ')
        cleaned = re.sub(r'\s+', ' ', cleaned)
        if not cleaned:
            continue
        lines.append(cleaned)
    return lines



def is_footer_or_heading(line: str) -> bool:
    lower = line.lower()
    return (
        lower == 'the following applications have been added to patch management.'
        or lower.startswith('downloaded, repackaged, and signed on ')
        or lower.startswith('downloaded on ')
    )



def parse_app_line(line: str) -> Optional[Tuple[str, str]]:
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



def start_guided_downloads(items: Sequence[Tuple[str, str]]) -> None:
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



def main() -> None:
    rtf_path = DEFAULT_RTF_PATH
    if len(os.sys.argv) > 1:
        rtf_path = Path(os.path.expanduser(os.sys.argv[1]))

    logging.info('Reading RTF file from %s', rtf_path)
    items = extract_titles_from_rtf(rtf_path)
    if not items:
        raise RuntimeError('No application lines were found in the RTF file.')
    start_guided_downloads(items)


if __name__ == '__main__':
    main()
