# MihomoTray (macOS) 1.0.5

Mihomo menubar helper. Colored icons show the current proxy mode so Global left on is obvious. Left-click opens the dashboard; right-click switches modes. Chinese: `README.md`.

## Usage

1. Open the app from any folder; a Clash cat appears in the menu bar.
   - **Rule**: template mono CFW cat (eyes kept), follows light/dark
   - **Global**: red (non-template)
   - **Direct**: green (non-template)
   - **Offline**: grey (non-template)
   - Hover (3 lines when connected, from mihomo `GET /configs`):
     - Mode: Rule / Global / Direct
     - Log level: Silent / Error / Warning / Info / Debug (unknown shows —)
     - TUN: On / Off (`tun.enable`; log maps to `log-level`)
     - **Connected**: mode / log / TUN; **offline**: short reason (Can't connect / Auth failed / Timed out)

2. Left-click: open `http://127.0.0.1:9090/ui/` (from `panel_url`); tip while `secret` empty — set secret to stop  
   Right-click menu: (grey status **only when offline**; when connected starts at Open panel)
   - Open panel → default browser on `panel_url`
   - Open app → launch `switch_program` from `Data/config.ini`; grey if unset; notify on missing file / launch failure
   - Rule / Global / Direct → switch mihomo mode (check mark on current)
   - Quit

3. Polls about every 3 seconds by default; changes elsewhere update icon and hover.  
4. Single instance. Autostart: set `autostart = true` and restart (default `false`) → `~/Library/LaunchAgents/com.mihomotray.MihomoTray.plist`.

## Layout

```
MihomoTray.app/
Data/config.ini      Config (created on first run)
Data/Icons/          Optional PNG overrides (defaults in Assets/, 18×18 and @2x)
```

## Config (`Data/config.ini` — restart after edits)

| Key | Meaning |
|-----|---------|
| `controller` | external-controller, default `127.0.0.1:9090`, port required; `:9090` / `0.0.0.0:9090` → `127.0.0.1:9090` |
| `secret` | Access key from mihomo config; ASCII only; whole line is the key; tip when opening panel if empty |
| `panel_url` | Dashboard URL |
| `switch_program` | Optional app for “Open app” |
| `switch_program_args` | Extra args (usually empty) |
| `poll_interval` | Seconds (default 3) |
| `close_connections` | Close connections after mode switch (default true) |
| `language` | `system` / `zh` / `en` |
| `autostart` | Default false |

No `theme` (unlike Windows). Deleting `config.ini` regenerates defaults; upgrades append missing keys only.

## Build (on a Mac)

```bash
./build.sh          # -> dist/arm64/ and dist/x86_64/
./build.sh arm64
./build.sh x86_64
./build.sh native
```

Needs Xcode or CLT (`swiftc`). Separate Intel and Apple Silicon zips (no universal).

## Version / CI

- Marketing `CFBundleShortVersionString` = **1.0.5**
- Build `CFBundleVersion` = **1.0.5.N** (bump only the 4th segment locally)
- Actions: `build-mac.yml`; tags `mac-v*`

Unsigned: first open via Finder → Open.

## FAQ

- Trailing `;` / `#` comments OK except on `secret`
- Bad config keys show a tip and fall back to defaults
- Grey icon: match `external-controller` / `secret` to mihomo
- Switch failures notify with the reason

Design: icon colors show mode so Global is hard to forget. Art inspired by Clash for Windows tray cat; red/green/grey are recolors.
