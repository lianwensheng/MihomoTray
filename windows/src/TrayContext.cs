using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;

namespace MihomoTray
{
    public sealed class TrayContext : ApplicationContext
    {
        private static readonly string[] Modes = { "rule", "global", "direct" };
        private readonly AppConfig _cfg;
        private readonly MihomoClient _client;
        private readonly SynchronizationContext _ui;
        private readonly NotifyIcon _tray;
        private DateTime _lastPanelOpen = DateTime.MinValue;
        private readonly FlClashMenu _menu;           // Windows 原生右键菜单（每次弹出时重建）
        private readonly Dictionary<string, Icon> _icons = new Dictionary<string, Icon>();
        private readonly System.Windows.Forms.Timer _timer;
        private int _polling;          // 0/1，防止请求堆积
        private string _mode;          // 最近一次读到的模式
        private bool _connected;
        private string _statusText = Loc.Disconnected;  // 悬停 / 菜单灰字短状态
        private bool _disposed;        // Quit() 之后为 true，晚到的回调直接忽略
        private int _switchSeq;        // 每次切换模式 +1，只采用最新一次切换的结果
        private int _switching;        // 正在切换时丢弃轮询结果，避免旧模式把新模式覆盖回去

        public TrayContext(AppConfig cfg)
        {
            _cfg = cfg;
            _client = new MihomoClient(cfg.Controller, cfg.Secret);
            _ui = SynchronizationContext.Current;

            foreach (var n in new[] { "rule", "global", "direct", "offline" }) _icons[n] = LoadIcon(n);

            _menu = new FlClashMenu { Theme = cfg.Theme, Build = BuildMenuEntries };

            _tray = new NotifyIcon
            {
                Icon = _icons["offline"],
                Text = TrayTip.Offline,     // 第一次轮询成功前显示“未连接”
                Visible = true
            };

            // 左键单击图标直接打开面板（800ms 内重复点击只打开一次，避免双击开两个标签页）
            _tray.MouseClick += delegate(object sender, MouseEventArgs e)
            {
                if (e.Button != MouseButtons.Left) return;
                if ((DateTime.UtcNow - _lastPanelOpen).TotalMilliseconds < 800) return;
                _lastPanelOpen = DateTime.UtcNow;
                OpenPanel();
            };

            // 和 FlClash 一样在右键松开（WM_RBUTTONUP）时弹出原生菜单
            _tray.MouseUp += delegate(object sender, MouseEventArgs e)
            {
                if (e.Button != MouseButtons.Right) return;
                Poll();
                _menu.Show();
            };

            _timer = new System.Windows.Forms.Timer { Interval = cfg.PollSeconds * 1000 };
            _timer.Tick += delegate { Poll(); };
            _timer.Start();
            Poll();

            string autoErr = Autostart.Sync(cfg.Autostart);
            if (autoErr != null) cfg.Errors.Add(Loc.AutostartFailed + (Loc.En ? ": " : "：") + autoErr);

            if (cfg.Errors.Count > 0)
                Warn(Loc.BadConfig, string.Join("\n", cfg.Errors.ToArray()));
        }

        /// <summary>
        /// 托盘图标：优先用 Data\Icons\tray_xxx.ico（可以替换成自己的图标），
        /// 文件不存在时先把编译进 exe 的原始图标复制一份过去；文件损坏或读不了就用内置原始图标。
        /// </summary>
        private static Icon LoadIcon(string name)
        {
            string file = "tray_" + name + ".ico";
            string path = Path.Combine(AppConfig.IconsDir, file);
            try
            {
                if (!File.Exists(path))
                {
                    byte[] data = ReadEmbedded(file);
                    if (data != null)
                    {
                        Directory.CreateDirectory(AppConfig.IconsDir);
                        File.WriteAllBytes(path, data);
                    }
                }
                if (File.Exists(path))
                {
                    long len = new FileInfo(path).Length;
                    if (len > 2 * 1024 * 1024) throw new IOException("图标超过 2MB");  // C5
                    byte[] bytes = File.ReadAllBytes(path);   // 先读进内存，不锁住文件，方便用户替换
                    using (var ms = new MemoryStream(bytes))
                    {
                        Icon tmp = new Icon(ms, SystemInformation.SmallIconSize);
                        try
                        {
                            // C4：头部合法但内部损坏时，构造可能不抛异常，用 ToBitmap 提前验证
                            using (Bitmap bmp = tmp.ToBitmap()) { }
                            Icon clone = (Icon)tmp.Clone();  // D1：Clone 后立刻 Dispose 临时句柄
                            tmp.Dispose();
                            return clone;
                        }
                        catch
                        {
                            tmp.Dispose();
                            throw;
                        }
                    }
                }
            }
            catch { }
            try
            {
                byte[] data = ReadEmbedded(file);
                if (data != null)
                    using (var ms = new MemoryStream(data))
                        return new Icon(ms, SystemInformation.SmallIconSize);
            }
            catch { }
            return (Icon)SystemIcons.Application.Clone();   // 资源缺失时退回系统默认图标，不至于启动就崩
        }

        private static byte[] ReadEmbedded(string resName)
        {
            using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream(resName))
            {
                if (s == null) return null;
                var ms = new MemoryStream();
                s.CopyTo(ms);
                return ms.ToArray();
            }
        }

        /// <summary>右键菜单内容：打开面板、切换程序 | 三个模式（当前模式打对勾）| 退出。</summary>
        private List<FlClashMenu.Entry> BuildMenuEntries()
        {
            var list = new List<FlClashMenu.Entry>();
            list.Add(new FlClashMenu.Entry { Text = _statusText, Enabled = false });
            list.Add(new FlClashMenu.Entry());
            list.Add(new FlClashMenu.Entry { Text = Loc.OpenPanel, OnClick = OpenPanel });
            list.Add(new FlClashMenu.Entry { Text = Loc.SwitchProgram, Enabled = _cfg.HasSwitchProgram, OnClick = LaunchSwitchProgram });
            list.Add(new FlClashMenu.Entry());
            foreach (var m in Modes)
            {
                string mode = m;
                string label = m == "rule" ? Loc.ModeRule : m == "global" ? Loc.ModeGlobal : Loc.ModeDirect;
                list.Add(new FlClashMenu.Entry
                {
                    Text = label, Checkable = true, Checked = _connected && _mode == m,
                    Enabled = _connected, OnClick = delegate { SwitchMode(mode); }
                });
            }
            list.Add(new FlClashMenu.Entry());
            list.Add(new FlClashMenu.Entry { Text = Loc.Exit, OnClick = Quit });
            return list;
        }

        // ---- 轮询 ----
        private void Poll()
        {
            if (Interlocked.CompareExchange(ref _polling, 1, 0) != 0) return;
            int seqAtStart = Volatile.Read(ref _switchSeq);   // 轮询期间若发生过切换，结果作废
            ThreadPool.QueueUserWorkItem(delegate
            {
                MihomoStatus st = null; Exception err = null;
                try { st = _client.GetStatus(); }
                catch (Exception ex) { err = ex; }
                finally { Interlocked.Exchange(ref _polling, 0); }
                _ui.Post(delegate
                {
                    // 切换进行中，或者这次轮询发出后又切换过模式：结果可能是旧的，丢弃
                    if (Volatile.Read(ref _switching) > 0 || seqAtStart != Volatile.Read(ref _switchSeq)) return;
                    UpdateState(st, err);
                }, null);
            });
        }

        private void UpdateState(MihomoStatus st, Exception err)
        {
            if (_disposed) return;
            string mode = st == null ? null : st.Mode;
            if (err != null)
            {
                _connected = false;
                _statusText = ShortStatus(err);
                _tray.Icon = _icons["offline"];
                SetTip(_statusText);
            }
            else
            {
                _connected = true;
                _mode = mode;
                string key = (mode == "rule" || mode == "global" || mode == "direct") ? mode : "rule";
                _statusText = key == "rule" ? Loc.ModeRule : key == "global" ? Loc.ModeGlobal : Loc.ModeDirect;
                _tray.Icon = _icons[key];
                SetTip(TrayTip.For(true, st.Mode, st.TunEnabled, st.LogLevel));
            }
        }

        /// <summary>轮询失败时的短状态文案（悬停 ≤63 字 / 菜单灰字）。</summary>
        private static string ShortStatus(Exception err)
        {
            if (err == null) return Loc.Disconnected;
            string m = err.Message ?? "";
            if (m == Loc.AuthFailed) return Loc.StatusAuthFailed;
            if (m == Loc.ControllerTimeout) return Loc.StatusTimeout;
            if (m == Loc.CantConnect) return Loc.StatusCantConnect;
            return Loc.Disconnected;
        }

        private void SetTip(string t)
        {
            if (_disposed) return;
            if (t.Length > 63) t = t.Substring(0, 63);
            if (_tray.Text != t) _tray.Text = t;
        }

        // ---- 动作 ----
        private void SwitchMode(string mode)
        {
            if (_disposed) return;
            int seq = Interlocked.Increment(ref _switchSeq);
            Interlocked.Increment(ref _switching);
            ThreadPool.QueueUserWorkItem(delegate
            {
                Exception err = null; MihomoStatus now = null;
                try
                {
                    _client.SetMode(mode);
                    if (_cfg.CloseConnections)
                    {
                        try { _client.CloseAllConnections(); } catch { }
                    }
                    now = _client.GetStatus();
                }
                catch (Exception ex) { err = ex; }
                _ui.Post(delegate
                {
                    Interlocked.Decrement(ref _switching);
                    if (_disposed || seq != Volatile.Read(ref _switchSeq)) return;   // 已经有更新的一次切换
                    if (err != null)
                    {
                        UpdateState(null, err);
                        Warn(Loc.SwitchFailed, err.Message + "\n" + Loc.ControllerLabel + _cfg.Controller);
                    }
                    else UpdateState(now, null);
                }, null);
            });
        }

        private void OpenPanel()
        {
            MaybeShowPanelTip();
            string url = _cfg.PanelUrl;
            StartShell(new ProcessStartInfo(url) { UseShellExecute = true }, delegate(Exception ex)
            {
                Warn(Loc.CantOpenPanel, ex.Message + "\n" + url);
            });
        }

        /// <summary>首次打开面板：气泡提示实际 panel_url，旁路 .panel_tip_shown 只提示一次（菜单/左键共用）。</summary>
        private void MaybeShowPanelTip()
        {
            if (!AppConfig.TryClaimPanelTip()) return;
            Info(Loc.OpenPanel, Loc.PanelTipBody(_cfg.PanelUrl));
        }

        /// <summary>启动 config.ini 里 switch_program 指定的程序（ShellExecute，.exe / .lnk 都可以）。</summary>
        private void LaunchSwitchProgram()
        {
            if (!_cfg.HasSwitchProgram)
            {
                Warn(Loc.CantOpenApp, Loc.SwitchNotSet);
                return;
            }
            string path = AppConfig.ResolveProgramPath(_cfg.SwitchProgram, AppConfig.ExeDir);
            if (path == null || !File.Exists(path))
            {
                Warn(Loc.CantOpenApp, Loc.FileNotFound(path ?? _cfg.SwitchProgram));
                return;
            }
            var psi = new ProcessStartInfo(path) { UseShellExecute = true };
            string args = _cfg.EffectiveSwitchArgs;
            if (args.Length > 0) psi.Arguments = args;
            string dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir)) psi.WorkingDirectory = dir;
            StartShell(psi, delegate(Exception ex)
            {
                var w = ex as System.ComponentModel.Win32Exception;
                Warn(Loc.CantOpenApp, w != null && w.NativeErrorCode == 1223 ? Loc.UacDenied : ex.Message + "\n" + path);
            });
        }

        /// <summary>
        /// 在单独的 STA 线程里 ShellExecute：等 UAC 确认、解析 .lnk 或慢速磁盘时不会卡住托盘。
        /// 出错时把异常交回 UI 线程处理；返回的 Process 立即释放，不多占进程句柄。
        /// </summary>
        private void StartShell(ProcessStartInfo psi, Action<Exception> onError)
        {
            var t = new Thread(delegate()
            {
                try { using (Process.Start(psi)) { } }
                catch (Exception ex)
                {
                    _ui.Post(delegate { if (!_disposed) onError(ex); }, null);
                }
            });
            t.IsBackground = true;
            t.SetApartmentState(ApartmentState.STA);
            t.Start();
        }

        private void Warn(string title, string text)
        {
            if (_disposed) return;
            if (text.Length > 250) text = text.Substring(0, 247) + "...";
            _tray.ShowBalloonTip(4000, title, text, ToolTipIcon.Warning);
        }

        private void Info(string title, string text)
        {
            if (_disposed) return;
            if (text.Length > 250) text = text.Substring(0, 247) + "...";
            _tray.ShowBalloonTip(4000, title, text, ToolTipIcon.Info);
        }

        /// <summary>每一步单独 try，无论哪一步出错最后都一定 ExitThread，进程不会留在后台。</summary>
        private void Quit()
        {
            if (_disposed) return;
            _disposed = true;
            try
            {
                try { _timer.Stop(); _timer.Dispose(); } catch { }
                try { _tray.Visible = false; } catch { }
                try { _tray.Dispose(); } catch { }
                try { _menu.Dispose(); } catch { }
                foreach (var i in _icons.Values) { try { i.Dispose(); } catch { } }
            }
            finally
            {
                ExitThread();
            }
        }
    }
}
