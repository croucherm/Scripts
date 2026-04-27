import re
import os
import subprocess
import logging
from datetime import datetime

# Define constants
folder_path = os.path.expanduser('~/Desktop/email/')
raw_email_path = os.path.join(folder_path, 'raw_email.txt')
exclusion_file_path = os.path.join(folder_path, 'excluded_titles.txt')
output_file_path = os.path.join(folder_path, 'Mac Package Updates.rtf')
log_file_path = os.path.join(folder_path, 'script_log.txt')
user_name = "Mike"

# Ensure the folder exists
os.makedirs(folder_path, exist_ok=True)

# Set up logging
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Started processing emails.")

# AppleScript to extract emails
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

# Run the AppleScript
result = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
if result.returncode != 0:
    logging.error(f"Error executing AppleScript: {result.stderr}")
    raise RuntimeError("AppleScript execution failed")

# Get current date
current_date = datetime.now().strftime("%d%b%Y")

# Load exclusion list
try:
    with open(exclusion_file_path, 'r') as f:
        excluded_titles = {line.strip() for line in f if line.strip()}
except FileNotFoundError:
    logging.error(f"Exclusion file not found at {exclusion_file_path}")
    raise

# Load raw email content
try:
    with open(raw_email_path, 'r') as f:
        email_content = f.read()
except FileNotFoundError:
    logging.error(f"Raw email file not found at {raw_email_path}")
    raise

# Extract title and version
title_version_pattern = r"Title:\s*(.*?)<br>Version:\s*(.*?)<br>"
matches = re.findall(title_version_pattern, email_content)


def version_key(version: str):
    """Return a comparison key that treats numeric chunks numerically.

    Examples:
    - 147.0.7727.102 > 147.0.7727.56
    - 2025.3.3 Patch 1 > 2025.3.3
    """
    parts = re.findall(r"\d+|[A-Za-z]+", version)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part.lower()))
    return tuple(key)


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

# Write output as RTF
with open(output_file_path, 'w') as out_file:
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
    out_file.write(f"\\par Downloaded, repackaged, and signed on {current_date} by {user_name}\\par\n")
    out_file.write(f"Downloaded on {current_date} by {user_name}\\par\n")
    out_file.write("}")

# Delete raw_email.txt
try:
    os.remove(raw_email_path)
    logging.info("Deleted raw_email.txt after processing.")
except Exception as e:
    logging.warning(f"Could not delete raw_email.txt: {e}")

logging.info("Finished processing emails. Titles and versions saved.")
