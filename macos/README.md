# MihomoTray（macOS）1.0.5

菜单栏小工具，用来切换 mihomo 代理模式（规则 / 全局 / 直连）。英文说明见 `README_en.md`。

## 图标

| 模式 | 样式 |
|------|------|
| 规则 | **template 单色** CFW 小猫（保留眼睛），随系统浅/深色自动反色 |
| 全局 | **红色**非 template |
| 直连 | **绿色**非 template |
| 离线 | **灰色**非 template |

资源在 `Assets/`：`tray_{rule,global,direct,offline}.png`（18×18）与 `@2x`（36×36），另有 22pt 变体。预览：`Assets/preview.png`。运行时也可把同名 PNG 放到 `Data/Icons/` 覆盖。

## 菜单

打开面板 / 切换程序 | 规则模式 / 全局模式 / 直连模式（当前打勾）| 退出。  
左键点图标打开 `panel_url`；右键弹出菜单。悬停提示三行：模式 / 日志级别 / 虚拟网卡。

## 配置

`Data/config.ini`（应用旁；首次启动自动生成）。主要键：`controller`、`secret`、`panel_url`、`switch_program`、`poll_interval`、`close_connections`、`language`（`system|zh|en`）、`autostart`。

**开机自启**：默认关闭。把 `Data/config.ini` 里的 `autostart` 改成 `true` 并重启应用，会写入 `~/Library/LaunchAgents/com.mihomotray.MihomoTray.plist`（登录时用 `open` 打开本 `.app`）；改回 `false` 再启动一次就删除这个文件（只删自己的）。挪动 `.app` 位置后重新启动一次即可更新路径。

## 构建（需在 Mac 上）

```bash
./build.sh          # -> dist/arm64/MihomoTray.app 与 dist/x86_64/MihomoTray.app
./build.sh arm64    # 仅 Apple Silicon
./build.sh x86_64   # 仅 Intel
./build.sh native   # 仅本机架构
```

需要 Xcode 或 Command Line Tools（`swiftc`）。不再打 universal（lipo）包，开源发布时分别提供 Intel 与 Apple Silicon 两个 zip。

## 布局

- `Sources/MihomoTray/` Swift + AppKit（`main`、`TrayController`、`MihomoClient`、`AppConfig`、`Loc`）
- `Assets/` 菜单栏图标与预览
- `Resources/Info.plist`、`config.ini` 模板
- `tools/make_mac_icons.py` 从 Windows CFW 图生成 template / 红绿灰

版本 **1.0.5**：发版号 `CFBundleShortVersionString` = `1.0.5`；构建号 `CFBundleVersion` = `1.0.5.0`（本地只加第 4 段 `N`）。Actions / Release 读 ShortVersion。

## GitHub Actions 编译

推到 GitHub 后 `.github/workflows/build-mac.yml` 会在 `macos-14` 上跑 `./build.sh`，产物 `MihomoTray_macos_<版本>_AppleSilicon.zip` 与 `MihomoTray_macos_<版本>_Intel.zip` 在 Artifacts 里下载；推 `mac-v*` 标签（例如 `mac-v1.0.5`）时附到 Release。发版号从 `Resources/Info.plist` 的 `CFBundleShortVersionString` 读取。

程序没有签名和公证，第一次打开请在 Finder 里右键 `MihomoTray.app` → 打开，再点「打开」确认。
