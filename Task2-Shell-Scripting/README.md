# Task 2 — Shell Scripting: System Information Script

A Bash script that gathers system information, asks the user where to save it, creates
the directory and file, and writes the running-process list into that file using output
redirection.

Files in this folder:

| File | Purpose |
|------|---------|
| `system-info.sh` | The system information script |
| `README.md` | This document — how to run it, and the captured output |

---

## 1. Requirement checklist

| # | Requirement | Where it is done in `system-info.sh` |
|---|---|---|
| 1 | Prints the current date | `CURRENT_DATE=$(date)` then `echo` |
| 2 | Prints the hostname | `HOST_NAME=$(hostname)` |
| 3 | Prints the username | `USER_NAME=$(whoami)` |
| 4 | Prints the disk usage | `df -h` |
| 5 | Prints the running processes | `ps aux \| head -n 11` |
| 6 | Uses variables | `CURRENT_DATE`, `HOST_NAME`, `USER_NAME`, `REPORT_DIR`, `REPORT_FILE`, `REPORT_PATH`, … |
| 7 | Takes user input with `read -p` | `read -p "Enter the directory name…" REPORT_DIR` |
| 8 | Creates a directory with `mkdir` | `mkdir -p "$REPORT_DIR"` |
| 9 | Creates a file with `touch` | `touch "$REPORT_PATH"` |
| 10 | Stores processes in the file with `>` | `echo "===== SYSTEM REPORT =====" > "$REPORT_PATH"` then `ps aux >> "$REPORT_PATH"` |

---

## 2. How to run

```bash
chmod +x system-info.sh     # make it executable
./system-info.sh            # interactive — it will prompt you twice
./system-info.sh -y         # non-interactive — accepts the default names
```

`chmod +x` is needed because a freshly created file has mode `644` (`rw-r--r--`) and
cannot be executed. Alternatively run it without the execute bit as `bash system-info.sh`.

---

## 3. Key concepts used in the script

### 3.1 Variables and command substitution

```bash
CURRENT_DATE=$(date)          # $( ) runs the command and captures its stdout
HOST_NAME=$(hostname)
echo "Date: $CURRENT_DATE"    # $VAR expands the value
```

* **No spaces around `=`.** `NAME = value` is parsed as running a command called `NAME`.
* Always **quote** expansions — `"$REPORT_DIR"` — so a directory name containing a space
  stays one argument.
* `${VAR:-default}` expands to `default` when `VAR` is unset **or empty**. That is how
  the script falls back when the user just presses Enter at a prompt.

### 3.2 `read -p`

```bash
read -p "Enter the directory name [system_reports]: " REPORT_DIR
```

`read` takes one line from stdin into a variable; `-p` prints a prompt first, on the same
line, without a trailing newline. Useful relatives: `-s` (silent, for passwords),
`-t 10` (timeout), `-n 1` (one character, for y/n prompts).

> Note: bash prints the `-p` prompt only when stdin is a terminal. If you pipe input in
> (`printf 'a\nb\n' | ./system-info.sh`), the read still works but the prompt text is not
> shown — that is why it is absent from the piped transcript in §5.

### 3.3 `mkdir` and `touch`

```bash
mkdir -p "$REPORT_DIR"     # -p creates parents AND does not error if it already exists
touch "$REPORT_PATH"       # creates an empty file, or just bumps the mtime if it exists
```

Without `-p`, re-running the script would fail with `mkdir: cannot create directory
'system_reports': File exists` — so `-p` makes the script **idempotent**.

### 3.4 Output redirection

| Syntax | Meaning |
|---|---|
| `cmd > file` | stdout to `file`, **truncating** it first |
| `cmd >> file` | stdout **appended** to `file` |
| `cmd 2> file` | stderr to `file` |
| `cmd > file 2>&1` | stdout and stderr to the same file |
| `cmd \| tee file` | print to the screen **and** save to the file |
| `{ a; b; } >> file` | append the output of a whole block — one open, not one per line |

The script uses `>` exactly once (to create/truncate the report header) and `>>` for
every section after it. Using `>` twice would silently throw away the earlier section.

```bash
echo "===== SYSTEM REPORT =====" >  "$REPORT_PATH"   # truncate + write header
df -h                            >> "$REPORT_PATH"   # append disk usage
ps aux                           >> "$REPORT_PATH"   # append the process list
```

### 3.5 The commands themselves

| Command | What it prints |
|---|---|
| `date` | Current date and time (`date +"%Y-%m-%d_%H-%M-%S"` for a filename-safe stamp) |
| `hostname` | The machine's network name |
| `whoami` | Effective username (`id -un` is the portable equivalent) |
| `uname -srm` | Kernel name, release and machine architecture |
| `uptime` | How long the machine has been up, plus load averages |
| `df -h` | Free/used space per mounted filesystem, human-readable |
| `ps aux` | Every process on the system with user, CPU%, MEM%, and command |
| `ps -e \| wc -l` | Process count |
| `wc -l < file` | Line count (with `<` so `wc` prints only the number, not the filename) |
| `du -h file \| cut -f1` | File size, first tab-separated field only |

---

## 4. Interactive run (what you see on a terminal)

```console
$ chmod +x system-info.sh
$ ./system-info.sh
===============================================
         SYSTEM INFORMATION REPORT
===============================================

Current Date & Time : Wed Sep  2 21:31:39 UTC 2026
Hostname            : ubuntu-vm
Username            : saptak
...
Enter the directory name to store the report [system_reports]: system_reports
Enter the report file name [processes_2026-09-02_21-31-39.txt]: processes_demo.txt

[OK] Directory created : system_reports
[OK] File created      : system_reports/processes_demo.txt
[OK] Process information written to system_reports/processes_demo.txt
```

---

## 5. Captured output (real run on Ubuntu 22.04)

Command used — the script was executed inside a Linux container so the output is genuine
Linux output rather than macOS:

```bash
docker run --rm -v "$PWD":/work -w /tmp/run ubuntu:22.04 bash -c '
  apt-get update -qq && apt-get install -y -qq procps hostname
  printf "system_reports\nprocesses_demo.txt\n" | bash /work/system-info.sh'
```

```text
===============================================
         SYSTEM INFORMATION REPORT
===============================================

Current Date & Time : Wed Sep  2 21:31:39 UTC 2026
Hostname            : 3889beb05080
Username            : root
Kernel              : Linux 6.12.76-linuxkit aarch64
Uptime              : 21:31:39 up 0 min,  0 users,  load average: 0.10, 0.03, 0.01
Process Count       : 6

-----------------------------------------------
 DISK USAGE  (df -h)
-----------------------------------------------
Filesystem            Size  Used Avail Use% Mounted on
overlay               453G  1.5G  428G   1% /
tmpfs                  64M     0   64M   0% /dev
shm                    64M     0   64M   0% /dev/shm
/run/host_mark/Users  461G  400G   62G  87% /work
/dev/vda1             453G  1.5G  428G   1% /etc/hosts
tmpfs                 4.0K     0  4.0K   0% /proc/scsi

-----------------------------------------------
 TOP 10 RUNNING PROCESSES BY MEMORY  (ps aux)
-----------------------------------------------
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0   3880  2792 ?        Ss   21:31   0:00 bash -c ...
root       214  0.0  0.0   3880  2800 ?        S    21:31   0:00 bash /work/system-info.sh
root       225  0.0  0.0   6448  2460 ?        R    21:31   0:00 ps aux
root       226  0.0  0.0   2240   992 ?        S    21:31   0:00 head -n 11


[OK] Directory created : system_reports
[OK] File created      : system_reports/processes_demo.txt
[OK] Process information written to system_reports/processes_demo.txt

-----------------------------------------------
 VERIFICATION
-----------------------------------------------
Report path  : system_reports/processes_demo.txt
Lines written: 20
File size    : 4.0K

First 15 lines of the report (head -n 15):
===== SYSTEM REPORT =====
Generated on : Wed Sep  2 21:31:39 UTC 2026
Hostname     : 3889beb05080
User         : root
Kernel       : Linux 6.12.76-linuxkit aarch64

===== DISK USAGE (df -h) =====
Filesystem            Size  Used Avail Use% Mounted on
overlay               453G  1.5G  428G   1% /
tmpfs                  64M     0   64M   0% /dev
shm                    64M     0   64M   0% /dev/shm
/run/host_mark/Users  461G  400G   62G  87% /work
/dev/vda1             453G  1.5G  428G   1% /etc/hosts
tmpfs                 4.0K     0  4.0K   0% /proc/scsi


===============================================
 Report generated successfully.
===============================================
```

A container has almost no processes running, which is why only 4 rows appear under
`ps aux`. On a normal desktop or VM the same script prints the full process table — the
`>>` redirection captures all of it into the report file.

### 5.1 Verifying the file was actually written

```console
$ ls -l system_reports/
total 4
-rw-r--r-- 1 root root 1247 Sep  2 21:31 processes_demo.txt

$ wc -l system_reports/processes_demo.txt
20 system_reports/processes_demo.txt

$ tail -n 6 system_reports/processes_demo.txt
===== RUNNING PROCESSES (ps aux) =====
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0   3880  2792 ?        Ss   21:31   0:00 bash -c ...
root       214  0.0  0.0   3880  2800 ?        S    21:31   0:00 bash /work/system-info.sh
root       227  0.0  0.0   6448  2528 ?        R    21:31   0:00 ps aux
```

---

## 6. Submission steps (public GitHub repo)

```bash
cd Task2-Shell-Scripting
git init
git add system-info.sh README.md
git commit -m "Add system information shell script with README output"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Make sure the repository visibility is set to **Public** when creating it on GitHub.

Add `system_reports/` to a `.gitignore` if you do not want generated reports committed:

```gitignore
system_reports/
```

---

## 7. Common mistakes to avoid

| Mistake | Symptom | Fix |
|---|---|---|
| `NAME = value` | `NAME: command not found` | Remove the spaces: `NAME=value` |
| Missing shebang | Runs under the wrong shell, `read -p` fails in `sh` | First line `#!/bin/bash` |
| Forgetting `chmod +x` | `Permission denied` | `chmod +x system-info.sh` |
| Using `>` twice | Earlier sections silently disappear | Use `>` once, `>>` afterwards |
| Unquoted `$VAR` with spaces | `mkdir: too many arguments` | Quote it: `mkdir -p "$DIR"` |
| `mkdir` without `-p` | Fails on the second run | `mkdir -p` |
| CRLF line endings (edited on Windows) | `bad interpreter: /bin/bash^M` | `dos2unix system-info.sh` |
