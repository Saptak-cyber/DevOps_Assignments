#!/bin/bash
# Build step from the instructor's 10-final-cicd-pipeline/build.sh, extended to
# package the whole app/ package (calculator + HTTP server) and record which
# commit / run produced the build.
set -euo pipefail
echo "================================="
echo "Starting Application Build"
echo "================================="
rm -rf build
mkdir -p build/app
cp app/__init__.py app/calculator.py app/server.py build/app/
python3 -m compileall -q build/app
cat > build/build-info.txt <<INFO
Application: Session 16 Calculator
Build Status: SUCCESS
Build Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Commit: ${GITHUB_SHA:-local}
Workflow Run: ${GITHUB_RUN_ID:-local} (attempt ${GITHUB_RUN_ATTEMPT:-0})
Python: $(python3 --version 2>&1)
INFO
echo ""
echo "Build files:"
find build -type f -not -path '*/__pycache__/*' | sort
echo ""
cat build/build-info.txt
echo ""
echo "Build completed successfully."
