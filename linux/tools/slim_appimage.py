#!/usr/bin/env python3
"""Strip unused Qt / Python bits from an extracted AppImage tree, then leave it ready to repack."""
import os
import shutil
import sys

# Keep these Qt shared libs (prefix match after lib)
KEEP_LIBS = {
    "Qt6Core", "Qt6Gui", "Qt6Widgets", "Qt6DBus", "Qt6Network",
    "Qt6XcbQpa", "Qt6WaylandClient", "Qt6WaylandEglClientHwIntegration",
    "Qt6WlShellIntegration", "Qt6EglFSDeviceIntegration", "Qt6EglFsKmsSupport",
    "Qt6OpenGL",  # Gui/Xcb often needs OpenGL symbols
    "icu", "ICUDATA", "ICUUC", "ICUI18N",  # various casings
}
# Also keep any lib whose name contains these (case-insensitive)
KEEP_LIB_SUBSTR = ("icu", "pcre", "glib", "zstd", "png", "harfbuzz", "freetype",
                   "fontconfig", "xcb", "xkb", "wayland", "egl", "drm", "gbm",
                   "dbus", "double-conversion", "b2", "md4c", "oqs", "crypto",
                   "ssl", "nss", "nspr")

KEEP_PLATFORMS = {"libqxcb.so", "libqwayland.so", "libqoffscreen.so", "libqminimal.so"}
KEEP_IMAGEFORMATS = {"libqpng.so"}
KEEP_PLUGIN_DIRS = {"platforms", "imageformats", "platformthemes", "platforminputcontexts",
                    "iconengines", "xcbglintegrations", "wayland-shell-integration",
                    "wayland-decoration-client", "wayland-graphics-integration-client",
                    "tls", "networkinformation"}

KEEP_PYSIDE_SO = {"QtCore", "QtGui", "QtWidgets", "QtDBus", "QtNetwork", "QtOpenGL"}

DROP_PY_STDLIB = {
    "test", "idlelib", "ensurepip", "turtledemo", "tkinter", "lib2to3",
    "pydoc_data", "ctypes/macholib",
}


def keep_lib(name):
    base = name.split(".so")[0]
    # strip lib prefix
    core = base[3:] if base.startswith("lib") else base
    for k in KEEP_LIBS:
        if core == k or core.startswith(k + ".") or core.startswith(k + "-"):
            return True
        if k.lower() in core.lower() and k.lower() in ("icu",):
            return True
    low = name.lower()
    return any(s in low for s in KEEP_LIB_SUBSTR)


def slim(root):
    # Find PySide6
    site = None
    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath.endswith("site-packages") and "PySide6" in dirnames:
            site = dirpath
            break
    if not site:
        raise SystemExit("PySide6 not found under " + root)
    pyside = os.path.join(site, "PySide6")
    qt = os.path.join(pyside, "Qt")

    # Drop leftover pyside6 CLI wrappers in opt/.../bin and usr/bin
    for binroot in (
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(site))), "bin"),
        os.path.join(root, "usr", "bin"),
        os.path.join(root, "opt", "python3.12", "bin"),
    ):
        if not os.path.isdir(binroot):
            continue
        for fn in list(os.listdir(binroot)):
            if fn.startswith("pyside6-") or fn in ("assistant", "designer", "linguist"):
                try:
                    os.remove(os.path.join(binroot, fn))
                    print("removed wrapper", fn)
                except OSError:
                    pass

    # Drop qml, translations, doc, include, metatypes, helpers
    for rel in ("Qt/qml", "Qt/translations", "Qt/doc", "include", "doc", "Qt/metatypes",
                "Qt/libexec", "glue", "scripts", "typesystems", "py.typed"):
        p = os.path.join(pyside, rel) if not rel.startswith("Qt/") else os.path.join(pyside, rel)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
            print("removed", p)

    # Drop designer binaries and unused .abi3.so
    for fn in os.listdir(pyside):
        path = os.path.join(pyside, fn)
        if fn.startswith("Qt") and fn.endswith(".abi3.so"):
            mod = fn[2:].split(".")[0] if False else fn[len("Qt"):].split(".")[0]
            # fn like QtWidgets.abi3.so → Widgets
            name = fn.split(".")[0]  # QtWidgets
            short = name[2:] if name.startswith("Qt") else name  # Widgets
            if name not in {"Qt" + s for s in KEEP_PYSIDE_SO} and name not in KEEP_PYSIDE_SO:
                # KEEP_PYSIDE_SO has QtCore style... fix:
                if name not in KEEP_PYSIDE_SO and not any(name == x for x in KEEP_PYSIDE_SO):
                    if name not in {"QtCore", "QtGui", "QtWidgets", "QtDBus", "QtNetwork", "QtOpenGL"}:
                        os.remove(path)
                        print("removed", path)
                        pyi = path.replace(".abi3.so", ".pyi")
                        if os.path.isfile(pyi):
                            os.remove(pyi)
        if fn.startswith("pyside6-") or fn in ("assistant", "designer", "linguist", "lrelease",
                                                 "lupdate", "qml", "qmlcachegen", "qmlformat",
                                                 "qmllint", "qmlls", "qmltyperegistrar",
                                                 "qsb", "qtpy2cpp", "rcc", "uic", "balsam",
                                                 "balsamui", "svgtoqml"):
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
                print("removed bin", path)

    # Qt libs
    libdir = os.path.join(qt, "lib")
    if os.path.isdir(libdir):
        for fn in os.listdir(libdir):
            if not keep_lib(fn):
                os.remove(os.path.join(libdir, fn))
                print("removed lib", fn)

    # Explicitly drop unused Wayland compositor / eglfs (client + xcb kept)
    libdir = os.path.join(qt, "lib")
    if os.path.isdir(libdir):
        for fn in list(os.listdir(libdir)):
            low = fn.lower()
            if "compositor" in low or "eglfs" in low or "eglfskms" in low:
                os.remove(os.path.join(libdir, fn))
                print("removed extra", fn)

    # Plugins
    plug = os.path.join(qt, "plugins")
    if os.path.isdir(plug):
        for d in list(os.listdir(plug)):
            dp = os.path.join(plug, d)
            if not os.path.isdir(dp):
                continue
            if d not in KEEP_PLUGIN_DIRS:
                shutil.rmtree(dp)
                print("removed plugin dir", d)
                continue
            if d == "platforms":
                for f in list(os.listdir(dp)):
                    if f not in KEEP_PLATFORMS:
                        os.remove(os.path.join(dp, f))
            elif d == "imageformats":
                for f in list(os.listdir(dp)):
                    if f not in KEEP_IMAGEFORMATS:
                        os.remove(os.path.join(dp, f))

    # Drop unused PySide json extras if any
    for fn in list(os.listdir(pyside)):
        if fn.endswith(".json") and "Essentials" not in fn:
            pass  # keep

    # Python stdlib trim
    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath.endswith("/lib/python3.12") or dirpath.endswith("/lib/python3.11") or dirpath.endswith("/lib/python3.10"):
            for drop in DROP_PY_STDLIB:
                p = os.path.join(dirpath, drop)
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                    print("removed stdlib", p)
            break

    # Drop pip from AppImage usr/bin helpers that pull weight? keep pip optional — remove pip package
    for dirpath, dirnames, filenames in os.walk(os.path.join(site)):
        for d in list(dirnames):
            if d in ("pip", "setuptools", "wheel", "pkg_resources", "_distutils_hack"):
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
                print("removed", d)
        break


    # Remove type stubs and __pycache__
    for dirpath, dirnames, filenames in os.walk(pyside):
        for f in filenames:
            if f.endswith((".pyi", ".pyc")) or f == "py.typed":
                try:
                    os.remove(os.path.join(dirpath, f))
                except OSError:
                    pass
        if "__pycache__" in dirnames:
            shutil.rmtree(os.path.join(dirpath, "__pycache__"), ignore_errors=True)

    # strip shared libs
    import subprocess
    for dirpath, dirnames, filenames in os.walk(os.path.join(qt, "lib")):
        for f in filenames:
            if ".so" in f:
                fp = os.path.join(dirpath, f)
                try:
                    subprocess.call(["strip", "--strip-unneeded", fp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except OSError:
                    pass
    for dirpath, dirnames, filenames in os.walk(pyside):
        for f in filenames:
            if f.endswith(".so") or ".so." in f or f.endswith(".abi3.so"):
                fp = os.path.join(dirpath, f)
                try:
                    subprocess.call(["strip", "--strip-unneeded", fp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except OSError:
                    pass

    # Drop more stdlib rarely needed for tray
    for dirpath, dirnames, filenames in os.walk(root):
        if "/lib/python3." in dirpath and dirpath.rstrip("/").endswith(tuple(f"python3.{i}" for i in range(9, 14))):
            for drop in ("unittest", "email/test", "distutils", "lib-dynload/_tkinter*", "config-*-linux*", "site-packages/pip", "site-packages/setuptools", "site-packages/wheel"):
                pass
            for drop in ("unittest", "distutils", "pydoc.py", "doctest.py", "sqlite3", "dbm", "venv", "wsgiref", "xmlrpc", "http/server.py", "idlelib"):
                pp = os.path.join(dirpath, drop)
                if os.path.isdir(pp):
                    shutil.rmtree(pp, ignore_errors=True)
                elif os.path.isfile(pp):
                    os.remove(pp)
            break

    # shiboken6 keep (needed)

def main():
    if len(sys.argv) != 2:
        print("usage: slim_appimage.py <extracted-AppDir>", file=sys.stderr)
        sys.exit(2)
    root = sys.argv[1]
    slim(root)
    # report size
    total = 0
    for dp, dn, fn in os.walk(root):
        for f in fn:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    print("slimmed tree bytes:", total)
    print("slimmed tree MB:", round(total / 1024 / 1024, 1))


if __name__ == "__main__":
    main()
