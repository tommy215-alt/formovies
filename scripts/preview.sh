#!/bin/bash
# preview.sh SHOT... : render 3 low-sample frames per shot into work/prev
cd "$(dirname "$0")/.."
for s in "$@"; do
  t0=$(date +%s)
  xvfb-run -a -s "-screen 0 1280x1024x24" blender -b --python scripts/blender_shots.py -- $s --preview > work/prev/$s.log 2>&1
  grep -E "Error|Traceback|line [0-9]+" work/prev/$s.log | head -6
  echo "$s $(( $(date +%s) - t0 ))s"
done
