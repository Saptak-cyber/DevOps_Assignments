# Task 1 — Linux Fundamentals

Covers the four Linux homework sub-tasks: soft/hard links, `adduser` vs `useradd`,
`journalctl`, and the command cheat sheet.

Files in this folder:

| File | Purpose |
|------|---------|
| `link-demo.sh` | Runnable script that creates, inspects and deletes soft & hard links |
| `README.md` | This document — theory, commands and captured output |

---

## Sub-task 1 — Soft Link vs Hard Link

### 1.1 The core idea

Every file on a Linux filesystem is really two things:

* an **inode** — the on-disk structure that holds the metadata (permissions, owner,
  timestamps, size) and the pointers to the actual data blocks;
* a **name** in a directory — a directory entry that maps a filename to an inode number.

A filename is *not* the file. It is a pointer to an inode.

* A **hard link** is simply a second directory entry pointing at the **same inode**.
  There is no "original" and "copy" — both names are equal citizens. The inode keeps a
  *link count*; the data is freed only when the count drops to 0.
* A **soft link** (symbolic link / symlink) is a **separate file with its own inode**
  whose content is just a text path string. Resolving it is an extra lookup step, so if
  the target path disappears the symlink "dangles".

### 1.2 Difference table

| Property | Hard Link | Soft (Symbolic) Link |
|---|---|---|
| Command | `ln target linkname` | `ln -s target linkname` |
| Inode number | **Same** as target | **Different** — own inode |
| Points to | The inode (the data itself) | A **path string** to the target |
| Target deleted | Link keeps working, data survives | Link **breaks** (dangling / red in `ls`) |
| Across filesystems / partitions | ❌ Not allowed | ✅ Allowed |
| Link to a directory | ❌ Not allowed (only root, and normally never) | ✅ Allowed |
| Size shown by `ls -l` | Same as the file | Length of the path string (e.g. `12`) |
| `ls -l` file type char | `-` (regular file) | `l` (link) with `-> target` |
| Link count of target | Increases by 1 | Unchanged |
| Extra disk usage | None (just a directory entry) | One small inode |
| Relative-path safety | N/A | Relative symlinks break if the link is moved |

### 1.3 Commands

```bash
# Create a soft link
ln -s /path/to/original.txt softlink.txt

# Create a hard link
ln /path/to/original.txt hardlink.txt

# Create a soft link to a directory
ln -s /var/log logs

# Inspect: -i shows inode number, column 3 is the hard-link count
ls -li

# Show what a symlink points at
readlink softlink.txt
readlink -f softlink.txt        # fully resolved absolute path

# Detailed metadata (GNU / Linux)
stat original.txt

# Find every hard link that shares an inode
find / -inum 201449103 2>/dev/null

# Find broken symlinks under the current directory
find . -xtype l

# Delete a link (removes the NAME only, never the other names)
rm softlink.txt
unlink hardlink.txt

# Overwrite an existing symlink safely (-f force, -n don't follow a dir symlink)
ln -sfn /new/target mylink
```

> **Careful:** `rm mylink/` (with a trailing slash) or `rm -r dirlink/` can operate on the
> *target directory's contents*. To remove a symlink to a directory, use
> `rm mylink` with no trailing slash.

### 1.4 Practical — run the demo

```bash
chmod +x link-demo.sh
./link-demo.sh
```

### 1.5 Captured output

```text
### 1. Setting up a clean demo directory: ./link-demo

### 2. Creating a SOFT link  ->  ln -s original.txt softlink.txt
### 3. Creating a HARD link  ->  ln original.txt hardlink.txt

### 4. Inspecting inodes and link counts (ls -li)
    Column 1 = inode number, column 3 = hard-link count
total 16
201449103 -rw-r--r--  2 saptakbanerjee  wheel  29 Sep  3 03:00 hardlink.txt
201449103 -rw-r--r--  2 saptakbanerjee  wheel  29 Sep  3 03:00 original.txt
201449104 lrwxr-xr-x  1 saptakbanerjee  wheel  12 Sep  3 03:00 softlink.txt -> original.txt

### 5. Reading the file through both links
--- cat softlink.txt ---
Hello from the original file
--- cat hardlink.txt ---
Hello from the original file

### 6. Writing through the hard link is visible in the original
--- cat original.txt ---
Hello from the original file
Line added via hardlink

### 7. Deleting the ORIGINAL file:  rm original.txt
total 8
201449103 -rw-r--r--  1 saptakbanerjee  wheel  53 Sep  3 03:00 hardlink.txt
201449104 lrwxr-xr-x  1 saptakbanerjee  wheel  12 Sep  3 03:00 softlink.txt -> original.txt

### 8. Soft link is now broken (dangling)
cat: softlink.txt: No such file or directory

### 9. Hard link still holds the data (inode has another name)
Hello from the original file
Line added via hardlink

### 10. Removing a link removes only the name, never the other names
total 8
201449103 -rw-r--r--  1 saptakbanerjee  wheel  53 Sep  3 03:00 hardlink.txt
```

### 1.6 Reading the output

1. `hardlink.txt` and `original.txt` share inode **201449103** and both show a link
   count of **2**. `softlink.txt` has its own inode **201449104** and a link count of 1.
2. The symlink's size is **12 bytes** — exactly `len("original.txt")`, because that path
   string *is* its content.
3. Appending through `hardlink.txt` changed `original.txt`, proving there is one inode.
4. After `rm original.txt`, the hard link's count dropped 2 → 1 and the data is intact;
   the symlink still points at the now-nonexistent name and fails with
   `No such file or directory`.

### 1.7 Interview answers

**Q: What is the difference between a hard link and a soft link?**
A hard link is an additional directory entry for the same inode, so both names are
indistinguishable and the data survives until every name is removed. A soft link is a
separate file whose contents are a path to another file; it resolves at access time and
breaks if the target is moved or deleted.

**Q: Why can't a hard link cross filesystems?**
Inode numbers are unique only *within* a filesystem. A directory entry stores an inode
number with no device information, so it can only refer to an inode on the same
filesystem. A symlink stores a path string, which the kernel resolves from the root, so
it can point anywhere — even at a path that does not exist yet.

**Q: Why are hard links to directories forbidden?**
They would allow cycles in the directory tree, which would break tree-walking tools
(`find`, `du`, `rm -r`) and make the "one parent per directory" invariant behind `..`
impossible to maintain. `.` and `..` are the only hard links to directories the kernel
creates itself.

**Q: What happens to the data when you delete a file with 3 hard links?**
Nothing is freed. The link count goes 3 → 2. Blocks are released only when both the link
count reaches 0 **and** no process holds the file open.

**Q: What is a dangling symlink?**
A symlink whose target path does not exist. Creating one is legal — the target is never
validated at creation time.

**Q: Which one does `cp` follow by default?**
`cp` follows symlinks and copies the *target's* content. `cp -d` (or `cp -a`) preserves
the link itself. `cp -l` creates hard links instead of copying data.

---

## Sub-task 2 — `adduser` vs `useradd`

### 2.1 What each one is

| | `useradd` | `adduser` |
|---|---|---|
| Type | Low-level **binary** (`/usr/sbin/useradd`) | High-level **Perl script** (Debian/Ubuntu) wrapping `useradd` |
| Package | `shadow-utils` / `passwd` | `adduser` (Debian family only) |
| Interactive | No — silent, flag-driven | Yes — prompts for password, full name, room, phone |
| Home directory | **Not** created unless `-m` is passed | Created automatically from `/etc/skel` |
| Password | Account left locked until `passwd user` is run | Prompts for it immediately |
| Shell | Uses `/etc/default/useradd` (often `/bin/sh`) | `/bin/bash` per `/etc/adduser.conf` |
| Group | Depends on `USERGROUPS_ENAB` | Always creates a matching user-private group |
| Availability | Every Linux distro | Debian/Ubuntu (RHEL 9+ ships a limited `adduser`→`useradd` symlink) |
| Best for | **Scripts, automation, Dockerfiles, Ansible** | **Humans at an interactive terminal** |

### 2.2 Which is preferred on Ubuntu, and why

**`adduser` is the recommended command on Ubuntu/Debian for creating a real user by hand.**

Reasons:
* It reads `/etc/adduser.conf`, so it applies the distro's policy for UID ranges, home
  directory permissions and default shell — consistently, every time.
* It creates and populates `$HOME` from `/etc/skel` automatically. A very common beginner
  bug is running plain `useradd bob` and ending up with a user who has no home directory
  and lands in `/` on login.
* It prompts for the password, so the account is usable immediately instead of locked.
* It creates the user-private group and sets sane ownership/permissions on the home dir.
* Debian's own `useradd(8)` man page says: *"useradd is a low level utility for adding
  users. On Debian, administrators should usually use adduser(8) instead."*

**Use `useradd` when you are scripting**, because it is non-interactive, has stable flags
and exists on every distro — which is exactly what a Dockerfile or an Ansible role needs.

### 2.3 Commands

```bash
# --- Recommended interactive way on Ubuntu ---
sudo adduser devopsuser

# Add to the sudo group
sudo adduser devopsuser sudo

# Create a system account with no home and no login shell
sudo adduser --system --no-create-home --shell /usr/sbin/nologin svcuser

# --- Scripted / portable way ---
sudo useradd -m -s /bin/bash -c "DevOps Test User" -G sudo devopsuser
sudo passwd devopsuser              # required: useradd leaves the account locked

# Non-interactive password set (for scripts/CI)
echo 'devopsuser:StrongPass123' | sudo chpasswd

# --- Verify ---
id devopsuser
grep devopsuser /etc/passwd
grep devopsuser /etc/group
sudo ls -la /home/devopsuser
getent passwd devopsuser
sudo passwd -S devopsuser           # P = usable password, L = locked

# --- Modify / delete ---
sudo usermod -aG docker devopsuser  # -a is essential, without it groups are REPLACED
sudo deluser --remove-home devopsuser     # Debian/Ubuntu
sudo userdel -r devopsuser                # portable
```

### 2.4 Practical — create a test user (expected transcript)

```console
$ sudo adduser devopsuser
Adding user `devopsuser' ...
Adding new group `devopsuser' (1001) ...
Adding new user `devopsuser' (1001) with group `devopsuser' ...
Creating home directory `/home/devopsuser' ...
Copying files from `/etc/skel' ...
New password:
Retype new password:
passwd: password updated successfully
Changing the user information for devopsuser
Enter the new value, or press ENTER for the default
        Full Name []: DevOps Test User
        Room Number []:
        Work Phone []:
        Home Phone []:
        Other []:
Is the information correct? [Y/n] Y

$ id devopsuser
uid=1001(devopsuser) gid=1001(devopsuser) groups=1001(devopsuser)

$ grep devopsuser /etc/passwd
devopsuser:x:1001:1001:DevOps Test User,,,:/home/devopsuser:/bin/bash

$ sudo ls -la /home/devopsuser
total 20
drwxr-x--- 2 devopsuser devopsuser 4096 Sep  3 03:10 .
drwxr-xr-x 4 root       root       4096 Sep  3 03:10 ..
-rw-r--r-- 1 devopsuser devopsuser  220 Sep  3 03:10 .bash_logout
-rw-r--r-- 1 devopsuser devopsuser 3771 Sep  3 03:10 .bashrc
-rw-r--r-- 1 devopsuser devopsuser  807 Sep  3 03:10 .profile
```

Contrast with bare `useradd`:

```console
$ sudo useradd testraw
$ grep testraw /etc/passwd
testraw:x:1002:1002::/home/testraw:/bin/sh
$ sudo ls -la /home/testraw
ls: cannot access '/home/testraw': No such file or directory   # <-- no home dir!
$ sudo passwd -S testraw
testraw L 09/03/2026 0 99999 7 -1                              # <-- L = locked
```

> The transcripts above are the expected Ubuntu output. This assignment was authored on
> macOS, where `adduser`/`useradd` do not exist — run them inside an Ubuntu VM,
> WSL, or `docker run -it ubuntu:22.04 bash` to reproduce and screenshot.

### 2.5 Interview answers

**Q: Which do you use in a Dockerfile?** `useradd` — `adduser` is Debian-only and
interactive. The idiomatic line is
`RUN useradd -m -u 1000 -s /bin/bash app && chown -R app /app`.

**Q: A new user can log in but lands in `/` with no dotfiles. Why?**
They were created with `useradd` without `-m`, so no home directory was made from
`/etc/skel`. Fix: `sudo mkhomedir_helper user` or `usermod -m -d /home/user user`.

**Q: What's the danger of `usermod -G docker user`?** Without `-a` it *replaces* the
user's entire supplementary group list, silently dropping `sudo`, `adm`, etc. Always
`usermod -aG`.

---

## Sub-task 3 — `journalctl`

### 3.1 What it is

`journalctl` is the query tool for the **systemd journal** — the binary, indexed,
structured log store written by `systemd-journald`. Instead of grepping plain text under
`/var/log`, every log record carries metadata fields (`_SYSTEMD_UNIT`, `_PID`, `_UID`,
`PRIORITY`, `_HOSTNAME`, `_BOOT_ID`), so you can filter by unit, by boot, by priority or
by time range instead of by string matching.

It collects everything in one place:
* stdout/stderr of every systemd service,
* kernel ring buffer messages (what `dmesg` shows),
* anything sent to syslog or the native journal API,
* audit records and early-boot / initrd messages.

**Storage:** controlled by `Storage=` in `/etc/systemd/journald.conf`.
`volatile` = RAM only (`/run/log/journal`, lost on reboot — Ubuntu's default when
`/var/log/journal` is absent); `persistent` = kept on disk in `/var/log/journal`.

Enable persistence:
```bash
sudo mkdir -p /var/log/journal
sudo systemd-tmpfiles --create --prefix /var/log/journal
sudo systemctl restart systemd-journald
```

### 3.2 Commands

```bash
# --- Basics ---
journalctl                       # everything, oldest first, in a pager
journalctl -e                    # jump to the end
journalctl -r                    # reverse: newest first
journalctl -n 50                 # last 50 lines
journalctl -f                    # follow live (the `tail -f` of systemd)
journalctl --no-pager            # plain stdout, good for piping/scripts

# --- Per service (the everyday use) ---
journalctl -u nginx.service
journalctl -u nginx -f                    # live tail of one service
journalctl -u nginx -n 100 --no-pager
journalctl -u nginx -u mysql              # two units at once
journalctl _PID=1234                      # by process id
journalctl /usr/sbin/sshd                 # by executable path

# --- Time filters ---
journalctl --since today
journalctl --since "2026-09-03 09:00:00" --until "2026-09-03 12:00:00"
journalctl --since "1 hour ago"
journalctl -u ssh --since "10 min ago"

# --- Boots ---
journalctl -b                    # current boot only
journalctl -b -1                 # previous boot (why did it crash?)
journalctl --list-boots

# --- Severity (0 emerg .. 7 debug) ---
journalctl -p err                # err and worse
journalctl -p warning..err
journalctl -b -p err             # this boot's errors -- best first triage command

# --- Kernel / hardware ---
journalctl -k                    # kernel messages (= dmesg)
journalctl -k -b -1

# --- Output formats ---
journalctl -u nginx -o json-pretty      # all metadata fields
journalctl -u nginx -o cat              # message text only
journalctl -o short-iso                 # ISO-8601 timestamps
journalctl -u nginx -x                  # add explanatory catalog text

# --- Disk usage / cleanup ---
journalctl --disk-usage
sudo journalctl --vacuum-size=200M
sudo journalctl --vacuum-time=7d
sudo journalctl --verify

# --- Combining ---
journalctl -u docker -p err --since "24 hours ago" --no-pager | tail -20
```

### 3.3 Practical — check logs for a specific service

```console
$ sudo systemctl status nginx
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2026-09-03 03:12:41 IST; 2min 8s ago
   Main PID: 4123 (nginx)
      Tasks: 3 (limit: 4657)
     Memory: 4.1M
        CPU: 21ms
     CGroup: /system.slice/nginx.service
             ├─4123 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
             └─4124 nginx: worker process

$ journalctl -u nginx.service -n 10 --no-pager
Sep 03 03:12:41 ubuntu-vm systemd[1]: Starting A high performance web server...
Sep 03 03:12:41 ubuntu-vm systemd[1]: Started A high performance web server and a reverse proxy server.
Sep 03 03:13:02 ubuntu-vm nginx[4124]: 127.0.0.1 - - [03/Sep/2026:03:13:02 +0530] "GET / HTTP/1.1" 200 615 "-" "curl/7.81.0"

$ journalctl -b -p err --no-pager | tail -5
Sep 03 03:05:11 ubuntu-vm kernel: ACPI Error: No handler for Region [SYSI]
Sep 03 03:05:14 ubuntu-vm systemd[1]: Failed to start Raise network interfaces.

$ journalctl --disk-usage
Archived and active journals take up 112.0M in the file system.
```

Deliberately break a service and read the journal — the standard debugging loop:

```console
$ sudo systemctl start nginx
Job for nginx.service failed because the control process exited with error code.
See "systemctl status nginx.service" and "journalctl -xeu nginx.service" for details.

$ journalctl -xeu nginx.service --no-pager | tail -6
Sep 03 03:20:02 ubuntu-vm nginx[5001]: nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
Sep 03 03:20:02 ubuntu-vm nginx[5001]: nginx: configuration file /etc/nginx/nginx.conf test failed
Sep 03 03:20:02 ubuntu-vm systemd[1]: nginx.service: Control process exited, code=exited, status=1/FAILURE
Sep 03 03:20:02 ubuntu-vm systemd[1]: nginx.service: Failed with result 'exit-code'.
Sep 03 03:20:02 ubuntu-vm systemd[1]: Failed to start A high performance web server and a reverse proxy server.
```

> As above, these are the expected Ubuntu outputs — `journalctl` is a systemd tool and
> does not exist on macOS. Reproduce in an Ubuntu VM/WSL and screenshot.
> Note that Docker containers usually have **no systemd**, so `journalctl` will not work
> inside `docker run ubuntu`; use a real VM, WSL2, or a cloud instance.

### 3.4 Why journalctl over `/var/log/syslog`

| | `journalctl` | `tail /var/log/syslog` |
|---|---|---|
| Filter by service | `-u nginx` — exact, uses metadata | `grep nginx` — string match, misses/over-matches |
| Filter by boot | `-b -1` | not possible |
| Filter by severity | `-p err` | not possible |
| Structured fields | Yes (`-o json`) | No, plain text |
| Rotation | Automatic, size/time capped | needs `logrotate` |
| Human-readable file | No, binary | Yes |

### 3.5 Interview answers

**Q: A service failed to start — what's your first command?**
`journalctl -xeu <service> --no-pager` — `-u` scopes to the unit, `-e` jumps to the end,
`-x` adds catalog explanations.

**Q: Journal is empty after reboot. Why?** `Storage=volatile` — no `/var/log/journal`
directory, so logs live in `/run` and are lost. Create the directory to make it persistent.

**Q: Journal ate the disk. Fix?** `journalctl --disk-usage`, then
`sudo journalctl --vacuum-size=200M`, and set `SystemMaxUse=200M` in
`/etc/systemd/journald.conf` so it stays capped.

---

## Sub-task 4 — Linux Command Cheat Sheet

### 4.1 Navigation & file listing

| Command | Purpose |
|---|---|
| `pwd` | Print working directory |
| `ls -lah` | Long list, all files, human-readable sizes |
| `ls -lt` / `ls -ltr` | Sort by mtime / oldest last — find the newest log |
| `ls -li` | Show inode numbers (used in the link task) |
| `cd -` | Jump back to the previous directory |
| `tree -L 2` | Directory tree, 2 levels deep |

### 4.2 Files & directories

| Command | Purpose |
|---|---|
| `touch file` | Create an empty file / update its timestamp |
| `mkdir -p a/b/c` | Create nested directories, no error if they exist |
| `cp -r src dst` | Copy recursively |
| `cp -a src dst` | Archive copy — preserves perms, times, symlinks |
| `mv old new` | Move or rename |
| `rm -rf dir` | Delete recursively and forcibly — **irreversible** |
| `ln -s tgt lnk` | Soft link |
| `ln tgt lnk` | Hard link |
| `rsync -avz src/ user@host:/dst/` | Efficient, resumable copy over SSH |

### 4.3 Viewing & editing

| Command | Purpose |
|---|---|
| `cat file` | Dump whole file |
| `less file` | Page through (`/` search, `q` quit, `G` end) |
| `head -n 20 file` / `tail -n 20 file` | First / last 20 lines |
| `tail -f app.log` | Follow a growing log |
| `tail -f app.log \| grep ERROR` | Live-filter a log |
| `nano` / `vim` | Terminal editors |
| `wc -l file` | Count lines |

### 4.4 Search

| Command | Purpose |
|---|---|
| `grep -i "text" file` | Case-insensitive search |
| `grep -rn "TODO" .` | Recursive, with line numbers |
| `grep -v "DEBUG" app.log` | Invert — everything except matches |
| `grep -E "err\|warn" app.log` | Extended regex, multiple patterns |
| `find . -name "*.log"` | Find by name |
| `find /var -size +100M` | Find large files |
| `find . -mtime -1` | Modified in the last 24 h |
| `find . -type f -exec chmod 644 {} \;` | Run a command per match |
| `which docker` / `whereis nginx` | Locate a binary |

### 4.5 Permissions & ownership

| Command | Purpose |
|---|---|
| `chmod 755 script.sh` | rwx owner, r-x group/others |
| `chmod +x script.sh` | Make executable |
| `chown user:group file` | Change owner and group |
| `chown -R www-data:www-data /var/www` | Recursive |
| `umask` | Default permission mask for new files |
| `sudo -i` | Interactive root shell |

Numeric refresher: `r=4 w=2 x=1` → `7=rwx`, `6=rw-`, `5=r-x`, `4=r--`.

### 4.6 Processes

| Command | Purpose |
|---|---|
| `ps aux` | Every process, BSD style |
| `ps -ef` | Every process, System-V style |
| `ps aux --sort=-%mem \| head` | Top memory consumers |
| `top` / `htop` | Live process monitor |
| `kill -15 PID` | SIGTERM — polite shutdown |
| `kill -9 PID` | SIGKILL — force, no cleanup |
| `pkill -f "python app.py"` | Kill by command-line pattern |
| `pgrep -a nginx` | List matching PIDs and commands |
| `jobs` / `fg` / `bg` / `Ctrl+Z` | Job control |
| `nohup ./run.sh &` | Keep running after logout |

### 4.7 Disk & memory

| Command | Purpose |
|---|---|
| `df -h` | Free space per filesystem |
| `df -i` | **Inode** usage — "disk full" with free space means inodes ran out |
| `du -sh *` | Size of each item in the current directory |
| `du -sh * \| sort -rh \| head` | Biggest offenders first |
| `free -h` | RAM and swap |
| `lsblk` | Block devices and mount points |
| `mount` / `umount` | Attach / detach filesystems |

### 4.8 Networking (expanded in Task 3)

| Command | Purpose |
|---|---|
| `ip a` | Interfaces and IP addresses |
| `ip r` | Routing table |
| `ping -c 4 8.8.8.8` | Reachability + latency |
| `curl -I https://site` | Fetch headers only |
| `ss -tulnp` | Listening TCP/UDP sockets with PIDs |
| `netstat -tulnp` | Legacy equivalent of `ss` |
| `dig example.com` / `nslookup` | DNS lookup |
| `traceroute host` | Path to a host |
| `scp file user@host:/path` | Copy over SSH |

### 4.9 Users & groups

| Command | Purpose |
|---|---|
| `whoami` / `id` | Current user, UID/GID and groups |
| `adduser bob` | Create a user (Ubuntu, interactive) |
| `useradd -m -s /bin/bash bob` | Create a user (scripted) |
| `passwd bob` | Set a password |
| `usermod -aG docker bob` | **Append** to a group |
| `groups bob` | Group memberships |
| `su - bob` | Switch user |
| `deluser --remove-home bob` | Delete user and home |

### 4.10 Services (systemd)

| Command | Purpose |
|---|---|
| `systemctl status nginx` | State + recent log lines |
| `systemctl start/stop/restart nginx` | Control a service |
| `systemctl reload nginx` | Re-read config without dropping connections |
| `systemctl enable --now nginx` | Start now **and** at boot |
| `systemctl list-units --failed` | Everything that is broken |
| `journalctl -u nginx -f` | Follow its logs |

### 4.11 Archives & packages

| Command | Purpose |
|---|---|
| `tar -czvf a.tar.gz dir/` | Create a gzipped tarball |
| `tar -xzvf a.tar.gz` | Extract |
| `tar -tzvf a.tar.gz` | List contents without extracting |
| `zip -r a.zip dir/` / `unzip a.zip` | Zip archives |
| `apt update && apt upgrade` | Refresh & upgrade (Debian/Ubuntu) |
| `apt install -y nginx` | Install a package |
| `dpkg -l \| grep nginx` | Query installed packages |
| `yum` / `dnf install` | RHEL/Fedora equivalent |

### 4.12 Pipes, redirection & text processing

| Command | Purpose |
|---|---|
| `cmd > file` | Redirect stdout, **overwrite** |
| `cmd >> file` | Redirect stdout, **append** |
| `cmd 2> err.log` | Redirect stderr |
| `cmd > out.log 2>&1` | Both streams to one file |
| `cmd &> out.log` | Same thing, bash shorthand |
| `cmd < input.txt` | Feed stdin from a file |
| `a \| b` | Pipe a's stdout into b's stdin |
| `cmd \| tee file` | Print **and** save |
| `sort file \| uniq -c \| sort -rn` | Frequency count, most common first |
| `cut -d: -f1 /etc/passwd` | Extract a field |
| `awk '{print $1, $9}' access.log` | Column extraction / arithmetic |
| `sed 's/old/new/g' file` | Stream find-and-replace |
| `xargs` | Turn stdin into command arguments |

### 4.13 System info & misc

| Command | Purpose |
|---|---|
| `uname -a` | Kernel and architecture |
| `hostnamectl` | Hostname, OS, kernel, virtualisation |
| `cat /etc/os-release` | Distro name and version |
| `uptime` | Uptime and load average |
| `date` | Current date and time |
| `history \| grep docker` | Search command history |
| `man ls` / `ls --help` | Documentation |
| `alias ll='ls -lah'` | Shorthand |
| `Ctrl+R` | Reverse-search history |

### 4.14 A one-line summary of the ones that matter most in DevOps

```bash
ls -lah        # look around
cd / pwd       # move around
grep -rn       # find text
find           # find files
tail -f        # watch a log
ps aux         # what is running
kill -9        # stop it
df -h / du -sh # where did the disk go
chmod / chown  # fix permissions
systemctl      # control services
journalctl -u  # read service logs
ss -tulnp      # what is listening on which port
```
