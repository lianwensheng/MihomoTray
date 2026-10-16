MihomoTray (Windows) 2.3.5
================================

Mihomo tray helper. Colored icons show the current proxy mode so you notice if Global was left on. Left-click opens the controller dashboard; right-click switches modes — handy when you only need light control of Mihomo.

Usage
------------------------------------------------------
1. Put this folder anywhere and double-click MihomoTray.exe. A Clash cat icon appears in the tray.
   - Original (blue) = Rule　Red = Global　Green = Direct　Grey = not connected to mihomo
   - Hover tip (3 lines when connected, from mihomo GET /configs):
     Mode : Rule / Global / Direct
     Log level : Silent / Error / Warning / Info / Debug (unknown shows —)
     TUN : On / Off
     TUN maps to tun.enable; log level maps to log-level. This tool does not read Windows system proxy settings.
     When connected: mode / log level / TUN; when offline: a short reason (Can't connect / Auth failed / Timed out)

2. Left-click: open the dashboard http://127.0.0.1:9090/ui/ (from panel_url); while secret is empty a balloon shows the URL — set secret to stop
   Right-click: (grey status line at the top only when offline)
   - Open panel　→ open http://127.0.0.1:9090/ui/ in the default browser (from panel_url)
   - Open app　　→ launch the program set by switch_program in Data\config.ini (e.g. Clash Verge / FlClash / Clash Party)
                     Greyed out if unset; missing file or launch failure shows a balloon with the reason
   - Rule / Global / Direct → switch mihomo mode (current mode has a check mark)
   - Exit　　　　→ quit
3. Every 3 seconds it re-reads mode and TUN. Changes made elsewhere (dashboard, Clash Party, etc.) update the icon and hover tip.
4. Single instance only. For autostart set autostart = true in Data\config.ini and restart (default false).

Folder layout
------------------------------------------------------
MihomoTray.exe
Data\config.ini                         Config (legacy config.ini next to the exe is moved here on first run)
Data\MihomoTray.exe.config   .NET runtime hint (backup only; .NET only loads the copy next to the exe — the one in Data is unused and harmless)
Data\Icons\                             Tray icons you can replace:
    tray_rule.ico         Rule
    tray_global.ico     Global
    tray_direct.ico      Direct
    tray_offline.ico     Offline
  Original icons are embedded: if a file is deleted it is restored on next start;
  corrupt, over 2MB, or unreadable files fall back to the embedded icon. Restart after replacing icons.

Config (Data\config.ini — restart after edits)
------------------------------------------------------
controller                           mihomo external-controller address, default 127.0.0.1:9090, port required
                                You can copy mihomo's form; :9090 and 0.0.0.0:9090 become 127.0.0.1:9090
secret                                external-controller access key — look it up in your mihomo config and fill it in; ASCII letters/digits/symbols only
                                The whole line is the key (no trailing comments). Opening the panel while secret is empty shows a balloon tip; set secret to stop
panel_url                           URL opened by left-click and "Open panel"
switch_program              File launched by "Open app" (.exe or .lnk). Leave empty to grey out the item.
                                Spaces in the path need no quotes (quotes OK). Env vars like %LOCALAPPDATA% work;
                                relative paths are from this tool's exe folder. The program starts in its own folder.
                                Examples: switch_program = C:\Program Files\FlClash\FlClash.exe
                                      switch_program = %LOCALAPPDATA%\Programs\SomeClient\SomeClient.exe
                                      switch_program = ..\Shortcuts\Clash Verge.lnk
switch_program_args          Extra command-line args (usually empty; passed as-is, quotes kept)
                                Or: switch_program = "C:\a b\x.exe" --min — text after the quoted path is treated as args
poll_interval                        Poll interval in seconds
close_connections               Disconnect existing connections after a mode switch (default true)
language                            UI language: system / zh / en (default system)
autostart                            Autostart, default false; true writes HKCU\...\CurrentVersion\Run\MihomoTray;
                                set back to false and start once to remove only this entry
theme                                Menu theme: system / light / dark
                                Default light (FlClash-like: native menu stays light under dark system theme);
                                use system to follow OS dark mode (Windows 10 1903+)
( Delete config.ini and restart to regenerate defaults; upgrading appends missing keys at the end without changing existing ones )

Runtime
------------------------------------------------------
Windows 10 / 11 with built-in .NET Framework 4.x — no extra runtime.
Menus are drawn by Windows: Win11 rounded/shadow; Win10 classic.
Unsigned: if SmartScreen warns, choose More info → Run anyway

FAQ
------------------------------------------------------
- Except secret, values may have trailing comments after a space and ; or #, e.g. poll_interval = 5 ; seconds
- Bad entries in Data\config.ini (bad address, not a number, etc.) show a balloon naming the key and fall back to defaults
- Icon stays grey: confirm mihomo is running with external-controller (e.g. external-controller: 127.0.0.1:9090),
  and that address/secret match Data\config.ini.
- Switch failures show a balloon with the reason (Can't connect / Auth failed / etc.).
- Some antivirus may flag unsigned helpers — add an exclusion if needed.

Icons: tray art from Clash for Windows 0.20.39 tray_normal.ico; red/green/grey are recolors of that original.

Build from source
------------------------------------------------------
In the monorepo windows folder run build.bat (or build.sh) to produce dist\MihomoTray.exe and dist\Data\ (config.ini, MihomoTray.exe.config, Icons\).

Chinese: README.txt in the same folder.
