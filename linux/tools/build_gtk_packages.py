#!/usr/bin/env python3
"""Build GTK variant: .deb, .rpm, and .tar.gz into dist/."""
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def version_arg():
    if len(sys.argv) > 1:
        return sys.argv[1]
    text = (ROOT / "mihomotray" / "__init__.py").read_text()
    for line in text.splitlines():
        if line.startswith("__version__"):
            return line.split('"')[1]
    raise SystemExit("no version")


def copy_package(dest: Path):
    pkg = dest / "mihomotray"
    shutil.copytree(
        ROOT / "mihomotray",
        pkg,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


LAUNCHER = """#!/usr/bin/env python3
import os
import sys
os.environ.setdefault("MIHOMOTRAY_FRONTEND", "gtk")
from mihomotray.__main__ import main
raise SystemExit(main())
"""

DESKTOP = """[Desktop Entry]
Type=Application
Name=MihomoTray
Comment=mihomo proxy mode tray icon
Exec=mihomotray
Icon=mihomotray
Terminal=false
Categories=Network;Utility;
"""

INSTALL_SH = r"""#!/bin/sh
# Install MihomoTray GTK from this tarball (user or system prefix).
set -e
PREFIX="${PREFIX:-/usr/local}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "Installing to $PREFIX"
install -d "$PREFIX/bin"
install -d "$PREFIX/lib/mihomotray"
install -d "$PREFIX/share/applications"
install -d "$PREFIX/share/icons/hicolor/256x256/apps"
rm -rf "$PREFIX/lib/mihomotray/mihomotray"
cp -a "$ROOT/mihomotray" "$PREFIX/lib/mihomotray/"
cat > "$PREFIX/bin/mihomotray" <<'LAUNCH'
#!/usr/bin/env python3
import os, sys
os.environ.setdefault("MIHOMOTRAY_FRONTEND", "gtk")
PREFIX = "@@PREFIX@@"
sys.path.insert(0, PREFIX + "/lib/mihomotray")
from mihomotray.__main__ import main
raise SystemExit(main())
LAUNCH
# Patch prefix into launcher
sed "s|@@PREFIX@@|$PREFIX|g" "$PREFIX/bin/mihomotray" > "$PREFIX/bin/mihomotray.tmp"
mv "$PREFIX/bin/mihomotray.tmp" "$PREFIX/bin/mihomotray"
chmod +x "$PREFIX/bin/mihomotray"
cp "$ROOT/mihomotray.desktop" "$PREFIX/share/applications/"
if [ "$PREFIX" != "/usr" ]; then
  sed "s|^Exec=.*|Exec=$PREFIX/bin/mihomotray|" "$PREFIX/share/applications/mihomotray.desktop" > "$PREFIX/share/applications/mihomotray.desktop.tmp"
  mv "$PREFIX/share/applications/mihomotray.desktop.tmp" "$PREFIX/share/applications/mihomotray.desktop"
fi
cp "$ROOT/mihomotray.png" "$PREFIX/share/icons/hicolor/256x256/apps/mihomotray.png"
echo "Done. Run: mihomotray"
echo "Dependencies: python3, PyGObject, AyatanaAppIndicator3, Gtk3, libnotify — see README."
"""


def write_launcher(path: Path):
    path.write_text(LAUNCHER)
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def build_deb(ver: str):
    work = Path(tempfile.mkdtemp(prefix="mtray-deb-"))
    try:
        root = work / ("mihomotray_%s_all" % ver)
        lib = root / "usr/lib/python3/dist-packages"
        bin_dir = root / "usr/bin"
        apps = root / "usr/share/applications"
        icons = root / "usr/share/icons/hicolor/256x256/apps"
        debian = root / "DEBIAN"
        for d in (lib, bin_dir, apps, icons, debian):
            d.mkdir(parents=True)
        copy_package(lib)
        write_launcher(bin_dir / "mihomotray")
        (apps / "mihomotray.desktop").write_text(DESKTOP)
        shutil.copy2(ROOT / "mihomotray/icons/tray_rule_256.png", icons / "mihomotray.png")
        size = sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) // 1024
        control = (
            "Package: mihomotray\n"
            "Version: %s\n"
            "Section: net\n"
            "Priority: optional\n"
            "Architecture: all\n"
            "Installed-Size: %d\n"
            "Maintainer: MihomoTray <mihomotray@local>\n"
            "Depends: python3 (>= 3.9), python3-gi, gir1.2-gtk-3.0, "
            "gir1.2-ayatanaappindicator3-0.1 | gir1.2-appindicator3-0.1, gir1.2-notify-0.7\n"
            "Description: Tray icon for mihomo proxy mode (GTK)\n"
            " Lightweight GTK + AppIndicator tray that shows and switches\n"
            " mihomo rule/global/direct modes.\n"
        ) % (ver, size)
        (debian / "control").write_text(control)
        out = DIST / ("MihomoTray_linux_%s.deb" % ver)
        subprocess.check_call(["dpkg-deb", "--build", "--root-owner-group", str(root), str(out)])
        print("built", out, "(%d KB)" % (out.stat().st_size // 1024))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def build_rpm(ver: str):
    work = Path(tempfile.mkdtemp(prefix="mtray-rpm-"))
    try:
        rpmbuild = work / "rpmbuild"
        for d in ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS", "BUILDROOT"):
            (rpmbuild / d).mkdir(parents=True)
        src_root = work / ("mihomotray-%s" % ver)
        lib = src_root / "usr/lib/python3/site-packages"
        bin_dir = src_root / "usr/bin"
        apps = src_root / "usr/share/applications"
        icons = src_root / "usr/share/icons/hicolor/256x256/apps"
        for d in (lib, bin_dir, apps, icons):
            d.mkdir(parents=True)
        copy_package(lib)
        write_launcher(bin_dir / "mihomotray")
        (apps / "mihomotray.desktop").write_text(DESKTOP)
        shutil.copy2(ROOT / "mihomotray/icons/tray_rule_256.png", icons / "mihomotray.png")
        tarball = rpmbuild / "SOURCES" / ("mihomotray-%s.tar.gz" % ver)
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(src_root, arcname="mihomotray-%s" % ver)
        spec = """Name:           mihomotray
Version:        %(ver)s
Release:        1%%{?dist}
Summary:        Tray icon for mihomo proxy mode (GTK)
License:        MIT
BuildArch:      noarch
Source0:        mihomotray-%(ver)s.tar.gz
Requires:       python3 >= 3.9
Requires:       python3-gobject
Requires:       libayatana-appindicator-gtk3
Requires:       libnotify
Requires:       gtk3

%%description
Lightweight GTK + AppIndicator tray that shows and switches
mihomo rule/global/direct modes.

%%prep
%%setup -q

%%build

%%install
rm -rf %%{buildroot}
mkdir -p %%{buildroot}
cp -a usr %%{buildroot}/

%%files
/usr/bin/mihomotray
/usr/lib/python3/site-packages/mihomotray
/usr/share/applications/mihomotray.desktop
/usr/share/icons/hicolor/256x256/apps/mihomotray.png

%%changelog
* Wed Oct 14 2026 MihomoTray <mihomotray@local> - %(ver)s-1
- Initial GTK package
""" % {"ver": ver}
        spec_path = rpmbuild / "SPECS" / "mihomotray.spec"
        spec_path.write_text(spec)
        subprocess.check_call([
            "rpmbuild", "-bb",
            "--define", "_topdir %s" % rpmbuild,
            str(spec_path),
        ])
        built = list((rpmbuild / "RPMS").rglob("*.rpm"))
        if not built:
            raise SystemExit("rpmbuild produced no rpm")
        out = DIST / ("MihomoTray_linux_%s.rpm" % ver)
        shutil.copy2(built[0], out)
        print("built", out, "(%d KB)" % (out.stat().st_size // 1024))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def build_targz(ver: str):
    work = Path(tempfile.mkdtemp(prefix="mtray-tar-"))
    try:
        name = "MihomoTray_linux_gtk_%s" % ver
        root = work / name
        root.mkdir()
        copy_package(root)
        (root / "mihomotray.desktop").write_text(DESKTOP)
        shutil.copy2(ROOT / "mihomotray/icons/tray_rule_256.png", root / "mihomotray.png")
        (root / "install.sh").write_text(INSTALL_SH)
        (root / "install.sh").chmod(0o755)
        (root / "README.txt").write_text(
            "MihomoTray Linux GTK %s\n\n"
            "sudo ./install.sh          # installs to /usr/local\n"
            "PREFIX=/usr sudo ./install.sh\n\n"
            "Or run from source:\n"
            "  MIHOMOTRAY_FRONTEND=gtk PYTHONPATH=. python3 -m mihomotray\n" % ver
        )
        out = DIST / (name + ".tar.gz")
        with tarfile.open(out, "w:gz") as tar:
            tar.add(root, arcname=name)
        print("built", out, "(%d KB)" % (out.stat().st_size // 1024))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    DIST.mkdir(exist_ok=True)
    ver = version_arg()
    build_deb(ver)
    build_rpm(ver)
    build_targz(ver)


if __name__ == "__main__":
    main()
