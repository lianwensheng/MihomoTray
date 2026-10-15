# MihomoTray (Linux) 1.0.3

Tray helper for mihomo mode (Rule / Global / Direct). Chinese: `README.md`.

## Variants

| Variant | Artifacts | Notes |
|---------|-----------|-------|
| **Qt (slim AppImage)** | `MihomoTray_linux_qt_1.0.3_x86_64.AppImage` | ~46MB; left-click panel on KDE/XFCE; hover tip when the desktop supports it |
| **GTK (light)** | `.deb` / `.rpm` / `.tar.gz` | Tiny; menu-first; **no hover** — use the grey status line at the top of the menu |

## Status text

Grey icon when offline. Hover (if any) and the grey menu line show:

- **Can't connect** — bad controller host/port or mihomo down
- **Auth failed** — secret mismatch
- **Timed out** — controller not responding

When connected, the grey line shows the current mode. No spammy desktop notifications.

## Config

`~/.config/MihomoTray/config.ini` on first run. Keys: `controller`, `secret`, `panel_url`, `switch_program`, `poll_interval`, `close_connections`, `language`, `autostart` (no `theme`).

Default template uses blank lines between sections. Match controller/secret/panel_url to mihomo. Restart after edits.

## Run / build

```bash
./MihomoTray_linux_qt_1.0.3_x86_64.AppImage
sudo apt install ./MihomoTray_linux_1.0.3.deb && mihomotray
./build.sh all    # or qt / gtk
```

## Version / Actions

Marketing `__version__` **1.0.3** (UA / packages). Local `__build__` starts at 0 (not in UA); N>0 adds `.N` to local artifact names. Workflow `build-linux.yml`; Release on `linux-v*`.
