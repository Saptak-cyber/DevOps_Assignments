# Task 4 — Git / GitHub

Two sub-tasks: understanding `git commit -a -m` vs `git commit -m`, and doing a
cherry-pick from a feature branch back into `main`.

Files in this folder:

| File | Purpose |
|------|---------|
| `git-cherry-pick-demo.sh` | Reproduces the entire homework in a throwaway repo, printing every command |
| `README.md` | This document — commands, real output, explanation |

Reproduce everything:

```bash
chmod +x git-cherry-pick-demo.sh
./git-cherry-pick-demo.sh
```

---

# Task 1 — `git commit -m` vs `git commit -a -m`

## 1.1 The three areas

Git moves a change through three places:

```
 Working Directory  --git add-->  Staging Area (Index)  --git commit-->  Repository
   (your edits)                    (what will go in)                     (history)
```

* `git commit -m "msg"` commits **only what is in the staging area**.
* `git commit -a -m "msg"` runs an implicit `git add` on **every already-tracked file
  that was modified or deleted**, then commits — a shortcut for `git add -u && git commit`.

## 1.2 The one difference that matters

**`-a` does not stage untracked (brand-new) files.** It only touches files Git already
knows about. A new file must always be `git add`-ed at least once.

| Situation | `git commit -m` | `git commit -a -m` |
|---|---|---|
| New, untracked file | Not committed | **Not committed** |
| Modified tracked file, not staged | Not committed | ✅ Committed |
| Modified tracked file, already staged | ✅ Committed | ✅ Committed |
| Deleted tracked file, not staged | Not recorded | ✅ Deletion recorded |
| Partially staged file (`git add -p`) | Only the staged hunks | ⚠️ The **whole** file — the partial staging is lost |

## 1.3 Test — real output

### Step 1a — `-a` on an untracked file does nothing

```console
$ echo "line 1" > file1.txt

$ git status --short
?? file1.txt

$ git commit -a -m "attempt with -a on an untracked file"
On branch main

Initial commit

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	file1.txt

nothing added to commit but untracked files present (use "git add" to track)
```

`??` in `git status --short` means untracked. `-a` skipped it and nothing was committed.

### Step 1b — untracked files need `git add`

```console
$ git add file1.txt

$ git commit -m "Commit 1: add file1.txt"
[main (root-commit) f4e8aab] Commit 1: add file1.txt
 1 file changed, 1 insertion(+)
 create mode 100644 file1.txt
```

### Step 1c — plain `-m` on an unstaged modification also does nothing

```console
$ echo "line 2" >> file1.txt

$ git status --short
 M file1.txt

$ git commit -m "try to commit without staging"
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   file1.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

Note the two-column status: ` M` means **modified in the working tree but not staged**
(space in the index column, `M` in the worktree column). Git's own hint at the end names
both fixes.

### Step 1d — `-a` commits it in one step

```console
$ git commit -a -m "Commit 2: append line 2 to file1.txt"
[main d76d167] Commit 2: append line 2 to file1.txt
 1 file changed, 1 insertion(+)

$ git status --short
(clean — no output)
```

## 1.4 What I observed

1. `-a` **only** helps with files Git already tracks. For a new file the two commands
   behave identically — both refuse.
2. For a modified tracked file, `-a` saves the `git add` step. `git commit -a -m` is
   exactly `git add -u && git commit -m`.
3. `-a` also records **deletions** of tracked files, which `git add .` historically did
   not (`git add -A` does).
4. The risk of `-a`: it sweeps up *everything* modified, including debug prints or a
   stray config change you did not mean to commit. It also destroys deliberate partial
   staging done with `git add -p`.

**Habit:** use `git status` → `git add <specific files>` → `git commit -m` for real work,
and reserve `git commit -a -m` for small, single-purpose edits where you already know
nothing else changed.

Related shortcuts:

```bash
git commit -am "msg"      # -a and -m combined
git commit --amend        # rewrite the last commit (never after pushing to a shared branch)
git add -u                # stage modifications + deletions of tracked files (what -a does)
git add -A                # stage everything, including new files
git add -p                # stage hunk by hunk, interactively
```

---

# Task 2 — Git Cherry-Pick

## 2.1 What cherry-pick is

`git cherry-pick <commit>` takes the **diff introduced by one commit** and replays it on
top of your current branch as a **new commit with a new hash**.

* `merge` brings over an entire branch and its history.
* `rebase` moves a whole series of commits onto a new base.
* `cherry-pick` copies **exactly one** (or a chosen few) — the surgical option.

Typical real use: a hotfix was made on a release branch and you need only that one fix on
`main`, without dragging in the half-finished features sitting next to it.

## 2.2 Setup — 4 commits on `main`

```console
$ git log --oneline
9add905 Commit 4: add setup instructions to README
e6b9b8e Commit 3: add README.md
d76d167 Commit 2: append line 2 to file1.txt
f4e8aab Commit 1: add file1.txt
```

## 2.3 New branch with 3 commits

```console
$ git checkout -b feature-branch
Switched to a new branch 'feature-branch'

$ git log --oneline
6b9bc50 Feature commit 3: add featureC.js
7c7dd72 Feature commit 2: URGENT bugfix for login (this one goes to main)
a7f273f Feature commit 1: add featureA.js
9add905 Commit 4: add setup instructions to README
e6b9b8e Commit 3: add README.md
d76d167 Commit 2: append line 2 to file1.txt
f4e8aab Commit 1: add file1.txt

$ git log --oneline --graph --all --decorate
* 6b9bc50 (HEAD -> feature-branch) Feature commit 3: add featureC.js
* 7c7dd72 Feature commit 2: URGENT bugfix for login (this one goes to main)
* a7f273f Feature commit 1: add featureA.js
* 9add905 (main) Commit 4: add setup instructions to README
* e6b9b8e Commit 3: add README.md
* d76d167 Commit 2: append line 2 to file1.txt
* f4e8aab Commit 1: add file1.txt
```

`HEAD -> feature-branch` shows where I am; `(main)` shows main is still 3 commits behind.

## 2.4 Identify the commit to pick

```console
$ git log --oneline --grep="URGENT"
7c7dd72 Feature commit 2: URGENT bugfix for login (this one goes to main)

$ git show --stat 7c7dd72
commit 7c7dd72496f585f41468b74b61806e80b789aeed
Author: Saptak Banerjee <saptak.banerjee@scalerailabs.com>
Date:   Thu Sep 3 03:07:53 2026 +0530

    Feature commit 2: URGENT bugfix for login (this one goes to main)

 bugfix.py | 1 +
 1 file changed, 1 insertion(+)
```

Ways to find the right hash:

```bash
git log --oneline                    # short hashes + subjects
git log --oneline --grep="bugfix"    # search commit messages
git log --oneline -- path/to/file    # commits that touched one file
git log -p -1 <hash>                 # the full diff of one commit
git show --stat <hash>               # which files it changed
```

## 2.5 Switch to `main` — the change is not there yet

```console
$ git checkout main
Switched to branch 'main'

$ ls
README.md
file1.txt
```

`bugfix.py` is absent, as expected.

## 2.6 Cherry-pick

```console
$ git cherry-pick 7c7dd72
[main 658c21c] Feature commit 2: URGENT bugfix for login (this one goes to main)
 Date: Thu Sep 3 03:07:53 2026 +0530
 1 file changed, 1 insertion(+)
 create mode 100644 bugfix.py
```

Note the hash: **`658c21c`, not `7c7dd72`**. Git created a *new* commit object because
the parent is different. It preserved the original **author date** (shown on its own
`Date:` line) while the committer date is now.

## 2.7 Verify

```console
$ ls
README.md
bugfix.py
file1.txt

$ cat bugfix.py
def bugfix(): return 'fixed the login bug'

$ git log --oneline
658c21c Feature commit 2: URGENT bugfix for login (this one goes to main)
9add905 Commit 4: add setup instructions to README
e6b9b8e Commit 3: add README.md
d76d167 Commit 2: append line 2 to file1.txt
f4e8aab Commit 1: add file1.txt

$ git log --oneline --graph --all --decorate
* 658c21c (HEAD -> main) Feature commit 2: URGENT bugfix for login (this one goes to main)
| * 6b9bc50 (feature-branch) Feature commit 3: add featureC.js
| * 7c7dd72 Feature commit 2: URGENT bugfix for login (this one goes to main)
| * a7f273f Feature commit 1: add featureA.js
|/
* 9add905 Commit 4: add setup instructions to README
* e6b9b8e Commit 3: add README.md
* d76d167 Commit 2: append line 2 to file1.txt
* f4e8aab Commit 1: add file1.txt

$ git diff --stat main feature-branch
 featureA.js | 1 +
 featureC.js | 1 +
 2 files changed, 2 insertions(+)
```

**Verification result — three things confirm the cherry-pick worked:**

1. `bugfix.py` now exists on `main` with the correct content.
2. The graph forked at `9add905`: `main` has the picked commit `658c21c`, while
   `feature-branch` still carries the original `7c7dd72`. The **same change now exists as
   two distinct commit objects** — that is exactly what cherry-pick means.
3. `git diff --stat main feature-branch` lists only `featureA.js` and `featureC.js`.
   `bugfix.py` is *not* in the diff, proving only the selected commit came across and the
   other two feature commits stayed behind.

## 2.8 Cherry-pick options

```bash
git cherry-pick <hash>              # one commit
git cherry-pick <h1> <h2> <h3>      # several, applied in the order given
git cherry-pick A..B                # a range, EXCLUDING A
git cherry-pick A^..B               # a range, INCLUDING A
git cherry-pick -n <hash>           # apply to the working tree, do NOT commit yet
git cherry-pick -e <hash>           # edit the commit message
git cherry-pick -x <hash>           # append "(cherry picked from commit <hash>)" — do
                                    #   this when picking onto a public branch, so the
                                    #   origin of the change is traceable
git cherry-pick --continue          # after resolving a conflict
git cherry-pick --abort             # give up, restore the branch
git cherry-pick --skip              # skip this commit, continue the sequence
```

### Handling a conflict

```console
$ git cherry-pick 7c7dd72
Auto-merging app.py
CONFLICT (content): Merge conflict in app.py
error: could not apply 7c7dd72... Feature commit 2
hint: After resolving the conflicts, mark them with
hint: "git add/rm <pathspec>", then run "git cherry-pick --continue".

$ git status
$ vim app.py            # remove the <<<<<<< ======= >>>>>>> markers
$ git add app.py
$ git cherry-pick --continue
```

## 2.9 Interview answers

**Q: cherry-pick vs merge vs rebase?**
`merge` joins two histories with a merge commit and keeps both intact. `rebase` replays a
series of commits onto a new base, rewriting their hashes. `cherry-pick` copies one
specific commit's diff onto the current branch as a new commit. Use cherry-pick when you
want *one* change and not the branch it lives on.

**Q: Why does the hash change?**
A commit hash is a SHA of the tree, the parent(s), the author, the committer and the
message. The parent is different on the target branch, so the hash must differ, even
though the diff is identical.

**Q: Any downside?**
It creates duplicate commits. If the feature branch is later merged into `main`, the same
change appears twice in the history. Git usually detects the duplicate patch and applies
it cleanly, but not always — use `-x` so the duplication is at least documented.

**Q: Can you undo a cherry-pick?**
Before committing: `git cherry-pick --abort`. After: `git revert <new-hash>` on a shared
branch, or `git reset --hard HEAD~1` if the commit has not been pushed anywhere.

---

## Submission

```bash
git init
git add Task4-Git-GitHub/
git commit -m "Add Git homework: commit -a vs -m, and cherry-pick demo with output"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo>.git
git push -u origin main
```

Every command output above is real terminal output from `git-cherry-pick-demo.sh`.
Run the script yourself to regenerate it — the short hashes will differ, since they depend
on your name, email and timestamps.
