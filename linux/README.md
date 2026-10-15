# MihomoTray（Linux）1.0.3

托盘小工具：看图标颜色就知道 mihomo 当前的代理模式，右键菜单里一键切换规则 / 全局 / 直连。英文说明见 `README_en.md`。

本版本提供 **两个变体**（共用同一套配置 / 连接 / 文案 / 开机自启逻辑）：

| 变体 | 产物 | 体积 | 依赖 | 特点 |
|------|------|------|------|------|
| **Qt（精简 AppImage）** | `MihomoTray_linux_qt_1.0.3_x86_64.AppImage` | 约 46MB（自 91MB 精简） | 基本自带；需 FUSE2 或 `--appimage-extract-and-run` | KDE/XFCE 等可左键开面板；有悬停提示（桌面支持时）；自动走 SNI / XEmbed |
| **GTK（轻量）** | `.deb` / `.rpm` / `.tar.gz` | 约几百 KB | 系统 Python3 + PyGObject + AppIndicator + Gtk3 + libnotify | 体积小；点击只弹菜单（无单独左键）；无悬停提示（不在菜单顶部加模式文字） |

## 图标

和 Windows 版同一套 CFW 原色小猫：规则模式原色、全局红、直连绿、未连接灰。
内置 16–256px；首次启动会把 256px 复制到 `~/.config/MihomoTray/Icons/tray_{rule,global,direct,offline}.png`，可替换（≤2MB）。

## 菜单

打开面板 / 切换程序 | 规则模式 / 全局模式 / 直连模式（当前打勾）| 退出。顺序与 Windows 版一致。

## 支持的桌面

| 桌面 | 说明 |
|------|------|
| GNOME（Ubuntu） | 自带 AppIndicator 扩展，直接可用 |
| GNOME（Fedora、Debian、Arch 等） | 需装 [AppIndicator and KStatusNotifierItem Support](https://extensions.gnome.org/extension/615/appindicator-support/)（Fedora：`sudo dnf install gnome-shell-extension-appindicator`，扩展里开启并重新登录） |
| KDE Plasma / XFCE / Cinnamon / MATE / Budgie | 一般原生支持托盘 |

## 配置

`~/.config/MihomoTray/config.ini`，首次启动自动生成。键：`controller`、`secret`、`panel_url`、`switch_program`、`switch_program_args`、`poll_interval`、`close_connections`、`language`（`system|zh|en`）、`autostart`（默认 `false`）。

**开机自启**：`autostart = true` 后重启小工具，写入 `~/.config/autostart/MihomoTray.desktop`（只管理带 `X-MihomoTray-Autostart` 标记的自己的文件）。AppImage 指向 AppImage 本身；deb/rpm/tar 安装后指向 `/usr/bin/mihomotray`（或安装前缀下的入口）。

## 运行

### Qt AppImage

```bash
chmod +x MihomoTray_linux_qt_1.0.3_x86_64.AppImage
./MihomoTray_linux_qt_1.0.3_x86_64.AppImage
# 无 FUSE 时：
./MihomoTray_linux_qt_1.0.3_x86_64.AppImage --appimage-extract-and-run
```

### GTK 包

**Debian / Ubuntu**

```bash
sudo apt install ./MihomoTray_linux_1.0.3.deb
# 依赖：python3 python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7
mihomotray
```

**Fedora**

```bash
sudo dnf install ./MihomoTray_linux_1.0.3.rpm
# 或：sudo dnf install python3-gobject libayatana-appindicator-gtk3 libnotify gtk3
mihomotray
```

**Arch**

```bash
# 用通用包，或自行打包；依赖示例：
sudo pacman -S python python-gobject libayatana-appindicator libnotify gtk3
# 然后解压 tar.gz 后：
sudo ./install.sh    # 默认装到 /usr/local
```

**openSUSE**

```bash
sudo zypper install python3-gobject typelib-1_0-AyatanaAppIndicator3-0_1 libnotify-tools gtk3
# 再装 rpm 或 tar.gz
```

**通用 tar.gz**

```bash
tar xzf MihomoTray_linux_gtk_1.0.3.tar.gz
cd MihomoTray_linux_gtk_1.0.3
sudo ./install.sh          # PREFIX=/usr/local
# PREFIX=/usr sudo ./install.sh
```

### 从源码运行

```bash
# Qt
pip install --user 'mihomotray[qt]'   # 或 PySide6-Essentials
MIHOMOTRAY_FRONTEND=qt ./run.sh

# GTK（需系统包 python3-gi 等）
MIHOMOTRAY_FRONTEND=gtk ./run.sh
```

## 打包

```bash
./build.sh          # = ./build.sh all
./build.sh qt       # 仅精简 AppImage
./build.sh gtk      # 仅 deb + rpm + tar.gz
```

Qt 构建用 python-appimage，再剥离不用的 Qt 模块；需要联网与 `file`、`curl`。

## 测试

```bash
pip install PySide6-Essentials
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 gir1.2-notify-0.7 xvfb
QT_QPA_PLATFORM=offscreen xvfb-run -a python3 -m unittest discover -s test -v
```

## 版本与 GitHub Actions

版本 **1.0.3**：发版号 `__version__`（与 `pyproject.toml`、User-Agent `MihomoTray/1.0.3` 一致）；本地构建号 `__build__`（从 `0` 起，不进 UA）。Actions / Release 只认 `__version__`；本地 `__build__>0` 时产物文件名带 `.N`。
`.github/workflows/build-linux.yml` 在 `ubuntu-latest` 上跑测试并 `./build.sh all`；Artifacts / 推 `linux-v*` 标签（例如 `linux-v1.0.3`）的 Release 附带上述四个产物。

## 和 Windows 版的差别

- GNOME 上（两变体）点击通常只弹菜单；Qt 变体在 KDE 等可左键开面板
- GTK 变体无悬停提示（不额外往菜单加文字）
- 提示用桌面通知；配置在 `~/.config/MihomoTray/`
