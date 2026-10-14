export MIHOMOTRAY_FRONTEND=qt
if [ -z "${APPDIR}" ]; then
  APPDIR="$(dirname "$(readlink -f "$0")")"
  # entrypoint may live in AppDir root; python-appimage substitutes {{ python-executable }}
fi
{{ python-executable }} -s -m mihomotray "$@"
