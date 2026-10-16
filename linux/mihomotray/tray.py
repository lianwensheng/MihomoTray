"""托盘图标与菜单（Qt / PySide6）。QSystemTrayIcon 在 Linux 上优先走 StatusNotifierItem，
没有 SNI 宿主时 Qt 自动退回 XEmbed。"""
import os
import shutil
import subprocess
import sys
import threading
import time

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from . import autostart, config, icons, loc
from .client import MihomoClient, tray_tip

MODES = ("rule", "global", "direct")


def log(msg):
    sys.stderr.write("MihomoTray: " + msg.replace("\n", " | ") + "\n")
    sys.stderr.flush()


def load_icon(name):
    """优先用 ~/.config/MihomoTray/Icons/tray_<name>.png；文件不存在时先复制内置 256px。"""
    user = icons.ensure_user_icon(name)
    try:
        if os.path.isfile(user) and os.path.getsize(user) <= 2 * 1024 * 1024:
            ic = QIcon(user)
            if not ic.isNull() and not ic.pixmap(16, 16).isNull():
                return ic
    except OSError:
        pass
    ic = QIcon()
    for p in icons.package_icon_paths(name):
        ic.addFile(p)
    return ic


class TrayApp(QObject):
    _result = Signal(object)   # 后台线程把结果交回 UI 线程

    def __init__(self, cfg, tray_cls=QSystemTrayIcon):
        super().__init__()
        self.cfg = cfg
        self.client = MihomoClient(cfg.controller, cfg.secret)
        self.mode = None
        self.connected = False
        self.disposed = False
        self.tip = ""
        self._polling = False
        self._switch_seq = 0
        self._switching = 0
        self._pending_mode = None
        self._last_panel_open = 0.0
        self._lock = threading.Lock()
        self._result.connect(lambda fn: fn())
        self.icons = {n: load_icon(n) for n in icons.ICON_NAMES}
        self.icon_key = "offline"

        self.menu = QMenu()
        self.menu.aboutToShow.connect(self.poll)
        self.status_text = loc.Disconnected()
        self.act_status = QAction(self.status_text, self.menu)
        self.act_status.setEnabled(False)
        self.act_panel = QAction(loc.OpenPanel(), self.menu)
        self.act_panel.triggered.connect(self.open_panel)
        self.act_app = QAction(loc.SwitchProgram(), self.menu)
        self.act_app.setEnabled(cfg.has_switch_program)
        self.act_app.triggered.connect(self.launch_switch_program)
        self.act_modes = {}
        labels = {"rule": loc.ModeRule(), "global": loc.ModeGlobal(), "direct": loc.ModeDirect()}
        for m in MODES:
            a = QAction(labels[m], self.menu)
            a.setCheckable(True)
            a.setEnabled(False)
            a.triggered.connect(lambda _=False, mm=m: self.switch_mode(mm))
            self.act_modes[m] = a
        self.act_exit = QAction(loc.Exit(), self.menu)
        self.act_exit.triggered.connect(self.quit)
        self.menu.addAction(self.act_status)
        self.sep_status = self.menu.addSeparator()  # 与 act_status 一起：仅断连时显示
        self.menu.addAction(self.act_panel)
        self.menu.addAction(self.act_app)
        self.menu.addSeparator()
        for m in MODES:
            self.menu.addAction(self.act_modes[m])
        self.menu.addSeparator()
        self.menu.addAction(self.act_exit)
        self._sync_status_row()

        self.tray = tray_cls(self.icons["offline"])
        self.tray.setContextMenu(self.menu)
        self.set_tip(loc.Disconnected())   # 第一次轮询成功前显示“未连接”
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        self.timer = QTimer(self)
        self.timer.setInterval(cfg.poll_seconds * 1000)
        self.timer.timeout.connect(self.poll)
        self.timer.start()
        self.poll()

        err = autostart.sync(cfg.autostart)
        if err:
            cfg.errors.append(loc.AutostartFailed() + (": " if loc.En else "：") + err)
        if cfg.errors:
            self.warn(loc.BadConfig(), "\n".join(cfg.errors))

    # ---- 托盘事件 ----
    def _on_activated(self, reason):
        # 左键（KDE / XFCE 等会发 Trigger）打开面板；GNOME 的 AppIndicator 只弹菜单，不会走到这里
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            now = time.monotonic()
            if now - self._last_panel_open < 0.8:
                return
            self._last_panel_open = now
            self.open_panel()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            self.poll()

    def _post(self, fn):
        self._result.emit(fn)

    # ---- 轮询 ----
    def poll(self):
        if self.disposed:
            return
        with self._lock:
            if self._polling:
                return
            self._polling = True
        seq_at_start = self._switch_seq

        def work():
            st, err = None, None
            try:
                st = self.client.get_status()
            except Exception as e:
                err = e
            finally:
                with self._lock:
                    self._polling = False

            def done():
                # 切换进行中，或者这次轮询发出后又切换过模式：结果可能是旧的，丢弃
                if self._switching > 0 or seq_at_start != self._switch_seq:
                    return
                self.update_state(st, err)
            self._post(done)
        threading.Thread(target=work, daemon=True).start()

    def update_state(self, st, err):
        if self.disposed:
            return
        if err is not None:
            self.connected = False
            self.status_text = loc.ShortStatus(err)
            self.set_icon("offline")
            self.set_tip(self.status_text)
        else:
            self.connected = True
            self.mode = st.mode
            key = st.mode if st.mode in MODES else "rule"
            self.status_text = (
                loc.ModeRule() if key == "rule" else loc.ModeGlobal() if key == "global" else loc.ModeDirect()
            )
            self.set_icon(key)
            self.set_tip(tray_tip(True, st.mode, st.tun_enabled, st.log_level))
        self.act_status.setText(self.status_text)
        self._sync_status_row()
        for m, a in self.act_modes.items():
            a.setEnabled(self.connected)
            a.setChecked(self.connected and self.mode == m)

    def _sync_status_row(self):
        """连上后隐藏顶部灰字与紧挨的分隔线；断连时显示。"""
        show = not self.connected
        self.act_status.setVisible(show)
        self.sep_status.setVisible(show)

    def set_icon(self, key):
        if key != self.icon_key:
            self.icon_key = key
            self.tray.setIcon(self.icons[key])

    def set_tip(self, t):
        # 桌面不显示悬停提示（如 GNOME）时这里设了也看不到，忽略即可
        t = t[:63]
        if t != self.tip:
            self.tip = t
            self.tray.setToolTip(t)

    # ---- 动作 ----
    def switch_mode(self, mode):
        if self.disposed:
            return
        self._pending_mode = mode
        self._switch_seq += 1
        seq = self._switch_seq
        self._switching += 1

        def work():
            # 连点时只认最新目标：若飞行中又被更新，循环再 set 一次，避免旧请求后到把模式盖回去
            err, now = None, None
            try:
                while True:
                    target = self._pending_mode
                    snap = self._switch_seq
                    self.client.set_mode(target)
                    if self.cfg.close_connections:
                        try:
                            self.client.close_all_connections()
                        except Exception:
                            pass
                    now = self.client.get_status()
                    if snap == self._switch_seq:
                        break
            except Exception as e:
                err = e
                now = None

            def done():
                self._switching -= 1
                if self.disposed or seq != self._switch_seq:
                    return  # 已经有更新的一次切换
                if err is not None:
                    self.update_state(None, err)
                    self.warn(loc.SwitchFailed(), str(err) + "\n" + loc.ControllerLabel() + self.cfg.controller)
                else:
                    self.update_state(now, None)
            self._post(done)
        threading.Thread(target=work, daemon=True).start()

    def open_panel(self):
        self.maybe_show_panel_tip()
        url = self.cfg.panel_url
        if QDesktopServices.openUrl(QUrl(url)):
            return
        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except OSError as e:
            self.warn(loc.CantOpenPanel(), str(e) + "\n" + url)

    def maybe_show_panel_tip(self):
        """打开面板：secret 为空或纯空格时每次通知 panel_url；配了 secret 则不提示。"""
        if (self.cfg.secret or "").strip():
            return
        self.info(loc.OpenPanel(), loc.PanelTipBody(self.cfg.panel_url))

    def launch_switch_program(self):
        argv, err = self.cfg.program_command()
        if err:
            self.warn(loc.CantOpenApp(), err)
            return
        try:
            subprocess.Popen(argv, cwd=os.path.dirname(argv[0]) or None, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError as e:
            self.warn(loc.CantOpenApp(), str(e) + "\n" + argv[0])

    def warn(self, title, text):
        """切换失败等提示：桌面通知；没有通知服务时只打日志。"""
        if self.disposed:
            return
        if len(text) > 250:
            text = text[:247] + "..."
        log(title + ": " + text)
        try:
            if QSystemTrayIcon.supportsMessages() and self.tray.isVisible():
                self.tray.showMessage(title, text, QSystemTrayIcon.MessageIcon.Warning, 4000)
                return
        except Exception:
            pass
        if shutil.which("notify-send"):
            try:
                subprocess.Popen(["notify-send", "-a", "MihomoTray", "-u", "normal", title, text],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass

    def info(self, title, text):
        """首次打开面板等轻提示。"""
        if self.disposed:
            return
        if len(text) > 250:
            text = text[:247] + "..."
        log(title + ": " + text)
        try:
            if QSystemTrayIcon.supportsMessages() and self.tray.isVisible():
                self.tray.showMessage(title, text, QSystemTrayIcon.MessageIcon.Information, 4000)
                return
        except Exception:
            pass
        if shutil.which("notify-send"):
            try:
                subprocess.Popen(["notify-send", "-a", "MihomoTray", "-u", "low", title, text],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass

    def quit(self):
        if self.disposed:
            return
        self.disposed = True
        from PySide6.QtWidgets import QApplication
        try:
            self.timer.stop()
            self.tray.hide()
        finally:
            QApplication.quit()
