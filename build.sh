#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

VERSION=0.3.19
while getopts "v:" option; do
  case "$option" in
    v) VERSION=$OPTARG ;;
    *) exit 1 ;;
  esac
done
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Expected version: X.Y.Z' >&2; exit 1; }
"${PYTHON:-python2}" -c 'import sys; assert sys.version_info[:2] == (2, 7), "Python 2.7 required"'

rm -rf .build
mkdir -p .build dist
BUILD_DIR="$PWD/.build"
trap 'rm -rf "$BUILD_DIR"' EXIT
cp -R res .build/res
find .build -name '*.pyc' -delete
find .build -name __pycache__ -type d -prune -exec rm -rf {} +

./as3/build.sh
VERSION="$VERSION" perl -pi -e 's/\{\{VERSION\}\}/$ENV{VERSION}/g' \
  .build/res/scripts/client/gui/mods/mod_wotstat_spotting_points.py
VERSION="$VERSION" perl -pe 's/\{\{VERSION\}\}/$ENV{VERSION}/g' meta.xml > .build/meta.xml

cd .build
"${PYTHON:-python2}" -m compileall -q -d res res
PACKAGE="wotstat.spotting-points_$VERSION"
zip -q -0 -X "$PACKAGE.wotmod" meta.xml
zip -q -r -0 -X "$PACKAGE.wotmod" res -i '*.pyc' '*.swf' '*.png'
cp "$PACKAGE.wotmod" "../dist/$PACKAGE.wotmod"
cp "$PACKAGE.wotmod" "../dist/$PACKAGE.mtmod"
echo "Built dist/$PACKAGE.{wotmod,mtmod}"
