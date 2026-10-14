"""开机自启：~/.config/autostart/MihomoTray.desktop（XDG Autostart，GNOME/KDE/XFCE/Cinnamon/MATE/Budgie 都认）。
每次启动按 config.ini 的 autostart 同步：true 写入/更新，false 只删除带 X-MihomoTray 标记的自己的文件。"""
import os
import sys

MARKER = "X-MihomoTray-Autostart=true"


def autostart_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "autostart")


def desktop_path():
    return os.path.join(autostart_dir(), "MihomoTray.desktop")


def launch_command():
    """AppImage → $APPIMAGE；MIHOMOTRAY_LAUNCHER；已安装入口 /usr[/local]/bin/mihomotray（argv0 或显式）；
    否则源码：PYTHONPATH + python -m mihomotray。"""
    appimage = os.environ.get("APPIMAGE")
    if appimage and os.path.isfile(appimage):
        return [os.path.abspath(appimage)]
    launcher = os.environ.get("MIHOMOTRAY_LAUNCHER")
    if launcher and os.path.isfile(launcher) and os.access(launcher, os.X_OK):
        return [os.path.abspath(launcher)]
    argv0 = os.path.abspath(sys.argv[0]) if sys.argv else ""
    if os.path.basename(argv0) == "mihomotray" and os.path.isfile(argv0) and os.access(argv0, os.X_OK):
        return [argv0]
    if os.environ.get("MIHOMOTRAY_USE_SYSTEM_LAUNCHER") == "1":
        for cand in ("/usr/bin/mihomotray", "/usr/local/bin/mihomotray"):
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return [cand]
    pkg_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return ["/usr/bin/env", "PYTHONPATH=" + pkg_parent, sys.executable, "-m", "mihomotray"]


def _quote(arg):
    # Desktop Entry 规范：含保留字符的参数加双引号，" ` $ \ 前加反斜杠；% 写成 %%
    arg = arg.replace("%", "%%")
    if any(c in arg for c in ' \t\n"\'\\><~|&;$*?#()`'):
        return '"' + "".join("\\" + c if c in '"`$\\' else c for c in arg) + '"'
    return arg


def desktop_entry(cmd):
    return ("[Desktop Entry]\n"
            "Type=Application\n"
            "Name=MihomoTray\n"
            "Comment=mihomo proxy mode tray icon\n"
            "Exec=" + " ".join(_quote(a) for a in cmd) + "\n"
            "Icon=mihomotray\n"
            "Terminal=false\n"
            "X-GNOME-Autostart-enabled=true\n"
            + MARKER + "\n")


def decide(enabled, current, wanted):
    """决策逻辑（可单测）：current 为现有文件内容（没有则 None）。返回 'write' / 'delete' / None。"""
    if enabled:
        return None if current == wanted else "write"
    if current is not None and MARKER in current:
        return "delete"
    return None  # 不是自己写的文件不碰


def sync(enabled):
    """成功返回 None，失败返回原因。"""
    path = desktop_path()
    try:
        current = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
    except OSError:
        current = None
    wanted = desktop_entry(launch_command())
    action = decide(enabled, current, wanted)
    try:
        if action == "write":
            os.makedirs(autostart_dir(), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(wanted)
            os.replace(tmp, path)
        elif action == "delete":
            os.remove(path)
    except OSError as e:
        return str(e)
    return None
