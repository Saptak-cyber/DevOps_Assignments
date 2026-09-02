#!/bin/bash
#===============================================================================
# git-cherry-pick-demo.sh — reproduces the whole Git homework end to end in a
# throwaway repository, printing every command and its output.
#
# Covers:
#   Task 1: git commit -m  vs  git commit -a -m
#   Task 2: 4 commits on main, a branch with 3 commits, cherry-pick one of them
#           back into main, and verify.
#
# Usage:  ./git-cherry-pick-demo.sh [target-directory]
#===============================================================================

DEMO_DIR="${1:-./git-demo}"

hdr() { echo; echo "==============================================================="; echo " $*"; echo "==============================================================="; }
cmd() { echo; echo "\$ $*"; eval "$@"; }

rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR" || exit 1

git init -q -b main
git config user.name  "Saptak Banerjee"
git config user.email "saptak.banerjee@example.com"

#===============================================================================
hdr "TASK 1 — git commit -m   vs   git commit -a -m"
#===============================================================================

echo
echo "--- 1a: a brand-new (UNTRACKED) file — -a will NOT pick it up ---"
echo "line 1" > file1.txt
cmd "git status --short"
cmd "git commit -a -m 'attempt with -a on an untracked file'"

echo
echo "--- 1b: untracked files must be git add-ed first ---"
cmd "git add file1.txt"
cmd "git commit -m 'Commit 1: add file1.txt'"

echo
echo "--- 1c: modify a TRACKED file, then plain 'git commit -m' ---"
echo "line 2" >> file1.txt
cmd "git status --short"
cmd "git commit -m 'try to commit without staging'"

echo
echo "--- 1d: same change with -a — it stages tracked modifications for you ---"
cmd "git commit -a -m 'Commit 2: append line 2 to file1.txt'"
cmd "git status --short"

#===============================================================================
hdr "TASK 2 — CHERRY-PICK"
#===============================================================================

echo
echo "--- 2a: two more commits on main (4 total) ---"
echo "# DevOps Assignment" > README.md
git add README.md && git commit -q -m "Commit 3: add README.md"
echo "Setup instructions" >> README.md
git commit -q -a -m "Commit 4: add setup instructions to README"
cmd "git log --oneline"

echo
echo "--- 2b: new branch with 3 commits ---"
cmd "git checkout -b feature-branch"
echo "console.log('feature A');" > featureA.js
git add featureA.js && git commit -q -m "Feature commit 1: add featureA.js"
echo "def bugfix(): return 'fixed the login bug'" > bugfix.py
git add bugfix.py && git commit -q -m "Feature commit 2: URGENT bugfix for login (this one goes to main)"
echo "console.log('feature C');" > featureC.js
git add featureC.js && git commit -q -m "Feature commit 3: add featureC.js"
cmd "git log --oneline"
cmd "git log --oneline --graph --all --decorate"

echo
echo "--- 2c: identify the exact commit to pick ---"
cmd "git log --oneline --grep=URGENT"
PICK=$(git log --format=%h --grep=URGENT -1)
echo "Selected commit: $PICK"
cmd "git show --stat $PICK"

echo
echo "--- 2d: back to main — bugfix.py is not here yet ---"
cmd "git checkout main"
cmd "ls"

echo
echo "--- 2e: cherry-pick that one commit onto main ---"
cmd "git cherry-pick $PICK"

echo
echo "--- 2f: VERIFY ---"
cmd "ls"
cmd "cat bugfix.py"
cmd "git log --oneline"
cmd "git log --oneline --graph --all --decorate"
cmd "git diff --stat main feature-branch"

echo
echo "Done. featureA.js and featureC.js stayed on feature-branch;"
echo "only the selected bugfix commit was copied to main, with a NEW hash."
