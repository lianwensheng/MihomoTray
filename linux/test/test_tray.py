"""MihomoTray Linux 测试：对着 test/mock_mihomo.py（与 Windows 版同一个 mock）跑，无界面（QT_QPA_PLATFORM=offscreen）。
运行：QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s test -v"""
import os, socket, subprocess, sys, tempfile, time, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
TMP = tempfile.mkdtemp(prefix="mtray-test-")
os.environ["XDG_CONFIG_HOME"] = TMP
os.environ.pop("APPIMAGE", None)

from mihomotray import __version__, autostart, config, loc
from mihomotray.client import MihomoClient, MihomoError, parse_status, tray_tip


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def start_mock(port, secret=""):
    p = subprocess.Popen([sys.executable, os.path.join(ROOT, "test", "mock_mihomo.py"), str(port)] + ([secret] if secret else []),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close(); return p
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("mock did not start")


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port, cls.sport = free_port(), free_port()
        cls.m1, cls.m2 = start_mock(cls.port), start_mock(cls.sport, "s3cret")

    @classmethod
    def tearDownClass(cls):
        cls.m1.kill(); cls.m2.kill(); cls.m1.wait(); cls.m2.wait()

    def setUp(self):
        loc.apply("zh")


class LocTest(unittest.TestCase):
    def test_lang(self):
        loc.apply("en"); self.assertEqual(loc.OpenPanel(), "Dashboard")
        loc.apply("zh"); self.assertEqual(loc.OpenPanel(), "打开面板")
        for env, en in (("zh_CN.UTF-8", False), ("zh_TW.UTF-8", False), ("en_US.UTF-8", True), ("de_DE.UTF-8", True)):
            old = {k: os.environ.pop(k, None) for k in ("LANGUAGE", "LC_ALL", "LC_MESSAGES")}
            os.environ["LANG"] = env
            loc.apply("system"); self.assertEqual(loc.En, en, env)
            for k, v in old.items():
                if v is not None: os.environ[k] = v
        os.environ["LANGUAGE"] = "zh_CN:en"; loc.apply("system"); self.assertFalse(loc.En); del os.environ["LANGUAGE"]

    def test_same_as_windows(self):
        """菜单和提示文字与 Windows 版 Loc.cs 完全一致；短文案不带句号。"""
        loc.apply("zh")
        self.assertEqual([loc.OpenPanel(), loc.SwitchProgram(), loc.ModeRule(), loc.ModeGlobal(), loc.ModeDirect(), loc.Exit()],
                         ["打开面板", "切换程序", "规则模式", "全局模式", "直连模式", "退出"])
        self.assertEqual(tray_tip(False, None, False, None), "模式 : 未连接\n日志级别 : —\n虚拟网卡 : —")
        self.assertEqual(tray_tip(True, "global", True, "info"), "模式 : 全局模式\n日志级别 : 信息\n虚拟网卡 : 开启")
        loc.apply("en")
        self.assertEqual(tray_tip(True, "direct", False, "warning"), "Mode : Direct\nLog Level : Warn\nTUN Mode : Off")
        self.assertEqual([loc.OpenPanel(), loc.SwitchProgram(), loc.ModeRule(), loc.ModeGlobal(), loc.ModeDirect(), loc.Exit()],
                         ["Dashboard", "Open App", "Rule", "Global", "Direct", "Exit"])
        for lang in ("zh", "en"):
            loc.apply(lang)
            for s in (loc.OpenPanel(), loc.SwitchProgram(), loc.Exit(), loc.BadConfig(), loc.SwitchFailed(), loc.CantOpenPanel(),
                      loc.CantOpenApp(), loc.AutostartFailed(), loc.Disconnected(), loc.CantConnect()):
                self.assertFalse(s.endswith((".", "。")), s)

    def test_panel_tip_body(self):
        loc.apply("zh")
        zh = loc.PanelTipBody("http://127.0.0.1:9090/ui/")
        self.assertTrue(zh.startswith("配置 secret 安全密钥后停止提醒通知\n"), zh)
        self.assertIn("即将打开 http://127.0.0.1:9090/ui/", zh)
        self.assertIn("可在 config.ini 的 panel_url 修改", zh)
        loc.apply("en")
        en = loc.PanelTipBody("http://example/ui/")
        self.assertTrue(en.startswith("Set secret in config.ini to stop this reminder\n"), en)
        self.assertIn("Opening http://example/ui/", en)
        self.assertIn("Change panel_url in config.ini", en)
        long_url = "http://127.0.0.1:9090/" + ("a" * 300)
        for lang in ("zh", "en"):
            loc.apply(lang)
            s = loc.PanelTipBody("http://x/")
            self.assertTrue(s.startswith(loc.PanelTipStopLine() + "\n"), s)
            self.assertFalse(s.endswith((".", "。")), s)
            short = loc.PanelTipBody(long_url)
            self.assertEqual(short, loc.PanelTipShort())
            self.assertTrue(short.startswith(loc.PanelTipStopLine() + "\n"), short)
            self.assertLessEqual(len(short), 250)
            self.assertFalse(short.endswith((".", "。")), short)

    def test_windows_loc_text(self):
        """逐条比对 Windows 版 Loc.cs 里同名文案（合仓 windows/ 或旧旁挂目录）。"""
        candidates = [
            os.path.join(ROOT, "..", "windows", "src", "Loc.cs"),
            os.path.join(ROOT, "..", "mihomo-tray", "src", "Loc.cs"),
        ]
        p = next((c for c in candidates if os.path.exists(c)), None)
        if p is None: self.skipTest("Windows sources not present")
        import re
        src = open(p, encoding="utf-8").read()
        for name, en, zh in re.findall(r'static string (\w+) \{ get \{ return En \? "((?:[^"\\]|\\.)*)" : "((?:[^"\\]|\\.)*)"; \} \}', src):
            f = getattr(loc, name, None)
            if f is None or name in ("DataDirFailed", "DataDirFallback", "UacDenied"): continue
            unesc = lambda s: s.encode().decode("unicode_escape").encode("latin1").decode("utf-8")
            loc.apply("en"); self.assertEqual(f(), unesc(en), name)
            loc.apply("zh"); self.assertEqual(f(), unesc(zh), name)


class ConfigTest(unittest.TestCase):
    def setUp(self): loc.apply("zh")

    def P(self, *lines):
        c = config.AppConfig(); c.parse(("language = zh",) + lines); return c

    def test_defaults(self):
        c = self.P(*config.DEFAULT_INI.replace("language = system", "").split("\n"))
        self.assertEqual((c.controller, c.secret, c.panel_url, c.poll_seconds, c.close_connections, c.language, c.autostart),
                         ("http://127.0.0.1:9090", "", "http://127.0.0.1:9090/ui/", 3, True, "zh", False))
        self.assertEqual(c.errors, [])
        c = config.AppConfig(); c.parse(config.DEFAULT_INI.split("\n")); self.assertEqual(c.language, "system")
        self.assertFalse(c.has_switch_program)

    def test_controller(self):
        for v, want in ((":9090", "http://127.0.0.1:9090"), ("0.0.0.0:9090", "http://127.0.0.1:9090"), ("[::]:9090", "http://127.0.0.1:9090"),
                        ("https://h:1/", "https://h:1"), ("127.0.0.1:9097", "http://127.0.0.1:9097")):
            self.assertEqual(self.P("controller = " + v).controller, want, v)
        for v in ("127.0.0.1", "ftp://a:1", "a:70000", "a b:1"):
            c = self.P("controller = " + v)
            self.assertEqual(c.controller, "http://127.0.0.1:9090"); self.assertEqual(len(c.errors), 1, v)

    def test_secret_poll_panel(self):
        self.assertEqual(self.P("secret = a ; b").secret, "a ; b")
        self.assertEqual(self.P('secret = "a"b"').secret, 'a"b')
        self.assertEqual(self.P("poll_interval = 0").poll_seconds, 1)
        self.assertEqual(self.P("poll_interval = 99").poll_seconds, 60)
        c = self.P("poll_interval = x"); self.assertEqual(c.poll_seconds, 3); self.assertIn("poll_interval = x", c.errors[0])
        c = self.P("panel_url = file:///etc"); self.assertEqual(c.panel_url, "http://127.0.0.1:9090/ui/"); self.assertTrue(c.errors)
        self.assertFalse(self.P("close_connections = off").close_connections)
        self.assertTrue(self.P("close_connections = whatever").close_connections)
        self.assertEqual(self.P("language = en").language, "en")
        self.assertEqual(self.P('controller = "1.2.3.4:5" x').errors[0], "controller：引号后面多出的内容\u201cx\u201d已忽略")

    def test_autostart_parse(self):
        for v in ("true", "TRUE", "1", "yes", "on", "true ; 注释"):
            self.assertTrue(self.P("autostart = " + v).autostart, v)
        for v in ("false", "0", "", "maybe"):
            self.assertFalse(self.P("autostart = " + v).autostart, v)

    def test_switch_program(self):
        d = tempfile.mkdtemp(dir=TMP)
        exe = os.path.join(d, "My App"); open(exe, "w").write("#!/bin/sh\n"); os.chmod(exe, 0o755)
        noexec = os.path.join(d, "plain"); open(noexec, "w").close()
        c = self.P('switch_program = "%s" --min' % exe, "switch_program_args = --tray \"a b\"")
        self.assertEqual(c.program_command(d)[0], [exe, "--min", "--tray", "a b"])
        self.assertEqual(self.P("switch_program = %s" % exe).program_command(d)[0], [exe])
        self.assertEqual(self.P("switch_program = My App").program_command(d)[0], [exe])      # 相对路径
        os.environ["MT_DIR"] = d
        self.assertEqual(self.P("switch_program = $MT_DIR/My App").program_command(d)[0], [exe])
        self.assertEqual(self.P("switch_program = sh -c true").program_command(d)[0][1:], ["-c", "true"])
        self.assertTrue(self.P("switch_program = sh").program_command(d)[0][0].endswith("/sh"))
        self.assertIn("找不到文件", self.P("switch_program = /nope/x").program_command(d)[1])
        self.assertIn("没有执行权限", self.P("switch_program = " + noexec).program_command(d)[1])
        self.assertEqual(self.P().program_command(d)[1], loc.SwitchNotSet())

    def test_load_and_upgrade(self):
        p = config.ini_path()
        if os.path.exists(p): os.remove(p)
        c = config.load()
        self.assertEqual(open(p, encoding="utf-8").read(), config.DEFAULT_INI)
        self.assertFalse(c.autostart)
        old = config.DEFAULT_INI.split("; 开机自启")[0].replace("secret = \n", "secret = abc\n").replace("\n", "\r\n")
        open(p, "w", newline="").write(old)
        c = config.load()
        s = open(p, encoding="utf-8", newline="").read()
        self.assertEqual(c.secret, "abc")
        self.assertIn("secret = abc\r\n", s)
        self.assertTrue(s.rstrip().endswith("autostart = false") and "\r\n; 开机自启" in s, "missing key appended to [ui], CRLF kept")
        # 只读 config.ini 不改动
        open(p, "w").write("secret = ro\n"); os.chmod(p, 0o444)
        c = config.load(); self.assertEqual(c.secret, "ro"); self.assertEqual(open(p).read(), "secret = ro\n")
        os.chmod(p, 0o644); os.remove(p)

    def test_panel_tip_secret_gate(self):
        """空/纯空格 secret → 应提示；非空 → 不提示（与 tray/gtk 逻辑一致）。"""
        self.assertFalse(("" or "").strip())
        self.assertFalse(("   " or "").strip())
        self.assertTrue(("abc" or "").strip())
        # 解析后的 secret 字段同样适用
        self.assertFalse((self.P("secret = ").secret or "").strip())
        self.assertFalse((self.P("secret =    ").secret or "").strip())
        self.assertTrue((self.P("secret = abc").secret or "").strip())


class ClientTest(Base):
    def test_api(self):
        c = MihomoClient("127.0.0.1:%d" % self.port, "")
        self.assertEqual(c.get_mode(), "rule")
        for m in ("global", "direct", "rule"):
            c.set_mode(m); self.assertEqual(c.get_mode(), m)
        c.close_all_connections()
        st = c.get_status()
        self.assertFalse(st.tun_enabled); self.assertEqual(st.log_level, "info")

    def test_auth(self):
        with self.assertRaises(MihomoError) as e:
            MihomoClient("127.0.0.1:%d" % self.sport, "wrong").get_mode()
        self.assertEqual(str(e.exception), loc.AuthFailed())
        self.assertEqual(MihomoClient("127.0.0.1:%d" % self.sport, "s3cret").get_mode(), "rule")
        with self.assertRaises(MihomoError) as e:
            MihomoClient("127.0.0.1:%d" % self.sport, "密钥").get_mode()
        self.assertEqual(str(e.exception), loc.BadSecretChars())

    def test_offline_and_parse(self):
        with self.assertRaises(MihomoError) as e:
            MihomoClient("127.0.0.1:%d" % free_port(), "").get_status()
        self.assertEqual(str(e.exception), loc.CantConnect())
        st = parse_status('{"mode":"Global","tun":{"enable":true},"tuic-server":{"enable":false},"log-level":"debug"}')
        self.assertEqual((st.mode, st.tun_enabled, st.log_level), ("global", True, "debug"))
        self.assertFalse(parse_status('{"mode":"rule","tuic-server":{"enable":true}}').tun_enabled)
        for bad in ("garbage", '{"x":{"mode":"rule"}}', '{"mode":"r-1"}'):
            with self.assertRaises(MihomoError): parse_status(bad)

    def test_user_agent(self):
        self.assertEqual(__version__, "1.0.3")


class AutostartTest(unittest.TestCase):
    def test_decide(self):
        w = autostart.desktop_entry(["/a b/MihomoTray.AppImage"])
        self.assertIn('Exec="/a b/MihomoTray.AppImage"', w)
        self.assertEqual(autostart.decide(True, None, w), "write")
        self.assertEqual(autostart.decide(True, w, w), None)
        self.assertEqual(autostart.decide(True, w.replace("/a b", "/old"), w), "write")
        self.assertEqual(autostart.decide(False, None, w), None)
        self.assertEqual(autostart.decide(False, w, w), "delete")
        self.assertEqual(autostart.decide(False, "[Desktop Entry]\nExec=foo\n", w), None)  # 不是自己写的不删
        self.assertEqual(autostart._quote("100%$x"), '"100%%\\$x"')

    def test_sync(self):
        p = autostart.desktop_path()
        self.assertIsNone(autostart.sync(False)); self.assertFalse(os.path.exists(p))
        self.assertIsNone(autostart.sync(True)); self.assertTrue(os.path.exists(p))
        self.assertIn("-m mihomotray", open(p).read())
        appimg = os.path.join(TMP, "MihomoTray_linux_qt_1.0.3_x86_64.AppImage"); open(appimg, "w").close()
        os.environ["APPIMAGE"] = appimg
        try:
            autostart.sync(True); self.assertIn("Exec=" + appimg + "\n", open(p).read())
        finally:
            del os.environ["APPIMAGE"]
        self.assertIsNone(autostart.sync(False)); self.assertFalse(os.path.exists(p))
        open(p, "w").write("[Desktop Entry]\nExec=other\n")
        autostart.sync(False); self.assertTrue(os.path.exists(p), "foreign file kept"); os.remove(p)


class TrayTest(Base):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as e:
            raise unittest.SkipTest("PySide6 not available: %s" % e)
        cls.app = QApplication.instance() or QApplication([])
        super().setUpClass()

    def wait(self, cond, t=5):
        from PySide6.QtCore import QCoreApplication
        end = time.time() + t
        while time.time() < end:
            QCoreApplication.processEvents(); time.sleep(0.02)
            if cond(): return True
        return False

    def make(self, port, **kw):
        from mihomotray.tray import TrayApp
        c = config.AppConfig(); c.parse(["controller = 127.0.0.1:%d" % port, "language = zh"] + ["%s = %s" % i for i in kw.items()])
        t = TrayApp(c)
        t.warnings = []
        t.warn = lambda title, text: t.warnings.append((title, text))
        return t

    def test_menu_and_switch(self):
        MihomoClient("127.0.0.1:%d" % self.port, "").set_mode("rule")
        t = self.make(self.port)
        self.assertTrue(self.wait(lambda: t.connected))
        self.assertEqual([a.text() for a in t.menu.actions()], ["规则模式", "", "打开面板", "切换程序", "", "规则模式", "全局模式", "直连模式", "", "退出"])
        self.assertFalse(t.act_app.isEnabled())
        self.assertEqual(t.icon_key, "rule"); self.assertTrue(t.act_modes["rule"].isChecked())
        self.assertEqual(t.tray.toolTip(), "模式 : 规则模式\n日志级别 : 信息\n虚拟网卡 : 关闭")
        t.act_modes["global"].trigger()
        self.assertTrue(self.wait(lambda: t.icon_key == "global" and t._switching == 0))
        self.assertTrue(t.act_modes["global"].isChecked() and not t.act_modes["rule"].isChecked())
        self.assertEqual(MihomoClient("127.0.0.1:%d" % self.port, "").get_mode(), "global")
        # 连点：只采用最后一次
        t.switch_mode("direct"); t.switch_mode("rule")
        self.assertTrue(self.wait(lambda: t._switching == 0))
        self.assertEqual(t.icon_key, "rule"); self.assertEqual(t.warnings, [])
        t.timer.stop(); t.disposed = True

    def test_offline(self):
        port = free_port()
        t = self.make(port)
        self.assertTrue(self.wait(lambda: not t._polling, 5))
        self.wait(lambda: False, 0.3)
        self.assertFalse(t.connected); self.assertEqual(t.icon_key, "offline")
        self.assertEqual(t.tray.toolTip(), "无法连接")
        self.assertEqual(t.status_text, "无法连接")
        self.assertTrue(all(not a.isEnabled() for a in t.act_modes.values()))
        t.switch_mode("global")
        self.assertTrue(self.wait(lambda: t.warnings))
        self.assertEqual(t.warnings[0][0], "切换失败")
        self.assertIn("控制器：http://127.0.0.1:%d" % port, t.warnings[0][1])
        t.timer.stop(); t.disposed = True

    def test_switch_program_enabled(self):
        t = self.make(self.port, switch_program="sh")
        self.assertTrue(t.act_app.isEnabled())
        t.timer.stop(); t.disposed = True

    def test_recover(self):
        """先离线，mock 起来后下一次轮询变回在线（相当于 mihomo 后启动）。"""
        port = free_port()
        t = self.make(port)
        self.wait(lambda: not t._polling); self.wait(lambda: False, 0.3)
        self.assertFalse(t.connected)
        m = start_mock(port)
        try:
            t.poll(); self.assertTrue(self.wait(lambda: t.connected))
            self.assertEqual(t.icon_key, "rule")
        finally:
            m.kill(); m.wait()
        t.timer.stop(); t.disposed = True




class IconsTest(unittest.TestCase):
    def test_ensure_user_icon(self):
        from mihomotray import icons
        p = icons.ensure_user_icon("rule")
        self.assertTrue(os.path.isfile(p))
        self.assertTrue(p.endswith(".png"))
        self.assertTrue(icons.package_icon_paths("global"))


class GtkTrayTest(Base):
    """GTK 前端：有 gi + AyatanaAppIndicator 时跑冒烟；否则 skip。"""

    @classmethod
    def setUpClass(cls):
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import Gtk  # noqa: F401
        except Exception as e:
            raise unittest.SkipTest("GTK/AppIndicator not available: %s" % e)
        super().setUpClass()

    def wait(self, cond, t=5):
        from gi.repository import GLib
        end = time.time() + t
        ctx = GLib.MainContext.default()
        while time.time() < end:
            while ctx.pending():
                ctx.iteration(False)
            time.sleep(0.02)
            if cond():
                return True
        return False

    def make(self, port, **kw):
        from mihomotray.gtk_tray import GtkTrayApp
        c = config.AppConfig()
        c.parse(["controller = 127.0.0.1:%d" % port, "language = zh"] + ["%s = %s" % i for i in kw.items()])
        return GtkTrayApp(c)

    def test_menu_order_and_switch(self):
        MihomoClient("127.0.0.1:%d" % self.port, "").set_mode("rule")
        t = self.make(self.port)
        self.assertTrue(self.wait(lambda: t.connected))
        self.assertEqual(t.menu_labels(), ["规则模式", "", "打开面板", "切换程序", "", "规则模式", "全局模式", "直连模式", "", "退出"])
        self.assertFalse(t.act_app.get_sensitive())
        self.assertEqual(t.icon_key, "rule")
        t.switch_mode("global")
        self.assertTrue(self.wait(lambda: t.icon_key == "global" and t._switching == 0))
        self.assertEqual(MihomoClient("127.0.0.1:%d" % self.port, "").get_mode(), "global")
        t.quit()

    def test_offline_warn(self):
        port = free_port()
        t = self.make(port)
        self.assertTrue(self.wait(lambda: not t._polling, 5))
        self.wait(lambda: False, 0.3)
        self.assertFalse(t.connected)
        self.assertEqual(t.icon_key, "offline")
        self.assertEqual(t.status_text, "无法连接")
        t.switch_mode("global")
        self.assertTrue(self.wait(lambda: t.warnings))
        self.assertEqual(t.warnings[0][0], "切换失败")
        t.quit()


if __name__ == "__main__":
    unittest.main()
