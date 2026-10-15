#!/usr/bin/env bash
# Build MihomoTray macOS 1.0.5 .app — separate Intel (x86_64) and Apple Silicon (arm64) apps.
# Usage:
#   ./build.sh           # build both into dist/arm64/ and dist/x86_64/
#   ./build.sh arm64     # Apple Silicon only
#   ./build.sh x86_64    # Intel only
#   ./build.sh native    # host arch only (uname -m)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# ShortVersion = 发版号 x.y.z；BundleVersion = x.y.z.N（本地只加 N）。CI 读 ShortVersion。
plist_str() {
  local key="$1"
  if /usr/libexec/PlistBuddy -c "Print :$key" Resources/Info.plist 2>/dev/null; then
    return 0
  fi
  python3 -c '
import sys
from pathlib import Path
key = sys.argv[1]
text = Path("Resources/Info.plist").read_text()
needle = "<key>%s</key>" % key
i = text.find(needle)
if i < 0:
    raise SystemExit(1)
rest = text[i + len(needle):]
a = rest.find("<string>")
b = rest.find("</string>", a)
print(rest[a + 8:b].strip())
' "$key"
}
VERSION="$(plist_str CFBundleShortVersionString)"
BUILD="$(plist_str CFBundleVersion)"

APP_NAME="MihomoTray"
DIST="$ROOT/dist"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script builds a macOS .app; run it on a Mac with Xcode/swiftc."
  echo "Sources and icons are ready under: $ROOT"
  exit 1
fi

command -v swiftc >/dev/null || { echo "swiftc not found; install Xcode CLT"; exit 1; }

TARGET="${1:-both}"
NATIVE="$(uname -m)"
case "$TARGET" in
  both|"") ARCHS="arm64 x86_64" ;;
  native) ARCHS="$NATIVE" ;;
  arm64|x86_64) ARCHS="$TARGET" ;;
  *) echo "usage: $0 [both|native|arm64|x86_64]"; exit 1 ;;
esac

rm -rf "$DIST"
mkdir -p "$DIST"

build_one() {
  local ARCH="$1"
  local OUT="$DIST/$ARCH"
  local APP="$OUT/$APP_NAME.app"
  local MACOS_DIR="$APP/Contents/MacOS"
  local RES_DIR="$APP/Contents/Resources"
  mkdir -p "$MACOS_DIR" "$RES_DIR" "$OUT/Data/Icons"

  cp Assets/tray_rule.png Assets/tray_rule@2x.png \
     Assets/tray_global.png Assets/tray_global@2x.png \
     Assets/tray_direct.png Assets/tray_direct@2x.png \
     Assets/tray_offline.png Assets/tray_offline@2x.png \
     "$RES_DIR/"
  cp Assets/tray_*-22*.png "$RES_DIR/" 2>/dev/null || true
  cp Resources/Info.plist "$APP/Contents/Info.plist"
  cp Resources/config.ini "$OUT/Data/config.ini"
  cp Assets/tray_rule.png Assets/tray_rule@2x.png \
     Assets/tray_global.png Assets/tray_global@2x.png \
     Assets/tray_direct.png Assets/tray_direct@2x.png \
     Assets/tray_offline.png Assets/tray_offline@2x.png \
     "$OUT/Data/Icons/"

  swiftc -O \
    -target "${ARCH}-apple-macosx12.0" \
    -sdk "$(xcrun --show-sdk-path)" \
    -framework AppKit -framework Foundation \
    -o "$MACOS_DIR/$APP_NAME" \
    Sources/MihomoTray/*.swift
  chmod +x "$MACOS_DIR/$APP_NAME"
  cp README.md README_en.md "$OUT/" 2>/dev/null || true
  echo "Built $ARCH -> $APP"
  lipo -archs "$MACOS_DIR/$APP_NAME" || true
}

for a in $ARCHS; do
  build_one "$a"
done

echo "OK. Outputs under $DIST/{arm64,x86_64}/"
echo "Version $VERSION (CFBundleVersion ${BUILD:-?})"
