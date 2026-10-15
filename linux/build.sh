#!/bin/sh
# 打包 Linux：./build.sh [qt|gtk|all]
#   qt  → dist/MihomoTray_linux_qt_<ver>_x86_64.AppImage（精简 Qt）
#   gtk → dist/MihomoTray_linux_<ver>.deb   (Package: mihomotray)
#         dist/MihomoTray_linux_<ver>.rpm   (Name: mihomotray)
#         dist/MihomoTray_linux_gtk_<ver>.tar.gz
#   all → 以上全部（默认）
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"
VERSION=$(sed -n 's/^__version__ = "\([^"]*\)".*/\1/p' mihomotray/__init__.py)
BUILD=$(sed -n 's/^__build__ = \([0-9][0-9]*\).*/\1/p' mihomotray/__init__.py)
BUILD=${BUILD:-0}
# 发版/CI：产物用 x.y.z；仅本地且 __build__>0 时文件名带 .N（__version__/UA 仍为 x.y.z）
if [ "$BUILD" -gt 0 ] && [ -z "${CI:-}${GITHUB_ACTIONS:-}" ]; then
  ARTIFACT_VER="${VERSION}.${BUILD}"
else
  ARTIFACT_VER="$VERSION"
fi
TARGET="${1:-all}"
case "$TARGET" in qt|gtk|all) ;; *) echo "usage: $0 [qt|gtk|all]" >&2; exit 1 ;; esac
PYVER="${PYVER:-3.12}"
[ -f mihomotray/icons/tray_rule_16.png ] || python3 tools/make_icons.py
mkdir -p dist

build_qt() {
  echo "==> building Qt AppImage (slim)"
  if ! python3 -m python_appimage --help >/dev/null 2>&1; then
    if [ -n "${VIRTUAL_ENV:-}" ]; then
      python3 -m pip install -q python-appimage
    else
      python3 -m pip install --user -q python-appimage \
        || python3 -m pip install -q --break-system-packages python-appimage
    fi
  fi
  WORK=$(mktemp -d)
  cp appimage/mihomotray.desktop appimage/mihomotray.png "$WORK/"
  # Force Qt frontend inside AppImage
  printf '%s\n' 'export MIHOMOTRAY_FRONTEND=qt' '{{ python-executable }} -s -m mihomotray "$@"' > "$WORK/entrypoint.sh"
  printf '%s\n' "$ROOT" > "$WORK/requirements.txt"
  printf '%s\n' "PySide6-Essentials>=6.5" >> "$WORK/requirements.txt"
  ( cd dist && python3 -m python_appimage build app -p "$PYVER" "$WORK" )
  FAT=$(ls -t dist/*.AppImage | head -n 1)
  echo "fat AppImage: $FAT ($(du -h "$FAT" | cut -f1))"

  EXTRACT=$(mktemp -d)
  (
    cd "$EXTRACT"
    APPIMAGE_EXTRACT_AND_RUN=1 "$ROOT/$FAT" --appimage-extract >/dev/null 2>&1 \
      || APPIMAGE_EXTRACT_AND_RUN=1 "$FAT" --appimage-extract >/dev/null
  )
  # locate squashfs-root
  SQ=$(find "$EXTRACT" -maxdepth 2 -type d -name squashfs-root | head -n 1)
  python3 "$ROOT/tools/slim_appimage.py" "$SQ"

  TOOL="$ROOT/tools/appimagetool-x86_64.AppImage"
  if [ ! -x "$TOOL" ]; then
    echo "downloading appimagetool..."
    curl -fsSL -o "$TOOL" \
      "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
      || wget -q -O "$TOOL" \
      "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$TOOL"
  fi
  SLIM_OUT="$ROOT/dist/MihomoTray_linux_qt_${ARTIFACT_VER}_x86_64.AppImage"
  rm -f "$SLIM_OUT"
  ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" "$SQ" "$SLIM_OUT"
  chmod +x "$SLIM_OUT"
  rm -f "$FAT"
  find "$ROOT/dist" -maxdepth 1 -name '*.AppImage' ! -name "MihomoTray_linux_qt_${ARTIFACT_VER}_x86_64.AppImage" -delete 2>/dev/null || true
  rm -rf "$EXTRACT" "$WORK"
  echo "built $SLIM_OUT ($(du -h "$SLIM_OUT" | cut -f1))"
}

build_gtk() {
  echo "==> building GTK packages (deb / rpm / tar.gz)"
  python3 "$ROOT/tools/build_gtk_packages.py" "$ARTIFACT_VER"
}

case "$TARGET" in
  qt) build_qt ;;
  gtk) build_gtk ;;
  all) build_qt; build_gtk ;;
esac
rm -rf build mihomotray.egg-info
echo "done (version $VERSION build $BUILD → artifacts $ARTIFACT_VER)"
