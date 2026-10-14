using System;
using System.Windows.Forms;
using Microsoft.Win32;

namespace MihomoTray
{
    /// <summary>
    /// 开机自启：HKCU\Software\Microsoft\Windows\CurrentVersion\Run 下的 MihomoTray 值（= 带引号的 exe 路径）。
    /// 每次启动按 config.ini 的 autostart 同步：true 写入/更新，false 只删除自己的 MihomoTray 值，其它启动项不碰。
    /// </summary>
    public static class Autostart
    {
        public const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
        public const string ValueName = "MihomoTray";

        public enum Action { None, Write, Delete }

        public static string CommandFor(string exePath) { return "\"" + exePath + "\""; }

        /// <summary>决策逻辑（可单测）：current 为注册表里现有的值，没有则 null。</summary>
        public static Action Decide(bool enabled, string current, string exePath)
        {
            string want = CommandFor(exePath);
            if (enabled) return string.Equals(current, want, StringComparison.OrdinalIgnoreCase) ? Action.None : Action.Write;
            return current == null ? Action.None : Action.Delete;
        }

        /// <summary>成功返回 null，失败返回原因。</summary>
        public static string Sync(bool enabled)
        {
            try
            {
                string exe = Application.ExecutablePath;
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(RunKey))
                {
                    if (k == null) return RunKey;
                    string cur = k.GetValue(ValueName) as string;
                    switch (Decide(enabled, cur, exe))
                    {
                        case Action.Write: k.SetValue(ValueName, CommandFor(exe), RegistryValueKind.String); break;
                        case Action.Delete: k.DeleteValue(ValueName, false); break;
                    }
                }
                return null;
            }
            catch (Exception ex) { return ex.Message; }
        }
    }
}
