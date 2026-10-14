using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace MihomoTray
{
    /// <summary>
    /// 仿 FlClash 的托盘右键菜单。
    /// FlClash（v0.8.99，plugins/tray/windows/tray_plugin.cpp）在 Windows 上用的是 Win32 原生弹出菜单：
    /// CreatePopupMenu + AppendMenuW（MF_STRING / MF_SEPARATOR / MF_CHECKED），
    /// 右键松开（WM_RBUTTONUP）时 SetForegroundWindow → TrackPopupMenu(TPM_BOTTOMALIGN | TPM_LEFTALIGN |
    /// TPM_RETURNCMD | TPM_RIGHTBUTTON，鼠标位置) → PostMessage(WM_NULL)。
    /// 当前模式用普通对勾（MF_CHECKED，不是 MFT_RADIOCHECK 圆点）表示。这里照搬同样的调用。
    /// 外观完全由 Windows 绘制：Win11 自带圆角/阴影，Win10 是经典直角菜单。
    /// </summary>
    public sealed class FlClashMenu : IDisposable
    {
        public sealed class Entry
        {
            public string Text;          // null = 分隔线
            public bool Checkable, Checked, Enabled = true;
            public Action OnClick;
        }

        private readonly OwnerWindow _owner = new OwnerWindow();

        /// <summary>每次弹出前重新生成菜单（FlClash 也是每次状态变化就重建整张菜单）。</summary>
        public Func<List<Entry>> Build;
        /// <summary>light / dark / system，见 Native.SetMenuTheme。</summary>
        public string Theme = "light";

        public FlClashMenu()
        {
            _owner.CreateHandle(new CreateParams { Caption = "MihomoTrayMenuOwner" });
        }

        public void Show()
        {
            if (Build == null) return;
            List<Entry> entries = Build();
            Native.SetMenuTheme(Theme, _owner.Handle);

            Action chosen = null;
            IntPtr menu = NativeMenu.CreatePopupMenu();
            if (menu == IntPtr.Zero) return;
            var actions = new Dictionary<int, Action>();
            try
            {
                int id = 1;
                foreach (var e in entries)
                {
                    if (e.Text == null)
                    {
                        NativeMenu.AppendMenuW(menu, NativeMenu.MF_SEPARATOR, UIntPtr.Zero, null);
                        continue;
                    }
                    uint flags = NativeMenu.MF_STRING;
                    if (!e.Enabled) flags |= NativeMenu.MF_GRAYED;
                    if (e.Checkable) flags |= e.Checked ? NativeMenu.MF_CHECKED : NativeMenu.MF_UNCHECKED;
                    NativeMenu.AppendMenuW(menu, flags, new UIntPtr((uint)id), e.Text);
                    if (e.OnClick != null) actions[id] = e.OnClick;
                    id++;
                }

                NativeMenu.POINT pt;
                NativeMenu.GetCursorPos(out pt);
                // 不先 SetForegroundWindow，点菜单外面菜单不会消失（MS KB135788）
                NativeMenu.SetForegroundWindow(_owner.Handle);
                int cmd = NativeMenu.TrackPopupMenu(menu,
                    NativeMenu.TPM_BOTTOMALIGN | NativeMenu.TPM_LEFTALIGN | NativeMenu.TPM_RETURNCMD | NativeMenu.TPM_RIGHTBUTTON,
                    pt.X, pt.Y, 0, _owner.Handle, IntPtr.Zero);
                NativeMenu.PostMessageW(_owner.Handle, NativeMenu.WM_NULL, IntPtr.Zero, IntPtr.Zero);

                Action a;
                if (cmd != 0 && actions.TryGetValue(cmd, out a)) chosen = a;
            }
            finally
            {
                NativeMenu.DestroyMenu(menu);
            }
            // 菜单完全关闭、托盘事件处理结束后再执行所选动作（例如“退出”会销毁托盘图标）
            if (chosen != null)
            {
                var ctx = System.Threading.SynchronizationContext.Current;
                if (ctx != null) ctx.Post(delegate { chosen(); }, null);
                else chosen();
            }
        }

        public void Dispose()
        {
            if (_owner.Handle != IntPtr.Zero) _owner.DestroyHandle();
        }

        /// <summary>菜单的属主窗口（不可见的顶层窗口），TrackPopupMenu 需要它。</summary>
        private sealed class OwnerWindow : NativeWindow { }
    }

    internal static class NativeMenu
    {
        public const uint MF_STRING = 0x0000, MF_GRAYED = 0x0001, MF_UNCHECKED = 0x0000, MF_CHECKED = 0x0008,
                          MF_SEPARATOR = 0x0800;
        public const uint TPM_LEFTALIGN = 0x0000, TPM_RIGHTBUTTON = 0x0002, TPM_BOTTOMALIGN = 0x0020,
                          TPM_RETURNCMD = 0x0100;
        public const uint WM_NULL = 0x0000;

        [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }

        [DllImport("user32.dll", SetLastError = true)] public static extern IntPtr CreatePopupMenu();
        [DllImport("user32.dll")] public static extern bool DestroyMenu(IntPtr hMenu);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern bool AppendMenuW(IntPtr hMenu, uint uFlags, UIntPtr uIDNewItem, string lpNewItem);
        [DllImport("user32.dll")]
        public static extern int TrackPopupMenu(IntPtr hMenu, uint uFlags, int x, int y, int nReserved, IntPtr hWnd, IntPtr prcRect);
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT pt);
        [DllImport("user32.dll")] public static extern bool PostMessageW(IntPtr hWnd, uint msg, IntPtr w, IntPtr l);
    }
}
