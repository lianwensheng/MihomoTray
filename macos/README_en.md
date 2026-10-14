# MihomoTray (macOS) 1.0.5

Menubar helper to switch mihomo proxy mode (Rule / Global / Direct). Chinese README: `README.md`.

## Icons

| Mode | Style |
|------|--------|
| Rule | **Template monochrome** CFW cat (with eyes); follows light/dark menubar |
| Global | **Red** non-template |
| Direct | **Green** non-template |
| Offline | **Grey** non-template |

Assets in `Assets/` (18×18 and @2x 36×36). Preview: `Assets/preview.png`. Override via `Data/Icons/`.

## Menu

Dashboard / Open App | Rule / Global / Direct (checkmark) | Quit.  
Left-click opens `panel_url`; right-click shows the menu. Tooltip: Mode / Log Level / TUN Mode.

## Config

`Data/config.ini` beside the app. Keys: `controller`, `secret`, `panel_url`, `switch_program`, `poll_interval`, `close_connections`, `language` (`system|zh|en`), `autostart`.

**Start at login**: off by default. Set `autostart = true` in `Data/config.ini` and restart the app; it writes `~/Library/LaunchAgents/com.mihomotray.MihomoTray.plist` (opens this `.app` via `open` at login). Set it back to `false` and start once more to remove that file (only its own). After moving the `.app`, start it once to update the path.

## Build (on a Mac)

```bash
./build.sh
open dist/MihomoTray.app
```

Requires Xcode or CLT (`swiftc`). Source + icons can be prepared on Linux; the `.app` binary must be built on macOS.

Version **1.0.5**.

## Build (on a Mac)

```bash
./build.sh          # -> dist/arm64/ and dist/x86_64/
./build.sh arm64|x86_64|native
```

No universal binary; CI uploads separate Apple Silicon and Intel zips.


## GitHub Actions

`.github/workflows/build-mac.yml` runs `./build.sh` on `macos-14` and uploads `MihomoTray_macos_<version>_AppleSilicon.zip` and `MihomoTray_macos_<version>_Intel.zip` as artifacts; pushing a `mac-v*` tag (e.g. `mac-v1.0.5`) also attaches them to a Release. The version is read from `Resources/Info.plist`.

The app is not signed or notarized: on first launch, right-click `MihomoTray.app` in Finder → Open, then confirm Open.


CI uploads separate **AppleSilicon** and **Intel** zips (no universal binary).
