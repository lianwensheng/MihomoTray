# MihomoTray

轻量托盘 / 菜单栏小工具：看图标颜色就知道 **mihomo** 当前是规则、全局还是直连，菜单里一键切换。

Windows、macOS、Linux 各用原生代码，**版本号各自独立**，合在本仓库一起发布。

## 平台一览

| 平台 | 目录 | 版本 | 产物 |
|------|------|------|------|
| Windows | [windows/](windows/) | 2.1.8 | MihomoTray_windows_2.1.8.zip |
| macOS | [macos/](macos/) | 1.0.5 | MihomoTray_macos_1.0.5_AppleSilicon.zip / _Intel.zip |
| Linux | [linux/](linux/) | 1.0.3 | Qt AppImage + GTK 的 `.deb` / `.rpm` / `.tar.gz` |

图标与 Windows 版一致：规则 = 原色猫、全局 = 红、直连 = 绿、未连接 = 灰。

更细的安装、配置、菜单说明见各目录里的 `README.md`（中文）和 `README_en`（英文）。

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

## 版本号约定

三端各自维护发版号 `x.y.z`（互不统一）。发版 / GitHub Actions / Release 标签只认这个发版号。

本地小改（未发版）只顺延第 4 段构建号 `N`，从 `0` 起：

| 平台 | 发版号（动了才发版） | 本地构建号 N | 产物文件名 |
|------|----------------------|--------------|------------|
| Windows | `AssemblyInformationalVersion`（产品版本） | `AssemblyFileVersion` 的第 4 段 | Release 用 `x.y.z`；本地 N>0 时 zip 可带 `.N` |
| macOS | `CFBundleShortVersionString` | `CFBundleVersion` = `x.y.z.N` | CI 读 ShortVersion，Release 用 `x.y.z` |
| Linux | `__version__`（UA / `pyproject.toml`） | `__build__`（不进 UA） | N=0 用 `x.y.z`；N>0 时本地产物文件名带 `.N` |

## 发版标签

每个平台用自己的标签前缀，互不影响：

| 平台 | 标签示例 | Release 名称 |
|------|----------|--------------|
| Windows | `win-v2.1.8` | Windows v2.1.8 |
| macOS | `mac-v1.0.5` | macOS v1.0.5 |
| Linux | `linux-v1.0.3` | Linux v1.0.3 |

```bash
git tag win-v2.1.8
git push origin win-v2.1.8
```

推送后，对应平台的 GitHub Actions 会编译并把产物挂到该 Release。

## CI 说明

- 三个 workflow：`.github/workflows/build-win.yml` / `build-mac.yml` / `build-linux.yml`
- 只监听 `main` 的 push，以及 pull request；用路径过滤，改哪端跑哪端
- 带平台前缀的 tag 发版时一定会跑，不受路径过滤影响
- 也可在 Actions 页手动 `workflow_dispatch`

## 许可证

[MIT](LICENSE)
