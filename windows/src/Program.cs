// MihomoTray 托盘小工具 - 入口
using System;
using System.Threading;
using System.Windows.Forms;

namespace MihomoTray
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            bool created;
            using (var mutex = new Mutex(true, "Local\\MihomoTrayModeSwitcher_7F3A", out created))
            {
                Loc.Apply("system");
                if (!created)
                {
                    MessageBox.Show(Loc.AlreadyRunning, Loc.AppTitle,
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }
                try { Native.SetProcessDPIAware(); } catch { }
                // 目标框架是 4.5，默认不含 TLS 1.2；https 的 controller 需要它
                try { System.Net.ServicePointManager.SecurityProtocol |= (System.Net.SecurityProtocolType)3072; } catch { }
                // 未处理的异常：提示后直接退出，避免变成“没有托盘图标却还占着单实例”的进程
                Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
                Application.ThreadException += delegate(object s, ThreadExceptionEventArgs e) { Fatal(e.Exception); };
                AppDomain.CurrentDomain.UnhandledException += delegate(object s, UnhandledExceptionEventArgs e) { Fatal(e.ExceptionObject as Exception); };
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                SynchronizationContext.SetSynchronizationContext(new WindowsFormsSynchronizationContext());
                Application.Run(new TrayContext(AppConfig.Load()));
                GC.KeepAlive(mutex);
            }
        }

        private static int _fatal;
        private static void Fatal(Exception ex)
        {
            if (Interlocked.Exchange(ref _fatal, 1) != 0) return;
            try
            {
                MessageBox.Show(Loc.FatalPrefix + (ex == null ? Loc.UnknownError : ex.Message),
                    Loc.AppTitle, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            catch { }
            Environment.Exit(1);
        }
    }
}
