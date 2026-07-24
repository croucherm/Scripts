#!/bin/bash

# Jamf parameters:
# $4 = CUPS queue name
# $5 = Display name
# $6 = SMB device URI
# $7 = Path to compressed PPD
# $8 = Printer location
# $9 = Old queue to remove (optional; deletion currently disabled)

set -euo pipefail

QUEUE_NAME="${4:-OIT-GROSVENOR-138-SMB-TEST}"
DISPLAY_NAME="${5:-OIT-GROSVENOR-138 SMB Test}"
DEVICE_URI="${6:-smb://oit-prt-wp007.oit.ohio.edu/OIT-GROSVENOR-138}"
PPD_GZ="${7:-/Library/Printers/PPDs/Contents/Resources/SHARP BP-C535WR.PPD.gz}"
LOCATION="${8:-Grosvenor Hall 138}"
OLD_QUEUE="${9:-}"

TEMP_PPD="/private/tmp/SHARP_BP-C535WR.$$.ppd"

cleanup() {
    /bin/rm -f "$TEMP_PPD"
}

trap cleanup EXIT

echo "Configuring SMB printer queue: $QUEUE_NAME"
echo "Display name: $DISPLAY_NAME"
echo "Device URI: $DEVICE_URI"
echo "Location: $LOCATION"

# Jamf policies normally run as root.
if [[ "$(/usr/bin/id -u)" -ne 0 ]]; then
    echo "ERROR: This script must run as root."
    exit 1
fi

# Confirm that the Apple SMB printing backend is available.
if ! /usr/sbin/lpinfo -v 2>/dev/null |
    /usr/bin/grep -qx "network smb"; then
    echo "ERROR: The SMB CUPS backend is unavailable."
    exit 2
fi

# Confirm that the Sharp driver is installed.
if [[ ! -r "$PPD_GZ" ]]; then
    echo "ERROR: Sharp PPD was not found:"
    echo "$PPD_GZ"
    echo "Install the Sharp BP-C535WR driver before this script runs."
    exit 3
fi

# Expand the compressed vendor PPD.
if ! /usr/bin/gzip -dc "$PPD_GZ" > "$TEMP_PPD"; then
    echo "ERROR: Unable to expand the Sharp PPD."
    exit 4
fi

if [[ ! -s "$TEMP_PPD" ]]; then
    echo "ERROR: Expanded PPD is empty."
    exit 5
fi

###############################################################################
# LEGACY QUEUE REMOVAL — CURRENTLY DISABLED
#
# This block may be enabled later after SMB deployment has been fully tested.
# It removes only the queue identified by parameter 9 and only when it is
# different from the new SMB queue name.
###############################################################################

# if [[ -n "$OLD_QUEUE" && "$OLD_QUEUE" != "$QUEUE_NAME" ]]; then
#     if /usr/bin/lpstat -p "$OLD_QUEUE" >/dev/null 2>&1; then
#         echo "Removing legacy queue: $OLD_QUEUE"
#         /usr/sbin/lpadmin -x "$OLD_QUEUE"
#     else
#         echo "Legacy queue not found: $OLD_QUEUE"
#     fi
# fi

###############################################################################

# Protect any existing queue that happens to use the requested test queue name.
if /usr/bin/lpstat -p "$QUEUE_NAME" >/dev/null 2>&1; then
    EXISTING_URI=$(
        /usr/bin/lpstat -v "$QUEUE_NAME" 2>/dev/null |
        /usr/bin/sed -E 's/^device for [^:]+: //'
    )

    echo "Existing queue found: $QUEUE_NAME"
    echo "Existing URI: $EXISTING_URI"

    if [[ "$EXISTING_URI" != "$DEVICE_URI" ]]; then
        echo "ERROR: The queue already exists with a different URI."
        echo "Expected: $DEVICE_URI"
        echo "Actual:   $EXISTING_URI"
        echo "No existing queue was modified or deleted."
        exit 6
    fi

    echo "The existing SMB test queue already uses the expected URI."
    echo "Refreshing its configuration without deleting it."
else
    echo "Creating new SMB test queue: $QUEUE_NAME"
fi

# Create the SMB test queue or update the matching test queue in place.
#
# abort-job prevents a failed authentication attempt from pausing the entire
# local printer queue.
if /usr/sbin/lpadmin \
    -p "$QUEUE_NAME" \
    -E \
    -v "$DEVICE_URI" \
    -P "$TEMP_PPD" \
    -D "$DISPLAY_NAME" \
    -L "$LOCATION" \
    -o auth-info-required=negotiate \
    -o printer-error-policy=abort-job \
    -o printer-is-shared=false; then

    echo "lpadmin completed successfully."
else
    RESULT=$?
    echo "ERROR: lpadmin failed with exit code $RESULT."
    exit "$RESULT"
fi

/usr/sbin/cupsaccept "$QUEUE_NAME"
/usr/sbin/cupsenable "$QUEUE_NAME"

ACTUAL_URI=$(
    /usr/bin/lpstat -v "$QUEUE_NAME" 2>/dev/null |
    /usr/bin/sed -E 's/^device for [^:]+: //'
)

echo "Installed URI: $ACTUAL_URI"

if [[ "$ACTUAL_URI" != "$DEVICE_URI" ]]; then
    echo "ERROR: Installed URI does not match the expected SMB URI."
    echo "Expected: $DEVICE_URI"
    echo "Actual:   $ACTUAL_URI"
    exit 7
fi

if /usr/bin/lpoptions -p "$QUEUE_NAME" 2>/dev/null |
    /usr/bin/tr ' ' '\n' |
    /usr/bin/grep -qx 'auth-info-required=negotiate'; then
    echo "Kerberos authentication is configured."
else
    echo "WARNING: Unable to confirm auth-info-required=negotiate through lpoptions."
fi

if /usr/bin/lpoptions -p "$QUEUE_NAME" 2>/dev/null |
    /usr/bin/tr ' ' '\n' |
    /usr/bin/grep -qx 'printer-error-policy=abort-job'; then
    echo "Printer error policy is configured as abort-job."
else
    echo "WARNING: Unable to confirm printer-error-policy=abort-job."
fi

echo "Current printer status:"
/usr/bin/lpstat -p "$QUEUE_NAME" -l

echo "SMB printer configuration completed successfully."
echo "No existing printer queues were deleted."

exit 0
