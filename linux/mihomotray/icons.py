"""图标路径：优先 ~/.config/MihomoTray/Icons/tray_<name>.png，否则用包内多尺寸 PNG。
不含 GUI 依赖，Qt / GTK 前端各自加载。"""
import os
import shutil

from . import config

ICON_NAMES = ("rule", "global", "direct", "offline")
ICON_SIZES = (16, 22, 24, 32, 48, 64, 128, 256)
PKG_ICONS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")


def ensure_user_icon(name):
    """确保用户目录有 tray_<name>.png（从内置 256px 复制），返回可用路径。
    用户文件超过 2MB 或不存在时返回包内最大可用尺寸路径。"""
    user = os.path.join(config.icons_dir(), "tray_%s.png" % name)
    try:
        if not os.path.exists(user):
            os.makedirs(config.icons_dir(), exist_ok=True)
            shutil.copyfile(os.path.join(PKG_ICONS, "tray_%s_256.png" % name), user)
        if os.path.isfile(user) and os.path.getsize(user) <= 2 * 1024 * 1024:
            return user
    except OSError:
        pass
    for s in reversed(ICON_SIZES):
        p = os.path.join(PKG_ICONS, "tray_%s_%d.png" % (name, s))
        if os.path.exists(p):
            return p
    return os.path.join(PKG_ICONS, "tray_%s_256.png" % name)


def package_icon_paths(name):
    """包内各尺寸路径列表（存在的）。"""
    out = []
    for s in ICON_SIZES:
        p = os.path.join(PKG_ICONS, "tray_%s_%d.png" % (name, s))
        if os.path.exists(p):
            out.append(p)
    return out
