MihomoTray (tray utility)
===================================

The right-click menu is a native Windows menu (same approach as FlClash). The current mode is checked with ✓.

Usage
-----
1. Put this folder anywhere and double-click MihomoTray.exe. A Clash for Windows cat icon appears in the tray.
   - Original (blue) = Rule　Red = Global　Green = Direct　Gray = disconnected from mihomo
   - Hover tip (3 lines, from mihomo GET /configs):
     Mode : Rule / Global / Direct (shows "Disconnected" when offline)
     Log Level : Silent / Error / Warn / Info / Debug (— when unknown or offline)
     TUN Mode : On / Off (— when offline)
     TUN Mode maps to tun.enable; Log Level maps to log-level. This tool does not read Windows system proxy settings.
2. Left-click the icon: open the dashboard http://127.0.0.1:9090/ui/ (set by panel_url)
   Right-click:
   - Dashboard　→ open http://127.0.0.1:9090/ui/ in the default browser
   - Open App　→ launch the program set by switch_program in Data\config.ini (e.g. Clash Verge / FlClash / Clash Party)
                 Grayed out when unset; balloon tip explains missing file or launch failure
   - Rule / Global / Direct → switch mihomo proxy mode (current mode has ✓)
   - Exit　　→ quit this tool
3. Every 3 seconds the current mode and TUN state are polled; changes made elsewhere (dashboard, Clash Party, etc.) update the icon and tip.
4. Only one instance is allowed. To start with Windows: set autostart = true in Data\config.ini and restart the app (default false).

Folder layout
-------------
MihomoTray.exe
Data\config.ini              Settings (legacy config.ini next to the exe is moved here on first run)
Data\MihomoTray.exe.config   .NET runtime declaration (backup only; .NET only loads the copy next to the exe)
Data\Icons\                  Tray icons you can replace:
    tray_rule.ico     Rule
    tray_global.ico   Global
    tray_direct.ico   Direct
    tray_offline.ico  Disconnected
  Original icons are embedded: deleting a file restores it on next launch;
  corrupt, >2MB, or unreadable files fall back to the embedded icon. Restart after replacing icons.

Config (Data\config.ini — restart to apply)
-------------------------------------------
controller        mihomo external-controller address, default 127.0.0.1:9090 (port required)
                  Values like :9090 or 0.0.0.0:9090 are treated as 127.0.0.1:9090
secret            external-controller secret; leave empty if none; ASCII letters/digits/symbols only. The whole line is the secret (no trailing comments)
panel_url         URL for left-click and Dashboard
switch_program    File for Open App (.exe or .lnk); leave empty to gray out the item.
                  Spaces need no quotes (quotes OK); env vars like %LOCALAPPDATA% work;
                  relative paths are from this app's folder. Working directory is the target's folder.
switch_program_args  Extra args (usually empty). Or: switch_program = "C:\a b\x.exe" --min
poll_interval     Poll interval in seconds
close_connections Close existing connections after mode switch (default true)
language          UI language: system (follow OS) / zh (Chinese) / en (English); default system
autostart         Start with Windows, default false; true adds a MihomoTray value under HKCU\...\CurrentVersion\Run on every start,
                  setting it back to false removes that value on the next start (only its own entry)
theme             Menu theme: system / light / dark
                  Default light (matches FlClash). Use system for dark native menu on Win10 1903+.
(Comments in config.ini are bilingual — Chinese and English each on their own line.
 Missing keys from upgrades are appended automatically; existing values are kept.)

Requirements
------------
Windows 10 / 11 with built-in .NET Framework 4.x. No extra runtime.
Menus are drawn by Windows (rounded on Win11, classic on Win10).

Chinese docs: README.txt
