# MihomoTray

Windows 托盘小工具，用来切换 mihomo 代理模式（规则 / 全局 / 直连）。用法见 `README.txt`；英文见 `README_en.txt`。界面文案在 `src/Loc.cs`，`language = system|zh|en`（默认 system；非中文系统走英文）。

## 右键菜单
Windows 原生 Win32 弹出菜单（`src/FlClashMenu.cs`），照 FlClash 的做法实现，当前模式打对勾。仿 Clash Party 的自绘菜单已移除。

FlClash 依据（v0.8.99，2026-10-03 发布）：`lib/common/tray.dart` 生成菜单，模式项是 `TrayMenuCheckbox`（`checked: mode == trayState.mode`），各组之间用 `TrayMenuSeparator`；
Windows 端由自带插件 `plugins/tray/windows/tray_plugin.cpp` 绘制：`CreatePopupMenu` + `AppendMenuW(MF_STRING | MF_CHECKED / MF_SEPARATOR)`，
右键松开（`WM_RBUTTONUP`）时 `SetForegroundWindow` → `TrackPopupMenu(TPM_BOTTOMALIGN | TPM_LEFTALIGN | TPM_RETURNCMD | TPM_RIGHTBUTTON)` → `PostMessage(WM_NULL)`；
左键松开（`WM_LBUTTONUP`）显示主窗口。FlClash 没有调用 uxtheme 的 `SetPreferredAppMode`，所以它的托盘菜单在深色系统下仍是浅色，这里 `theme = light` 与之一致，`system` / `dark` 是额外选项。

## 菜单
打开面板 / 切换程序 | 规则模式 / 全局模式 / 直连模式 | 退出。
“切换程序”启动 `switch_program`（可加 `switch_program_args`），用 ShellExecute，工作目录设为目标所在文件夹；未配置时变灰。
启动时若 `config.ini` 缺少新键（例如从旧版本升级），UTF-8 文件由 `AppConfig.MergeMissingKeys` 插到所属小节末尾；非 UTF-8 文件由 `MissingKeysBlock` + `AsciiOnly` 只在末尾追加 ASCII 内容。已有内容不改，只读文件跳过。

## Layout
- `src/` C# WinForms (.NET Framework 4.x) source
  - `Program.cs` entry, single-instance mutex, DPI awareness
  - `TrayContext.cs` NotifyIcon, menu, polling, mode switching
  - `MihomoClient.cs` REST client (GET/PATCH /configs, DELETE /connections, Bearer secret); `ParseTunEnabled` / `ParseLogLevel` 用 `MiniJson`（只扫最外层 key）读 `tun.enable` 与 `log-level`; `TrayTip` 悬停提示 3 行：模式 / 日志级别 / 虚拟网卡|TUN Mode（未知级别与离线为 —）
  - `FlClashMenu.cs` 原生 Win32 弹出菜单（P/Invoke CreatePopupMenu / AppendMenuW / TrackPopupMenu）
  - `Native.cs` Windows build detection, 原生菜单深色（uxtheme #135/#133/#136）
  - `AssemblyInfo.cs` Win32 版本资源（文件说明 / 文件版本 / 产品名称 / 产品版本 / 版权）
- `icons/` original CFW `tray_normal.ico` + generated `tray_{rule,global,direct,offline}.ico`（编译进 exe，运行时也会复制到 `Data/Icons/` 供自定义替换）
- `dist/Data/` 运行时目录：`config.ini`、`MihomoTray.exe.config`、`Icons/tray_*.ico`
- `tools/make_icons.py` recolors the original icon; `tools/make_preview.py` builds preview.png (menu mock); `tools/make_config.py` writes `dist/Data/config.ini`
- `test/` mock mihomo controller (Python) + API / TUN / config tests (mono)
- `research/` (not in zip) extracted CFW app.asar assets

## Build (Linux)
    sudo apt install mono-devel python3-pil   # Pillow 用于生成图标（tools/make_icons.py）
    ./build.sh          # -> dist/MihomoTray.exe + dist/Data/...

## Build (Windows)
    build.bat           -> dist\MihomoTray.exe + dist\Data\...

## Test (Linux, mono)
    python3 test/mock_mihomo.py 19090 & python3 test/mock_mihomo.py 19091 s3cret &
    mcs -out:test/ApiTest.exe -r:System.Windows.Forms.dll test/ApiTest.cs src/Loc.cs src/MihomoClient.cs src/AppConfig.cs && mono test/ApiTest.exe
    mcs -langversion:5 -out:/tmp/tt.exe -r:System.Windows.Forms.dll test/TunTest.cs src/Loc.cs src/MihomoClient.cs src/AppConfig.cs && mono /tmp/tt.exe
    SLOW_PORT=<慢响应端口> mcs -langversion:5 -out:/tmp/ft.exe -r:System.Windows.Forms.dll test/FixTest.cs src/Loc.cs src/MihomoClient.cs src/AppConfig.cs && mono /tmp/ft.exe   # 第 2 轮报告的回归测试
    mcs -langversion:5 -out:/tmp/st.exe -r:System.Windows.Forms.dll test/StyleTest.cs src/Loc.cs src/AppConfig.cs && mono /tmp/st.exe   # 可加参数：<shipped config.ini> <旧版 config.ini>
    mcs -langversion:5 -out:/tmp/at.exe -r:System.Windows.Forms.dll test/AutostartTest.cs src/Loc.cs src/AppConfig.cs src/Autostart.cs && mono /tmp/at.exe   # 开机自启的解析和决策逻辑

## 版本与 GitHub Actions
版本 **2.1.8**（`src/AssemblyInfo.cs`、User-Agent `MihomoTray/2.1.8`）。
发版只改**产品版本** `AssemblyInformationalVersion`（`x.y.z`）；本地测试只顺延**文件版本** `AssemblyFileVersion` 第 4 段 `N`（从 `0` 起，如 `2.1.8.0` → `2.1.8.1`）。Actions / Release 标签读产品版本，不跟 FileVersion。
`.github/workflows/build-win.yml` 在 `windows-latest` 上用 cmd 跑 `build.bat`（`CI` 环境变量存在时不 `pause`，本地双击不变），产物 `MihomoTray_windows_<版本>.zip` 在 Artifacts 里下载；推 `win-v*` 标签（例如 `win-v2.1.8`）时附到 Release。exe 未签名，首次运行 SmartScreen 可能提示，点「更多信息 → 仍要运行」。
