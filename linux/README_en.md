# MihomoTray (Linux) 1.0.5

Mihomo tray helper. Icon colors show Rule / Global / Direct so Global left on is obvious. Chinese: `README.md`.

## Variants

| Variant | Artifacts | Notes |
|---------|-----------|-------|
| **Qt (slim AppImage)** | `MihomoTray_linux_qt_1.0.5_x86_64.AppImage` | ~46MB; left-click panel on KDE/XFCE; hover when the desktop supports it |
| **GTK (light)** | `.deb` / `.rpm` / `.tar.gz` | Tiny; menu-first; **no hover** — when offline use the grey status line at the top of the menu |

Shared config / client / strings / autostart. Same CFW-style cat icons as Windows: original / red / green / grey.

## Usage

1. Run a variant; the cat appears in the tray.
   - Original = Rule　Red = Global　Green = Direct　Grey = offline
   - **Hover** (if supported, mainly Qt): 3 lines when connected (mode / log / TUN); short reason when offline (Can't connect / Auth failed / Timed out)
   - **GTK** without hover: read offline status from the grey menu line

2. Menu: (grey status **only when offline**; when connected starts at Open panel)
   - Open panel → browser on `panel_url` (default `http://127.0.0.1:9090/ui/`); tip while `secret` empty
   - Open app → `switch_program` (grey if unset)
   - Rule / Global / Direct → switch mode
   - Quit

3. Polls about every 3 seconds by default.  
4. Autostart: `autostart = true` → `~/.config/autostart/MihomoTray.desktop` (default false).

## Desktop support

| Desktop | Notes |
|---------|-------|
| GNOME (Ubuntu) | AppIndicator extension usually present |
| GNOME (Fedora, etc.) | Install AppIndicator extension |
| KDE / XFCE / Cinnamon / MATE / Budgie | Tray usually works |

If the desktop has no hover tip, mode is not duplicated as menu header text (by design).

## Config (`~/.config/MihomoTray/config.ini`)

| Key | Meaning |
|-----|---------|
| `controller` | external-controller (default `127.0.0.1:9090`) |
| `secret` | Access key from mihomo; ASCII; whole-line key; tip when opening panel if empty |
| `panel_url` | Dashboard URL |
| `switch_program` | Optional “Open app” path |
| `switch_program_args` | Extra args |
| `poll_interval` | Seconds (default 3) |
| `close_connections` | Default true |
| `language` | `system` / `zh` / `en` |
| `autostart` | Default false |

No `theme`. Missing keys are appended on upgrade.

## Run / build

```bash
./MihomoTray_linux_qt_1.0.5_x86_64.AppImage
sudo apt install ./MihomoTray_linux_1.0.5.deb && mihomotray
./build.sh all    # or qt / gtk
```

## Version / CI

Marketing `__version__` **1.0.5**; local `__build__` starts at 0 (not in UA); N>0 adds `.N` to local artifact names. Workflow `build-linux.yml`; tags `linux-v*`.

## FAQ

- Trailing comments OK except on `secret`
- Bad config → tip + defaults
- Grey icon → match controller/secret to mihomo
- Switch failures show the reason

Icon colors exist so you notice Global left on.
