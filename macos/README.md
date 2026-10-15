# MihomoTray（macOS）1.0.5

菜单栏小工具，用来切换 mihomo 代理模式（规则 / 全局 / 直连）。英文见 `README_en.md`。

## 图标

| 模式 | 样式 |
|------|------|
| 规则 | **template 单色** CFW 小猫（保留眼睛），随系统浅/深色反色 |
| 全局 | **红色**非 template |
| 直连 | **绿色**非 template |
| 离线 | **灰色**非 template |

资源在 `Assets/`（18×18 与 `@2x`）。也可把同名 PNG 放到 `Data/Icons/` 覆盖。

## 菜单与提示

菜单顶一行灰色状态 → 打开面板 / 切换程序 → 规则 / 全局 / 直连 → 退出。

- 左键打开 `panel_url`；右键弹出菜单；**首次**打开面板时通知实际地址（旁路 `.panel_tip_shown`，只一次）
- 悬停：已连接为模式 / 日志级别 / 虚拟网卡；未连接为短原因（无法连接 / 鉴权失败 / 连接超时）

## 配置

`Data/config.ini`（应用旁；首次自动生成）。键：`controller`、`secret`、`panel_url`、`switch_program`、`poll_interval`、`close_connections`、`language`、`autostart`（无 `theme`）。

默认模板按小节空行排版；对照 mihomo 配置填写 controller / secret / panel_url。改完后重启本应用。

**开机自启**：默认关闭。`autostart = true` 后写入 `~/Library/LaunchAgents/com.mihomotray.MihomoTray.plist`。

## 构建（需在 Mac 上）

```bash
./build.sh          # -> dist/arm64/ 与 dist/x86_64/
./build.sh arm64    # 仅 Apple Silicon
./build.sh x86_64   # 仅 Intel
./build.sh native   # 仅本机架构
```

需要 Xcode 或 CLT（`swiftc`）。发布分别提供 Intel 与 Apple Silicon 两个 zip（不打 universal）。

## 版本与 CI

- 发版号 `CFBundleShortVersionString` = **1.0.5**
- 构建号 `CFBundleVersion` = **1.0.5.0**（本地只加第 4 段 N）
- Actions：`build-mac.yml`；标签 `mac-v*`

未签名/公证：首次请在 Finder 右键 → 打开。
