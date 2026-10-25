#!/bin/bash
# Render every shot (resumable: existing frames are skipped).
cd "$(dirname "$0")/.."
SHOTS="${@:-A1 B1 B2 B3 C1 C2 C3 C4 D1 D2 D3 D4 D5a D5b E1 E2 E3 F1 F2}"
mkdir -p work/logs
for s in $SHOTS; do
  t0=$(date +%s)
  xvfb-run -a -s "-screen 0 1280x1024x24" blender -b --python scripts/blender_shots.py -- $s > work/logs/$s.log 2>&1
  echo "$s done $(( $(date +%s) - t0 ))s frames=$(ls assets/frames/shots/$s | wc -l)" >> work/logs/progress.txt
done
echo ALL_DONE >> work/logs/progress.txt
