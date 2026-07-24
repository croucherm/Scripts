#!/bin/bash

###############################################################################
# install-kerberos-smb-printer.sh
#
# Creates or refreshes a Kerberos-authenticated SMB printer queue on macOS.
# Intended for deployment through a Jamf Pro policy.
#
# Jamf parameters:
# $4 = CUPS queue name
# $5 = Display name
# $6 = SMB device URI
# $7 = Path to compressed PPD
# $8 = Printer location
# $9 = Old queue to remove
#      Optional; queue deletion is currently disabled in this script.
#
# Optional environment variables:
#
# DEBUG=1
#   Enables shell command tracing with set -x.
#
# STRICT_VERIFY=1
#   Returns a nonzero exit code when post-installation option verification
#   produces warnings. The default is to log warnings but return success when
#   the queue was created and its URI was verified.
###############################################################################

set -euo pipefail

DEBUG="${DEBUG:-0}"
STRICT_VERIFY="${STRICT_VERIFY:-0}"

if [[ "$DEBUG" == "1" ]]; then
    set -x
fi

###############################################################################
# Configuration
###############################################################################

QUEUE_NAME="${4:-OIT-GROSVENOR-138-SMB-TEST}"
DISPLAY_NAME="${5:-OIT-GROSVENOR-138 SMB Test}"
DEVICE_URI="${6:-smb://oit-prt-wp007.oit.ohio.edu/OIT-GROSVENOR-138}"
PPD_GZ="${7:-/Library/Printers/PPDs/Contents/Resources/SHARP BP-C535WR.PPD.gz}"
LOCATION="${8:-Grosvenor Hall 138}"
OLD_QUEUE="${9:-}"

SCRIPT_TAG="install-kerberos-smb-printer"
TEMP_PPD=""
VERIFY_WARNINGS=0

###############################################################################
# Logging and utility functions
###############################################################################

log() {
    /usr/bin/printf '[%s] %s\n' "$SCRIPT_TAG" "$*"
}

warn() {
    /usr/bin/printf '[%s] WARNING: %s\n' "$SCRIPT_TAG" "$*" >&2
}

die() {
    local exit_code="$1"
    shift

    /usr/bin/printf '[%s] ERROR: %s\n' "$SCRIPT_TAG" "$*" >&2
    exit "$exit_code"
}

add_verification_warning() {
    VERIFY_WARNINGS=$((VERIFY_WARNINGS + 1))
}

cleanup() {
    if [[ -n "${TEMP_PPD:-}" && -e "$TEMP_PPD" ]]; then
        /bin/rm -f "$TEMP_PPD"
    fi
}

get_queue_uri() {
    local lpstat_output

    if ! lpstat_output=$(
        /usr/bin/lpstat -v "$QUEUE_NAME" 2>/dev/null
    ); then
        return 1
    fi

    if [[ "$lpstat_output" != *": "* ]]; then
        return 1
    fi

    /usr/bin/printf '%s\n' "${lpstat_output#*: }"
}

trap cleanup EXIT

# Restrict newly created temporary files to the root account.
umask 077

###############################################################################
# Validate execution context
###############################################################################

# Jamf Pro policy scripts normally execute as root. Root privileges are
# required to create or modify system-wide CUPS printer queues.
if [[ "$(/usr/bin/id -u)" -ne 0 ]]; then
    die 1 "This script must run as root."
fi

###############################################################################
# Validate required commands
###############################################################################

REQUIRED_COMMANDS=(
    "/usr/bin/gzip"
    "/usr/bin/grep"
    "/usr/bin/lpoptions"
    "/usr/bin/lpstat"
    "/usr/bin/mktemp"
    "/usr/sbin/cupsaccept"
    "/usr/sbin/cupsenable"
    "/usr/sbin/lpadmin"
    "/usr/sbin/lpinfo"
)

for command_path in "${REQUIRED_COMMANDS[@]}"; do
    if [[ ! -x "$command_path" ]]; then
        die 2 "Required command is unavailable or not executable: $command_path"
    fi
done

###############################################################################
# Validate supplied configuration
###############################################################################

# Restrict queue names to a safe, predictable character set.
if [[ ! "$QUEUE_NAME" =~ ^[A-Za-z0-9._-]+$ ]]; then
    die 3 \
        "Invalid queue name '$QUEUE_NAME'. Allowed characters are letters, numbers, periods, underscores, and hyphens."
fi

if [[ -z "$DISPLAY_NAME" ]]; then
    die 4 "The printer display name cannot be empty."
fi

# Require an SMB URI containing a hostname and share name.
# Usernames and passwords must not be embedded in the URI.
if [[ ! "$DEVICE_URI" =~ ^smb://[^/@[:space:]]+/[^[:space:]]+$ ]]; then
    die 5 \
        "Invalid SMB URI '$DEVICE_URI'. Expected: smb://hostname/printer-share with no embedded credentials."
fi

if [[ -z "$LOCATION" ]]; then
    warn "Printer location is empty. The queue will be created without a useful location description."
fi

log "Configuration:"
log "  Queue name:  $QUEUE_NAME"
log "  Display name: $DISPLAY_NAME"
log "  Device URI:   $DEVICE_URI"
log "  PPD path:     $PPD_GZ"
log "  Location:     ${LOCATION:-Not specified}"

###############################################################################
# Confirm the macOS SMB printing backend
###############################################################################

if ! /usr/sbin/lpinfo -v 2>/dev/null |
    /usr/bin/grep -qx "network smb"; then

    die 6 "The Apple SMB CUPS backend is unavailable."
fi

log "Apple SMB CUPS backend detected."

###############################################################################
# Protect unrelated existing queues
###############################################################################

if /usr/bin/lpstat -p "$QUEUE_NAME" >/dev/null 2>&1; then
    if ! EXISTING_URI="$(get_queue_uri)"; then
        die 7 "The existing queue URI could not be determined: $QUEUE_NAME"
    fi

    log "Existing queue found: $QUEUE_NAME"
    log "Existing URI: $EXISTING_URI"

    if [[ "$EXISTING_URI" != "$DEVICE_URI" ]]; then
        die 8 \
            "Queue '$QUEUE_NAME' already exists with a different URI. Expected '$DEVICE_URI'; found '$EXISTING_URI'. No queue was modified or deleted."
    fi

    log "The existing queue uses the expected SMB URI."
    log "Its configuration will be refreshed without deleting the queue."
else
    log "No existing queue named '$QUEUE_NAME' was found."
    log "A new SMB printer queue will be created."
fi

###############################################################################
# Validate and expand the printer PPD
###############################################################################

if [[ ! -r "$PPD_GZ" ]]; then
    die 9 \
        "Printer PPD was not found or is not readable: $PPD_GZ. Install the printer driver before this script runs."
fi

GZIP_TEST_OUTPUT=""

if ! GZIP_TEST_OUTPUT=$(
    /usr/bin/gzip -t "$PPD_GZ" 2>&1
); then
    [[ -n "$GZIP_TEST_OUTPUT" ]] &&
        /usr/bin/printf '%s\n' "$GZIP_TEST_OUTPUT" >&2

    die 10 "The configured PPD is not a valid gzip-compressed file: $PPD_GZ"
fi

if ! TEMP_PPD=$(
    /usr/bin/mktemp "/private/tmp/${SCRIPT_TAG}.XXXXXX"
); then
    die 11 "Unable to create a secure temporary PPD file."
fi

GZIP_OUTPUT=""

if ! GZIP_OUTPUT=$(
    /usr/bin/gzip -dc "$PPD_GZ" > "$TEMP_PPD" 2>&1
); then
    [[ -n "$GZIP_OUTPUT" ]] &&
        /usr/bin/printf '%s\n' "$GZIP_OUTPUT" >&2

    die 12 "Unable to expand the printer PPD."
fi

if [[ ! -r "$TEMP_PPD" ]]; then
    die 13 "The expanded temporary PPD is not readable."
fi

if [[ ! -s "$TEMP_PPD" ]]; then
    die 14 "The expanded temporary PPD is empty."
fi

log "Printer PPD validated and expanded successfully."

###############################################################################
# LEGACY QUEUE REMOVAL — CURRENTLY DISABLED
#
# Re-enable only after the SMB deployment has been fully validated and queue
# removal has been formally approved.
#
# Tracking ticket: DWDS-496
# Disabled as of: 2026-07-24
#
# This block removes only the queue supplied through Jamf parameter 9 and only
# when that queue name differs from the SMB queue being deployed.
###############################################################################

# if [[ -n "$OLD_QUEUE" && "$OLD_QUEUE" != "$QUEUE_NAME" ]]; then
#     if /usr/bin/lpstat -p "$OLD_QUEUE" >/dev/null 2>&1; then
#         log "Removing legacy queue: $OLD_QUEUE"
#
#         if ! /usr/sbin/lpadmin -x "$OLD_QUEUE"; then
#             die 15 "Unable to remove legacy queue: $OLD_QUEUE"
#         fi
#     else
#         log "Legacy queue was not found: $OLD_QUEUE"
#     fi
# fi

###############################################################################

if [[ -n "$OLD_QUEUE" ]]; then
    warn \
        "Jamf parameter 9 specifies '$OLD_QUEUE', but legacy queue removal is disabled. No queue will be deleted."
fi

###############################################################################
# Create or update the SMB printer queue
###############################################################################

# auth-info-required=negotiate instructs CUPS to use Kerberos authentication.
#
# At print time, the SMB backend runs in the context of the user who submitted
# the job and uses that user's available Kerberos credentials to obtain or use
# a CIFS service ticket for the Windows print server.
#
# This script does not:
#   - Embed a username or password in the SMB URI
#   - Save user credentials
#   - Create or configure a machine Kerberos keytab
#   - Validate a user's Kerberos ticket during queue installation
#
# The submitting user must have a valid Kerberos identity when printing.
#
# printer-error-policy=abort-job prevents a failed or unauthorized job from
# stopping the entire local printer queue.

LPADMIN_OUTPUT=""

if LPADMIN_OUTPUT=$(
    /usr/sbin/lpadmin \
        -p "$QUEUE_NAME" \
        -E \
        -v "$DEVICE_URI" \
        -P "$TEMP_PPD" \
        -D "$DISPLAY_NAME" \
        -L "$LOCATION" \
        -o auth-info-required=negotiate \
        -o printer-error-policy=abort-job \
        -o printer-is-shared=false 2>&1
); then
    if [[ -n "$LPADMIN_OUTPUT" ]]; then
        log "lpadmin output:"
        /usr/bin/printf '%s\n' "$LPADMIN_OUTPUT"
    fi

    log "lpadmin completed successfully."
else
    LPADMIN_RESULT=$?

    /usr/bin/printf \
        '[%s] ERROR: lpadmin failed with exit code %s.\n' \
        "$SCRIPT_TAG" \
        "$LPADMIN_RESULT" >&2

    if [[ -n "$LPADMIN_OUTPUT" ]]; then
        /usr/bin/printf \
            '[%s] lpadmin diagnostic output:\n' \
            "$SCRIPT_TAG" >&2

        /usr/bin/printf '%s\n' "$LPADMIN_OUTPUT" >&2
    fi

    exit "$LPADMIN_RESULT"
fi

###############################################################################
# Accept jobs and enable the queue
###############################################################################

CUPSACCEPT_OUTPUT=""

if ! CUPSACCEPT_OUTPUT=$(
    /usr/sbin/cupsaccept "$QUEUE_NAME" 2>&1
); then
    [[ -n "$CUPSACCEPT_OUTPUT" ]] &&
        /usr/bin/printf '%s\n' "$CUPSACCEPT_OUTPUT" >&2

    die 16 "Unable to configure '$QUEUE_NAME' to accept print jobs."
fi

CUPSENABLE_OUTPUT=""

if ! CUPSENABLE_OUTPUT=$(
    /usr/sbin/cupsenable "$QUEUE_NAME" 2>&1
); then
    [[ -n "$CUPSENABLE_OUTPUT" ]] &&
        /usr/bin/printf '%s\n' "$CUPSENABLE_OUTPUT" >&2

    die 17 "Unable to enable printer queue '$QUEUE_NAME'."
fi

log "Printer queue is enabled and configured to accept jobs."

###############################################################################
# Verify the installed queue URI
###############################################################################

if ! ACTUAL_URI="$(get_queue_uri)"; then
    die 18 "Unable to determine the installed URI for '$QUEUE_NAME'."
fi

log "Installed URI: $ACTUAL_URI"

if [[ "$ACTUAL_URI" != "$DEVICE_URI" ]]; then
    die 19 \
        "Installed URI does not match the expected SMB URI. Expected '$DEVICE_URI'; found '$ACTUAL_URI'."
fi

log "Installed SMB URI verified."

###############################################################################
# Verify queue options
###############################################################################

OPTIONS_OUTPUT=""

if OPTIONS_OUTPUT=$(
    /usr/bin/lpoptions -p "$QUEUE_NAME" 2>&1
); then
    # Normalize any line breaks and pad the output with spaces so individual
    # option=value entries can be matched safely.
    NORMALIZED_OPTIONS=" ${OPTIONS_OUTPUT//$'\n'/ } "

    if [[ "$NORMALIZED_OPTIONS" == *" auth-info-required=negotiate "* ]]; then
        log "Kerberos authentication setting verified."
    else
        warn "Unable to confirm auth-info-required=negotiate through lpoptions."
        add_verification_warning
    fi

    if [[ "$NORMALIZED_OPTIONS" == *" printer-error-policy=abort-job "* ]]; then
        log "Printer error policy verified as abort-job."
    else
        warn "Unable to confirm printer-error-policy=abort-job through lpoptions."
        add_verification_warning
    fi
else
    warn "Unable to retrieve printer options for verification."
    [[ -n "$OPTIONS_OUTPUT" ]] &&
        /usr/bin/printf '%s\n' "$OPTIONS_OUTPUT" >&2

    add_verification_warning
fi

###############################################################################
# Report queue status
###############################################################################

PRINTER_STATUS=""

if PRINTER_STATUS=$(
    /usr/bin/lpstat -p "$QUEUE_NAME" -l 2>&1
); then
    log "Current printer status:"
    /usr/bin/printf '%s\n' "$PRINTER_STATUS"
else
    warn "Unable to retrieve the current printer status."
    [[ -n "$PRINTER_STATUS" ]] &&
        /usr/bin/printf '%s\n' "$PRINTER_STATUS" >&2

    add_verification_warning
fi

ACCEPTING_STATUS=""

if ACCEPTING_STATUS=$(
    /usr/bin/lpstat -a "$QUEUE_NAME" 2>&1
); then
    log "Current job-acceptance status:"
    /usr/bin/printf '%s\n' "$ACCEPTING_STATUS"
else
    warn "Unable to confirm that the queue is accepting jobs."
    [[ -n "$ACCEPTING_STATUS" ]] &&
        /usr/bin/printf '%s\n' "$ACCEPTING_STATUS" >&2

    add_verification_warning
fi

###############################################################################
# Final result
###############################################################################

if [[ "$VERIFY_WARNINGS" -gt 0 ]]; then
    warn \
        "Queue creation succeeded, but $VERIFY_WARNINGS post-installation verification warning(s) were recorded."

    if [[ "$STRICT_VERIFY" == "1" ]]; then
        die 20 \
            "STRICT_VERIFY=1 is enabled, so verification warnings are being treated as a policy failure."
    fi

    warn "Review the Jamf policy log before expanding the deployment scope."
else
    log "All required queue settings and status checks were verified."
fi

log "SMB printer configuration completed successfully."
log "No existing printer queues were deleted."

exit 0
