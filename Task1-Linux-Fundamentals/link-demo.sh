#!/bin/bash
# link-demo.sh - Demonstrates the difference between soft (symbolic) links and hard links.
# Portable: uses only ls / ln / cat / rm, so it behaves the same on Linux and macOS.

set -u

DEMO_DIR="${1:-./link-demo}"

echo "### 1. Setting up a clean demo directory: $DEMO_DIR"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR" || exit 1

echo "Hello from the original file" > original.txt
echo

echo "### 2. Creating a SOFT link  ->  ln -s original.txt softlink.txt"
ln -s original.txt softlink.txt

echo "### 3. Creating a HARD link  ->  ln original.txt hardlink.txt"
ln original.txt hardlink.txt
echo

echo "### 4. Inspecting inodes and link counts (ls -li)"
echo "    Column 1 = inode number, column 3 = hard-link count"
ls -li
echo

echo "### 5. Reading the file through both links"
echo "--- cat softlink.txt ---"; cat softlink.txt
echo "--- cat hardlink.txt ---"; cat hardlink.txt
echo

echo "### 6. Writing through the hard link is visible in the original"
echo "Line added via hardlink" >> hardlink.txt
echo "--- cat original.txt ---"; cat original.txt
echo

echo "### 7. Deleting the ORIGINAL file:  rm original.txt"
rm original.txt
ls -li
echo

echo "### 8. Soft link is now broken (dangling)"
cat softlink.txt 2>&1
echo

echo "### 9. Hard link still holds the data (inode has another name)"
cat hardlink.txt
echo

echo "### 10. Removing a link removes only the name, never the other names"
rm -f softlink.txt
ls -li
