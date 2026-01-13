#!/bin/bash
set -e
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y zip gettext binutils
else
    echo "Warning: apt-get not found. Ensure 'zip' and 'gettext' are installed."
fi
ADDON_NAME="smartCaptchaSolver"
OUTPUT_FILE="${ADDON_NAME}.nvda-addon"
rm -f "$OUTPUT_FILE"
mkdir -p build_tmp
rm -rf globalPlugins/captchaSolver/lib
cp manifest.ini build_tmp/
cp -r globalPlugins build_tmp/
cp -r docs build_tmp/doc
cd build_tmp
zip -r "../$OUTPUT_FILE" *
cd ..
rm -rf build_tmp
echo "Build complete: $OUTPUT_FILE"
