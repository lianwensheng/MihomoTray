# MihomoTray

English: [README_en.md](README_en.md)

轻量托盘 / 菜单栏小工具：看图标颜色就知道 **mihomo** 当前是规则、全局还是直连，菜单里一键切换。

Windows、macOS、Linux 各用原生代码，**版本号各自独立**，合在本仓库一起发布。

## 平台一览

| 平台 | 目录 | 版本 | 正式发行版 |
|------|------|------|------|
| Windows | [windows/](windows/) | 2.1.8 | 文件名：`MihomoTray_windows_2.1.8.zip` |
| macOS | [macos/](macos/) | 1.0.5 | 文件名：`MihomoTray_macos_1.0.5_AppleSilicon.zip` / `_Intel.zip` |
| Linux | [linux/](linux/) | 1.0.3 | Qt AppImage + GTK 的 `.deb` / `.rpm` / `.tar.gz` |

Windows 版与 Linux 版图标一致：规则 = 原色蓝猫、全局 = 红、直连 = 绿、未连接 = 灰  
macOS 版混用 template 图标：规则 = 单色黑/白猫、全局 = 红、直连 = 绿、未连接 = 灰

连不上控制器时图标仍为灰色；悬停提示与菜单顶部灰字会区分 **无法连接** / **鉴权失败** / **连接超时**（其它/未知情况显示「**未连接**」），Linux GTK 无悬停时主要看菜单灰字。

图标可自定义修改，更细的安装、配置、菜单说明见各目录里的 `README.md`（中文）和 `README_en.md`（英文）

## 配置

首次运行会生成 `config.ini`（Windows / macOS 在应用旁 `Data/`，Linux 在 `~/.config/MihomoTray/`）  
默认模板按小节空行排版，注释里说明如何对照 mihomo 配置文件填写 `controller` / `secret` / `panel_url`  
仅 Windows 有 `theme`；改完配置后需重启本小工具。

## 本地构建

**Windows**（需系统自带 `csc`，在 `windows/` 下）：

```bat
build.bat
```

**macOS**：

```bash
cd macos
./build.sh both          # 同时出 arm64 与 x86_64
# ./build.sh             # 只编本机架构
```

**Linux**：

```bash
cd linux
./build.sh all           # Qt AppImage + GTK deb/rpm/tar.gz
# ./build.sh qt          # 仅 AppImage
# ./build.sh gtk         # 仅 GTK 包
```

## 许可证

[MIT](LICENSE)
