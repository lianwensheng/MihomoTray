# MihomoTray (macOS) 1.0.5

Menubar helper to switch mihomo mode (Rule / Global / Direct). Icon colors show the current mode so Global left on is obvious. Chinese: `README.md`.

## Icons

| Mode | Style |
|------|-------|
| Rule | Template mono CFW cat (eyes kept), follows light/dark |
| Global | Red (non-template) |
| Direct | Green (non-template) |
| Offline | Grey (non-template) |

Assets in `Assets/`. Override via `Data/Icons/` with the same names.

## Menu and tip

Grey status line at top only when offline → Open panel / Open app → modes → Quit. When connected, menu starts at Open panel (no grey status row).

- Left-click opens `panel_url`; right-click shows the menu; tip while `secret` empty (set `secret` to stop)
- Hover: when connected — mode / log / TUN; when offline — short reason (Can't connect / Auth failed / Timed out)

## Config

`Data/config.ini` (next to the app; created on first run). Keys: `controller`, `secret`, `panel_url`, `switch_program`, `poll_interval`, `close_connections`, `language`, `autostart` (no `theme`).

Default template uses blank lines between sections. Match `controller` / `secret` / `panel_url` to mihomo. Restart after edits.

**Autostart**: off by default. `autostart = true` writes `~/Library/LaunchAgents/com.mihomotray.MihomoTray.plist`.

## Build (on a Mac)

```bash
./build.sh          # -> dist/arm64/ and dist/x86_64/
./build.sh arm64
./build.sh x86_64
./build.sh native
```

Needs Xcode or CLT (`swiftc`). Separate Intel and Apple Silicon zips (no universal).

## Version / Actions

Marketing `CFBundleShortVersionString` = **1.0.5**; build `CFBundleVersion` = **1.0.5.0** (bump only the 4th segment locally). Workflow `build-mac.yml`; Release on `mac-v*` tags.

Unsigned: first open via Finder → Open.
