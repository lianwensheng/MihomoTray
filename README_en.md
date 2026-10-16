# MihomoTray

Chinese: [README.md](README.md)

Lightweight tray / menu bar helper: the icon color shows whether **mihomo** is in Rule, Global, or Direct mode (so Global left on is obvious), with one-click switching from the menu.

Windows, macOS, and Linux each use native code with **independent version numbers**, published together from this repo.

## Platforms

| Platform | Directory | Version | Release artifacts |
|----------|-----------|---------|-------------------|
| Windows | [windows/](windows/) | 2.1.9 | Filename: `MihomoTray_windows_2.1.9.zip` |
| macOS | [macos/](macos/) | 1.0.6 | Filename: `MihomoTray_macos_1.0.6_AppleSilicon.zip` / `_Intel.zip` |
| Linux | [linux/](linux/) | 1.0.5 | Qt AppImage + GTK `.deb` / `.rpm` / `.tar.gz` |

Windows and Linux share the same icon style: Rule = original blue cat, Global = red, Direct = green, Offline = grey  
macOS mixes template icons: Rule = black/white cat, Global = red, Direct = green, Offline = grey

When the controller is unreachable the icon stays grey; the hover tip and the grey status line at the top of the menu distinguish **Can't connect** / **Auth failed** / **Timed out** (other/unknown cases show "**Disconnected**"), and on Linux GTK (no hover) rely on the grey menu line.

Icons can be customized. For install, config, and menu details see each platform's `README.md` (Chinese) and `README_en.md` (English)

## Config

On first run a `config.ini` is created (Windows / macOS: `Data/` next to the app; Linux: `~/.config/MihomoTray/`)  
The default template uses blank lines between sections; comments explain how to fill `controller` / `secret` / `panel_url` from the mihomo config file  
`theme` is Windows-only. Restart this app after editing the config.

## Build from source

**Windows** (needs system `csc`, run under `windows/`):

```bat
build.bat
```

**macOS**:

```bash
cd macos
./build.sh both          # arm64 and x86_64
# ./build.sh             # host arch only
```

**Linux**:

```bash
cd linux
./build.sh all           # Qt AppImage + GTK deb/rpm/tar.gz
# ./build.sh qt          # AppImage only
# ./build.sh gtk         # GTK packages only
```

## License

[MIT](LICENSE)
