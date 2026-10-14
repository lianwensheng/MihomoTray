"""入口：单实例（锁文件）→ 读配置 → Qt 或 GTK 托盘。

前端选择：环境变量 MIHOMOTRAY_FRONTEND=qt|gtk|auto（默认 auto）。
auto：能 import PySide6 则 qt，否则 gtk。
AppImage 入口固定 qt；deb/rpm 的 /usr/bin/mihomotray 固定 gtk。
"""
import os
import sys
import time


def _pick_frontend():
    pref = (os.environ.get("MIHOMOTRAY_FRONTEND") or "auto").strip().lower()
    if pref in ("qt", "gtk"):
        return pref
    try:
        import PySide6  # noqa: F401
        return "qt"
    except ImportError:
        return "gtk"


def main():
    from . import config, loc
    from .single_instance import acquire_lock

    frontend = _pick_frontend()
    loc.apply("system")
    lock = acquire_lock()
    if lock is None:
        _already_running(frontend)
        return 0

    cfg = config.load()
    if frontend == "gtk":
        rc = _run_gtk(cfg)
    else:
        rc = _run_qt(cfg)
    lock.close()
    return rc


def _already_running(frontend):
    from . import loc
    if frontend == "gtk":
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk
            dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=loc.AlreadyRunning(),
            )
            dialog.set_title(loc.AppTitle)
            dialog.run()
            dialog.destroy()
            return
        except Exception:
            pass
        sys.stderr.write(loc.AlreadyRunning() + "\n")
        return
    from PySide6.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance() or QApplication(sys.argv)
    QMessageBox.information(None, loc.AppTitle, loc.AlreadyRunning())


def _run_qt(cfg):
    from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
    from . import loc
    from .tray import TrayApp, log

    app = QApplication(sys.argv)
    app.setApplicationName("MihomoTray")
    app.setDesktopFileName("mihomotray")
    app.setQuitOnLastWindowClosed(False)

    def fatal(t, v, tb):
        import traceback
        traceback.print_exception(t, v, tb)
        try:
            QMessageBox.critical(None, loc.AppTitle, loc.FatalPrefix() + (str(v) or loc.UnknownError()))
        except Exception:
            pass
        os._exit(1)
    sys.excepthook = fatal

    # 开机自启时面板可能比我们晚启动：最多等 30 秒托盘宿主出现
    if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
        for _ in range(30):
            if QSystemTrayIcon.isSystemTrayAvailable():
                break
            app.processEvents()
            time.sleep(1)
        else:
            log("no system tray found (GNOME needs the AppIndicator extension) / "
                "没有找到系统托盘（GNOME 需要 AppIndicator 扩展）")
    tray = TrayApp(cfg)
    rc = app.exec()
    del tray
    return rc


def _run_gtk(cfg):
    from . import loc
    from .gtk_tray import log, run_gtk

    def fatal(t, v, tb):
        import traceback
        traceback.print_exception(t, v, tb)
        try:
            log(loc.FatalPrefix() + (str(v) or loc.UnknownError()))
        except Exception:
            pass
        os._exit(1)
    sys.excepthook = fatal

    # AppIndicator 会在宿主出现后连上；开机场景可选等待（MIHOMOTRAY_TRAY_WAIT=1 最多 30 秒）
    if os.environ.get("MIHOMOTRAY_TRAY_WAIT") == "1":
        for i in range(30):
            time.sleep(1)
            # 无可靠探测 API；满等后继续创建 Indicator
        log("tray wait finished / 托盘等待结束")

    run_gtk(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
