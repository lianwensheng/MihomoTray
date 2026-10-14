"""托盘图标与菜单（GTK3 + AyatanaAppIndicator3，可选回退 AppIndicator3）。
点击托盘只弹菜单（无单独左键动作）；AppIndicator 无悬停提示，不在菜单顶部加模式文字。"""
import os
import subprocess
import sys
import threading
import time
import webbrowser

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3  # noqa: E402
except (ValueError, ImportError):
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3  # noqa: E402

try:
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify  # noqa: E402
    _HAS_NOTIFY = True
except (ValueError, ImportError):
    Notify = None
    _HAS_NOTIFY = False

from . import autostart, config, icons, loc
from .client import MihomoClient

MODES = ("rule", "global", "direct")


def log(msg):
    sys.stderr.write("MihomoTray: " + msg.replace("\n", " | ") + "\n")
    sys.stderr.flush()


class GtkTrayApp:
    def __init__(self, cfg):
        self.cfg = cfg
        self.client = MihomoClient(cfg.controller, cfg.secret)
        self.mode = None
        self.connected = False
        self.disposed = False
        self._polling = False
        self._switch_seq = 0
        self._switching = 0
        self._lock = threading.Lock()
        self.icon_paths = {n: icons.ensure_user_icon(n) for n in icons.ICON_NAMES}
        self.icon_key = "offline"
        self.warnings = []  # 测试可检查；正式运行也会走 warn()

        if _HAS_NOTIFY:
            try:
                if not Notify.is_initted():
                    Notify.init("MihomoTray")
            except Exception:
                pass

        GtkTrayApp._id_seq = getattr(GtkTrayApp, "_id_seq", 0) + 1
        self.indicator = AppIndicator3.Indicator.new(
            "mihomotray-%d" % GtkTrayApp._id_seq,
            self.icon_paths["offline"],
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title(loc.AppTitle)
        try:
            self.indicator.set_icon_full(self.icon_paths["offline"], loc.Disconnected())
        except Exception:
            self.indicator.set_icon(self.icon_paths["offline"])

        self.menu = Gtk.Menu()
        self.act_panel = Gtk.MenuItem(label=loc.OpenPanel())
        self.act_panel.connect("activate", lambda *_: self.open_panel())
        self.act_app = Gtk.MenuItem(label=loc.SwitchProgram())
        self.act_app.set_sensitive(cfg.has_switch_program)
        self.act_app.connect("activate", lambda *_: self.launch_switch_program())
        self.act_modes = {}
        self._mode_handler_ids = {}
        labels = {"rule": loc.ModeRule(), "global": loc.ModeGlobal(), "direct": loc.ModeDirect()}
        for m in MODES:
            a = Gtk.CheckMenuItem(label=labels[m])
            a.set_sensitive(False)
            hid = a.connect("activate", self._on_mode_activate, m)
            self.act_modes[m] = a
            self._mode_handler_ids[m] = hid
        self.act_exit = Gtk.MenuItem(label=loc.Exit())
        self.act_exit.connect("activate", lambda *_: self.quit())

        for w in (self.act_panel, self.act_app):
            self.menu.append(w)
        self.menu.append(Gtk.SeparatorMenuItem())
        for m in MODES:
            self.menu.append(self.act_modes[m])
        self.menu.append(Gtk.SeparatorMenuItem())
        self.menu.append(self.act_exit)
        self.menu.show_all()
        self.menu.connect("show", lambda *_: self.poll())
        self.indicator.set_menu(self.menu)

        err = autostart.sync(cfg.autostart)
        if err:
            cfg.errors.append(loc.AutostartFailed() + (": " if loc.En else "：") + err)
        if cfg.errors:
            self.warn(loc.BadConfig(), "\n".join(cfg.errors))

        self._timer_id = GLib.timeout_add_seconds(cfg.poll_seconds, self._on_timer)
        self.poll()

    def _on_timer(self):
        if self.disposed:
            return False
        self.poll()
        return True

    def _on_mode_activate(self, item, mode):
        # CheckMenuItem 在代码里 set_active 也会触发；只处理用户点击且当前未勾选的切换
        if self.disposed or self._switching > 0:
            return
        if item.get_active() and self.mode != mode:
            self.switch_mode(mode)

    def _post(self, fn):
        GLib.idle_add(fn)

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
            self.set_icon("offline")
        else:
            self.connected = True
            self.mode = st.mode
            self.set_icon(st.mode if st.mode in MODES else "rule")
        for m, a in self.act_modes.items():
            a.set_sensitive(self.connected)
            a.handler_block(self._mode_handler_ids[m])
            try:
                a.set_active(self.connected and self.mode == m)
            finally:
                a.handler_unblock(self._mode_handler_ids[m])

    def set_icon(self, key):
        if key == self.icon_key:
            return
        self.icon_key = key
        path = self.icon_paths[key]
        try:
            self.indicator.set_icon_full(path, key)
        except Exception:
            self.indicator.set_icon(path)

    def switch_mode(self, mode):
        if self.disposed:
            return
        self._switch_seq += 1
        seq = self._switch_seq
        self._switching += 1

        def work():
            err, now = None, None
            try:
                self.client.set_mode(mode)
                if self.cfg.close_connections:
                    try:
                        self.client.close_all_connections()
                    except Exception:
                        pass
                now = self.client.get_status()
            except Exception as e:
                err = e

            def done():
                self._switching -= 1
                if self.disposed or seq != self._switch_seq:
                    return
                if err is not None:
                    self.update_state(None, err)
                    self.warn(loc.SwitchFailed(), str(err) + "\n" + loc.ControllerLabel() + self.cfg.controller)
                else:
                    self.update_state(now, None)
            self._post(done)
        threading.Thread(target=work, daemon=True).start()

    def open_panel(self):
        url = self.cfg.panel_url
        try:
            if webbrowser.open(url):
                return
        except Exception:
            pass
        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except OSError as e:
            self.warn(loc.CantOpenPanel(), str(e) + "\n" + url)

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
        if self.disposed:
            return
        if len(text) > 250:
            text = text[:247] + "..."
        self.warnings.append((title, text))
        log(title + ": " + text)
        if _HAS_NOTIFY:
            try:
                n = Notify.Notification.new(title, text, None)
                n.set_urgency(Notify.Urgency.NORMAL)
                n.show()
                return
            except Exception:
                pass
        # 没有 libnotify：只打日志（与 Qt 版无通知服务时一致）

    def quit(self):
        if self.disposed:
            return
        self.disposed = True
        if getattr(self, "_timer_id", None):
            try:
                GLib.source_remove(self._timer_id)
            except Exception:
                pass
        try:
            self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
        except Exception:
            pass
        # 测试里可能没进 Gtk.main()，避免 gtk_main_quit 断言
        try:
            if Gtk.main_level() > 0:
                Gtk.main_quit()
        except Exception:
            pass

    def menu_labels(self):
        """测试用：菜单项文字顺序（分隔符为空串）。"""
        out = []
        for child in self.menu.get_children():
            if isinstance(child, Gtk.SeparatorMenuItem):
                out.append("")
            else:
                out.append(child.get_label())
        return out


def run_gtk(cfg):
    app = GtkTrayApp(cfg)
    Gtk.main()
    return app
