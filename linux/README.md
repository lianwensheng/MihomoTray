# MihomoTray（Linux）1.0.6

Mihomo 托盘小工具，按不同颜色图标显示当前代理模式，防止忘关全局模式；菜单切换规则 / 全局 / 直连，方便轻量操作。英文见 `README_en.md`。

## 变体

| 变体 | 产物 | 说明 |
|------|------|------|
| **Qt（精简 AppImage）** | `MihomoTray_linux_qt_1.0.6_x86_64.AppImage` | 约 46MB；KDE/XFCE 等可左键开面板；桌面支持时有悬停 |
| **GTK（轻量）** | `.deb` / `.rpm` / `.tar.gz` | 约几百 KB；以菜单为主；**无悬停**，断连时看菜单顶灰字 |

两变体共用配置 / 连接 / 文案 / 开机自启逻辑。图标与 Windows 同套 CFW 猫：规则原色、全局红、直连绿、未连接灰。

## 使用方法

1. 运行对应变体后，托盘出现小猫图标。
   - 原色 = 规则　红 = 全局　绿 = 直连　灰 = 未连接
   - **悬停**（若桌面支持，主要是 Qt）：已连接时约 3 行（模式 / 日志级别 / 虚拟网卡）；未连接为短原因（无法连接 / 鉴权失败 / 连接超时）
   - **GTK** 无悬停时，断连状态只看菜单顶部灰字

2. 菜单：（断连时顶栏灰字；已连接从「打开面板」起）
   - 打开面板 → 浏览器打开 `panel_url`（默认 `http://127.0.0.1:9090/ui/`）；`secret` 为空时通知提示，配好后停止
   - 切换程序 → 启动 `switch_program`；未设置则灰显
   - 规则 / 全局 / 直连 → 切换模式（当前打勾）
   - 退出

3. 默认约每 3 秒轮询；别处改了模式，图标会跟着变。  
4. 开机自启：`autostart = true` 后写入 `~/.config/autostart/MihomoTray.desktop`（默认 false）。

## 桌面支持

| 桌面 | 说明 |
|------|------|
| GNOME（Ubuntu） | 自带 AppIndicator 扩展，一般可用 |
| GNOME（Fedora 等） | 需装 AppIndicator 扩展 |
| KDE / XFCE / Cinnamon / MATE / Budgie | 通常原生支持托盘 |

不支持悬停的桌面不会用菜单顶模式文字顶替悬停（按设计省略）。

## 配置（`~/.config/MihomoTray/config.ini`，首次自动生成，改完请重启）

| 键 | 说明 |
|----|------|
| `controller` | external-controller，默认 `127.0.0.1:9090` |
| `secret` | 访问密钥（mihomo 配置中查询）；ASCII；整行密钥；打开面板时若为空会提示 |
| `panel_url` | 面板网址 |
| `switch_program` | 「切换程序」路径，可留空 |
| `switch_program_args` | 附加参数 |
| `poll_interval` | 轮询秒数（默认 3） |
| `close_connections` | 切换后是否断开连接（默认 true） |
| `language` | `system` / `zh` / `en` |
| `autostart` | 默认 false |

无 `theme`。删配置可重生默认；升级只追加缺键。

## 运行

### Qt AppImage

```bash
chmod +x MihomoTray_linux_qt_1.0.6_x86_64.AppImage
./MihomoTray_linux_qt_1.0.6_x86_64.AppImage
# 无 FUSE：
./MihomoTray_linux_qt_1.0.6_x86_64.AppImage --appimage-extract-and-run
```

### GTK 包

```bash
sudo apt install ./MihomoTray_linux_1.0.6.deb && mihomotray   # Debian/Ubuntu
sudo dnf install ./MihomoTray_linux_1.0.6.rpm && mihomotray   # Fedora
tar xzf MihomoTray_linux_gtk_1.0.6.tar.gz && cd MihomoTray_linux_gtk_1.0.6 && sudo ./install.sh
```

### 从源码

```bash
MIHOMOTRAY_FRONTEND=qt ./run.sh    # 需 PySide6
MIHOMOTRAY_FRONTEND=gtk ./run.sh
./build.sh all    # 或 qt / gtk
```

## 版本与 CI

- 发版号 `__version__` = **1.0.6**（UA / 包名）
- 本地 `__build__` 从 0 起，不进 UA；N>0 时本地产物名带 `.N`
- Actions：`build-linux.yml`；标签 `linux-v*`

## 常见问题

- 除 `secret` 外可用行尾 `;` / `#` 注释
- 配置错误会提示并用默认值
- 图标一直灰：核对 mihomo `external-controller` / `secret`
- 切换失败会提示原因（无法连接 / 鉴权失败等）

图标颜色用于一眼区分模式，避免忘关全局。
