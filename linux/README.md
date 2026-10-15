# MihomoTray（Linux）1.0.3

托盘小工具：看图标颜色就知道 mihomo 当前模式（防忘关全局），菜单里切换规则 / 全局 / 直连。英文见 `README_en.md`。

## 变体

| 变体 | 产物 | 体积 | 依赖 | 特点 |
|------|------|------|------|------|
| **Qt（精简 AppImage）** | `MihomoTray_linux_qt_1.0.3_x86_64.AppImage` | 约 46MB | 基本自带；需 FUSE2 或 `--appimage-extract-and-run` | KDE/XFCE 等可左键开面板；有悬停时显示短状态 |
| **GTK（轻量）** | `.deb` / `.rpm` / `.tar.gz` | 约几百 KB | 系统 Python3 + PyGObject + AppIndicator + Gtk3 + libnotify | 体积小；点击主要弹菜单；**无悬停**，断连时看菜单顶部灰字状态 |

两变体共用配置 / 连接 / 文案 / 开机自启逻辑。

## 状态提示

未连接时图标为灰。悬停（若桌面支持）与菜单顶灰字（仅断连时显示）区分：

- **无法连接** — controller 地址/端口不对，或 mihomo 未开
- **鉴权失败** — secret 与 mihomo 不一致
- **连接超时** — 控制器无响应

已连接时菜单不显示顶栏灰字，模式看图标颜色与悬停。不做偶发桌面通知刷屏。

## 图标与菜单

图标与 Windows 同套 CFW 猫：规则原色、全局红、直连绿、未连接灰。

菜单：断连时状态（灰字）→ 打开面板 / 切换程序 → 模式 → 退出；已连接时从「打开面板」起。打开面板时若 `secret` 为空则通知实际 `{panel_url}` 与停提醒说明；填入 `secret` 后不再提示。

## 桌面支持

| 桌面 | 说明 |
|------|------|
| GNOME（Ubuntu） | 自带 AppIndicator 扩展，一般可用 |
| GNOME（Fedora 等） | 需装 AppIndicator 扩展 |
| KDE / XFCE / Cinnamon / MATE / Budgie | 通常原生支持托盘 |

## 配置

`~/.config/MihomoTray/config.ini`，首次自动生成。键：`controller`、`secret`、`panel_url`、`switch_program`、`poll_interval`、`close_connections`、`language`、`autostart`（无 `theme`）。

默认模板按小节空行排版；对照 mihomo 填写 controller / secret / panel_url。改完后重启。

开机自启：`autostart = true` 后写入 `~/.config/autostart/MihomoTray.desktop`。

## 运行

### Qt AppImage

```bash
chmod +x MihomoTray_linux_qt_1.0.3_x86_64.AppImage
./MihomoTray_linux_qt_1.0.3_x86_64.AppImage
# 无 FUSE：
./MihomoTray_linux_qt_1.0.3_x86_64.AppImage --appimage-extract-and-run
```

### GTK 包

```bash
# Debian/Ubuntu
sudo apt install ./MihomoTray_linux_1.0.3.deb
mihomotray

# Fedora
sudo dnf install ./MihomoTray_linux_1.0.3.rpm
mihomotray

# 通用 tar.gz
tar xzf MihomoTray_linux_gtk_1.0.3.tar.gz
cd MihomoTray_linux_gtk_1.0.3
sudo ./install.sh
```

### 从源码

```bash
MIHOMOTRAY_FRONTEND=qt ./run.sh    # 需 PySide6
MIHOMOTRAY_FRONTEND=gtk ./run.sh   # 需系统 gi 等
```

## 打包与测试

```bash
./build.sh all    # 或 qt / gtk
QT_QPA_PLATFORM=offscreen xvfb-run -a python3 -m unittest discover -s test -v
```

## 版本与 CI

- 发版号 `__version__` = **1.0.3**（UA / 包名）
- 本地 `__build__` 从 0 起，不进 UA；N>0 时产物文件名带 `.N`
- Actions：`build-linux.yml`；标签 `linux-v*`
