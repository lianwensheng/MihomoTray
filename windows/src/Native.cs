using System;
using System.Runtime.InteropServices;

namespace MihomoTray
{
    internal static class Native
    {
        [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct OSVERSIONINFOEX
        {
            public int dwOSVersionInfoSize, dwMajorVersion, dwMinorVersion, dwBuildNumber, dwPlatformId;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string szCSDVersion;
            public ushort wServicePackMajor, wServicePackMinor, wSuiteMask;
            public byte wProductType, wReserved;
        }
        [DllImport("ntdll.dll", CharSet = CharSet.Unicode)]
        private static extern int RtlGetVersion(ref OSVERSIONINFOEX v);

        private static int _build = -1;
        public static int WindowsBuild
        {
            get
            {
                if (_build < 0)
                {
                    try
                    {
                        var v = new OSVERSIONINFOEX();
                        v.dwOSVersionInfoSize = Marshal.SizeOf(typeof(OSVERSIONINFOEX));
                        _build = RtlGetVersion(ref v) == 0 ? v.dwBuildNumber : 0;
                    }
                    catch { _build = 0; }
                }
                return _build;
            }
        }
        // ---- 原生菜单深色模式（未公开的 uxtheme 序号导出，Win10 1903+ / Win11）----
        // 135 = SetPreferredAppMode(0 Default, 1 AllowDark, 2 ForceDark, 3 ForceLight)
        // 133 = AllowDarkModeForWindow，136 = FlushMenuThemes
        [DllImport("uxtheme.dll", EntryPoint = "#135")] private static extern int SetPreferredAppMode(int mode);
        [DllImport("uxtheme.dll", EntryPoint = "#133")] private static extern bool AllowDarkModeForWindow(IntPtr hwnd, bool allow);
        [DllImport("uxtheme.dll", EntryPoint = "#136")] private static extern void FlushMenuThemes();

        private static int _appMode = -1;

        /// <summary>
        /// 设置原生弹出菜单的深浅色：light = 不改动（与 FlClash 原版一致，系统默认浅色菜单），
        /// system = 跟随系统“应用”深浅色，dark = 强制深色。旧系统（1903 之前）静默忽略。
        /// </summary>
        public static void SetMenuTheme(string theme, IntPtr owner)
        {
            if (WindowsBuild < 18362) return;
            int mode = theme == "dark" ? 2 : theme == "system" ? 1 : 0;
            if (mode == 0 && _appMode <= 0) return;   // 从未改过就保持系统默认，和 FlClash 完全相同
            try
            {
                if (mode != _appMode)
                {
                    SetPreferredAppMode(mode == 0 ? 3 : mode);
                    _appMode = mode;
                }
                if (owner != IntPtr.Zero) AllowDarkModeForWindow(owner, mode != 0);
                FlushMenuThemes();
            }
            catch { }
        }

    }
}
