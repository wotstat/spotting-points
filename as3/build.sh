#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p ../.build/res/gui/flash
for target in SettingsWindow:Settings MarkerOverlay:Markers; do
  "${MXMLC:-mxmlc}" -load-config+=build-config.xml \
    -output="../.build/res/gui/flash/wotstatSpottingPoints${target#*:}.swf" \
    "src/wotstat/spottingpoints/${target%:*}.as"
done
