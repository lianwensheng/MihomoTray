# MihomoTray（Windows）2.1.8

Windows 托盘小工具，用来切换 mihomo 代理模式（规则 / 全局 / 直连）。

- 中文用法简版：`README.txt`（打进 zip）
- 英文：`README_en.txt`
- 界面文案：`src/Loc.cs`（`language = system|zh|en`，默认 system）

## 功能概要

| 项目 | 说明 |
|------|------|
| 图标 | 规则原色 / 全局红 / 直连绿 / 未连接灰 |
| 左键 | 打开 `panel_url` 面板（0.8 秒内防重复） |
| 右键 | 原生 Win32 菜单（FlClash 风格） |
| 悬停 | 已连接：模式 / 日志级别 / 虚拟网卡；未连接：短原因（无法连接 / 鉴权失败 / 连接超时） |
| 菜单顶 | 一行灰色状态（与悬停短原因或当前模式一致） |

## 菜单顺序

状态（灰字） → 打开面板 / 切换程序 → 规则 / 全局 / 直连（当前打勾）→ 退出。

「切换程序」启动 `switch_program`（可加 `switch_program_args`）；未配置时变灰。

## 配置

`Data/config.ini`（exe 旁；首次自动生成）。主要键：`controller`、`secret`、`panel_url`、`switch_program`、`poll_interval`、`close_connections`、`language`、`theme`、`autostart`。

默认模板按小节空行排版；`controller` / `secret` / `panel_url` 注释说明需对照 mihomo 配置填写。改完后重启本程序。

开机自启默认关闭；`autostart = true` 后每次启动会同步到注册表。

## 源码结构

- `src/` C# WinForms（.NET Framework 4.x）
- `icons/` CFW 原色猫 + 生成的模式图标
- `dist/Data/` 运行时：`config.ini`、`MihomoTray.exe.config`、`Icons/`
- `tools/` 图标 / 预览 / 配置生成
- `test/` mock controller 与回归测试

## 构建

**Windows**

```bat
build.bat
```

产出 `dist\MihomoTray.exe`，并在非 CI 下打包 `MihomoTray_windows_<版本>.zip`（FileVersion 第 4 段 N>0 时带 `.N`）。

**Linux（mono，便于自测）**

```bash
sudo apt install mono-devel python3-pil
./build.sh
```

## 版本与 CI

- 产品版本 **2.1.8**（`AssemblyInformationalVersion`，UA `MihomoTray/2.1.8`）
- 文件版本 **2.1.8.0**（本地小改只加第 4 段 N）
- Actions：`build-win.yml`；标签 `win-v*` 发 Release

exe 未签名，首次运行 SmartScreen 可能提示，选「更多信息 → 仍要运行」。
