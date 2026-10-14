# MihomoTray (Linux) 1.0.3

Tray helper: tell the mihomo proxy mode from the icon colour; switch rule / global / direct from the menu. Chinese: `README.md`.

Two **variants** share the same config / client / strings / autostart core:

| Variant | Artifact | Size | Deps | Notes |
|---------|----------|------|------|-------|
| **Qt (slim AppImage)** | `MihomoTray_linux_qt_1.0.3_x86_64.AppImage` | ~46MB (slimmed from ~91MB) | Mostly bundled; FUSE2 or `--appimage-extract-and-run` | Left-click opens panel on KDE/XFCE; tooltip when the DE shows it; SNI with XEmbed fallback |
| **GTK (lightweight)** | `.deb` / `.rpm` / `.tar.gz` | a few hundred KB | System Python3 + PyGObject + AppIndicator + Gtk3 + libnotify | Tiny; tray click shows menu only (no separate left-click); **no tooltip** (and no mode text added to the menu top) |

## Icons

Same coloured CFW cat as Windows: rule = original, global = red, direct = green, offline = grey. Built-in 16–256px; on first start 256px copies go to `~/.config/MihomoTray/Icons/`.

## Desktops

GNOME on Ubuntu works out of the box. Other GNOME: install the [AppIndicator](https://extensions.gnome.org/extension/615/appindicator-support/) extension (`gnome-shell-extension-appindicator` on Fedora). KDE / XFCE / Cinnamon / MATE / Budgie usually work natively.

## Config

`~/.config/MihomoTray/config.ini`. Keys: `controller`, `secret`, `panel_url`, `switch_program`, `switch_program_args`, `poll_interval`, `close_connections`, `language`, `autostart` (default `false`). Autostart writes `~/.config/autostart/MihomoTray.desktop` (only its own marked file).

## Run

**Qt AppImage**

```bash
chmod +x MihomoTray_linux_qt_1.0.3_x86_64.AppImage
./MihomoTray_linux_qt_1.0.3_x86_64.AppImage
```

**GTK**

```bash
# Debian/Ubuntu
sudo apt install ./MihomoTray_linux_1.0.3.deb
mihomotray
# Fedora
sudo dnf install ./MihomoTray_linux_1.0.3.rpm
mihomotray
# Arch (deps example)
sudo pacman -S python python-gobject libayatana-appindicator libnotify gtk3
# then unpack tar.gz and: sudo ./install.sh
# openSUSE
sudo zypper install python3-gobject typelib-1_0-AyatanaAppIndicator3-0_1 libnotify-tools gtk3
# Generic
tar xzf MihomoTray_linux_gtk_1.0.3.tar.gz && cd MihomoTray_linux_gtk_1.0.3 && sudo ./install.sh
mihomotray
```


**From source:** `MIHOMOTRAY_FRONTEND=qt|gtk ./run.sh`

## Build

```bash
./build.sh          # all
./build.sh qt       # slim AppImage only
./build.sh gtk      # deb + rpm + tar.gz
```

## Test

```bash
QT_QPA_PLATFORM=offscreen xvfb-run -a python3 -m unittest discover -s test -v
```

## Version / Actions

**1.0.3**. Workflow `build-linux.yml` builds both variants; Release on `linux-v*` tags (e.g. `linux-v1.0.3`) attaches all four artifacts.
