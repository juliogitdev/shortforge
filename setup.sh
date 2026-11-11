#!/usr/bin/env bash
# shortforge setup: installs three.js for the 3D world and checks Python/ffmpeg/Playwright.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/world3d"
[ -d node_modules/three ] || { npm init -y >/dev/null 2>&1; npm i three@0.160.0 --silent; }
command -v ffmpeg >/dev/null || { echo "ffmpeg missing: install it (apt-get install -y ffmpeg / brew install ffmpeg)"; exit 1; }
python3 -c "import PIL, numpy" 2>/dev/null || pip install pillow numpy
node -e "require('playwright')" 2>/dev/null || { npm i playwright --silent && npx playwright install chromium; }
echo "shortforge ready"
