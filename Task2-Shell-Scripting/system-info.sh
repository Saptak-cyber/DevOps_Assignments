#!/bin/bash
#===============================================================================
# system-info.sh — System Information Script
#
# Homework requirements covered:
#   - prints current date, hostname, username, disk usage, running processes
#   - uses variables to store and reuse data
#   - takes user input with `read -p`
#   - creates a directory with `mkdir`
#   - creates a file with `touch`
#   - stores the running-process information in that file using `>` redirection
#
# Usage:  ./system-info.sh          (interactive)
#         ./system-info.sh -y       (non-interactive, accepts the defaults)
#===============================================================================

# ---------------------------------------------------------------------------
# 0. Non-interactive flag, so the script can also run in CI / a screenshot loop
# ---------------------------------------------------------------------------
AUTO="no"
[ "${1:-}" = "-y" ] && AUTO="yes"

# ---------------------------------------------------------------------------
# 1. Store system data in VARIABLES using command substitution $( )
# ---------------------------------------------------------------------------
CURRENT_DATE=$(date)
DATE_STAMP=$(date +"%Y-%m-%d_%H-%M-%S")   # filesystem-safe timestamp
HOST_NAME=$(hostname)
USER_NAME=$(whoami)
KERNEL=$(uname -srm)
UPTIME_INFO=$(uptime)
PROCESS_COUNT=$(ps -e | wc -l)

# ---------------------------------------------------------------------------
# 2. Print the system information
# ---------------------------------------------------------------------------
echo "==============================================="
echo "         SYSTEM INFORMATION REPORT             "
echo "==============================================="
echo
echo "Current Date & Time : $CURRENT_DATE"
echo "Hostname            : $HOST_NAME"
echo "Username            : $USER_NAME"
echo "Kernel              : $KERNEL"
echo "Uptime              :$UPTIME_INFO"
echo "Process Count       : $PROCESS_COUNT"
echo

echo "-----------------------------------------------"
echo " DISK USAGE  (df -h)"
echo "-----------------------------------------------"
df -h
echo

echo "-----------------------------------------------"
echo " TOP 10 RUNNING PROCESSES BY MEMORY  (ps aux)"
echo "-----------------------------------------------"
ps aux | head -n 11
echo

# ---------------------------------------------------------------------------
# 3. Take user input with read -p
# ---------------------------------------------------------------------------
DEFAULT_DIR="system_reports"
DEFAULT_FILE="processes_${DATE_STAMP}.txt"

if [ "$AUTO" = "yes" ]; then
    REPORT_DIR="$DEFAULT_DIR"
    REPORT_FILE="$DEFAULT_FILE"
    echo "[auto mode] Using directory '$REPORT_DIR' and file '$REPORT_FILE'"
else
    read -p "Enter the directory name to store the report [$DEFAULT_DIR]: " REPORT_DIR
    read -p "Enter the report file name [$DEFAULT_FILE]: " REPORT_FILE
fi

# Fall back to the defaults if the user just pressed Enter
REPORT_DIR="${REPORT_DIR:-$DEFAULT_DIR}"
REPORT_FILE="${REPORT_FILE:-$DEFAULT_FILE}"

# Build the full path in a variable so it is written once and reused
REPORT_PATH="$REPORT_DIR/$REPORT_FILE"
echo

# ---------------------------------------------------------------------------
# 4. Create the directory with mkdir  (-p = no error if it already exists)
# ---------------------------------------------------------------------------
mkdir -p "$REPORT_DIR"
echo "[OK] Directory created : $REPORT_DIR"

# ---------------------------------------------------------------------------
# 5. Create the empty file with touch
# ---------------------------------------------------------------------------
touch "$REPORT_PATH"
echo "[OK] File created      : $REPORT_PATH"

# ---------------------------------------------------------------------------
# 6. Write the process information into the file with > and >> redirection
#      >   overwrites the file (used once, for the header)
#      >>  appends to it        (used for every section after that)
# ---------------------------------------------------------------------------
echo "===== SYSTEM REPORT =====" >  "$REPORT_PATH"
{
  echo "Generated on : $CURRENT_DATE"
  echo "Hostname     : $HOST_NAME"
  echo "User         : $USER_NAME"
  echo "Kernel       : $KERNEL"
  echo
  echo "===== DISK USAGE (df -h) ====="
} >> "$REPORT_PATH"

df -h >> "$REPORT_PATH"

{
  echo
  echo "===== RUNNING PROCESSES (ps aux) ====="
} >> "$REPORT_PATH"

# The required step: running-process information stored in the file via redirection
ps aux >> "$REPORT_PATH"

echo "[OK] Process information written to $REPORT_PATH"
echo

# ---------------------------------------------------------------------------
# 7. Verify what was written
# ---------------------------------------------------------------------------
LINE_COUNT=$(wc -l < "$REPORT_PATH")
FILE_SIZE=$(du -h "$REPORT_PATH" | cut -f1)

echo "-----------------------------------------------"
echo " VERIFICATION"
echo "-----------------------------------------------"
echo "Report path  : $REPORT_PATH"
echo "Lines written: $LINE_COUNT"
echo "File size    : $FILE_SIZE"
echo
echo "First 15 lines of the report (head -n 15):"
head -n 15 "$REPORT_PATH"
echo
echo "==============================================="
echo " Report generated successfully."
echo "==============================================="
