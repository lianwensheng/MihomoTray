MihomoTray (Windows) 2.1.8
==========================

Tray helper to switch mihomo mode: Rule / Global / Direct.

Icons
-----
Rule = original cat, Global = red, Direct = green, Offline = grey

Usage
-----
Left-click   Open dashboard (panel_url)
Right-click  Menu: status (grey) | Open panel / Open app | modes | Exit
Hover        When connected: mode / log / TUN; when offline: short reason
             (Can't connect / Auth failed / Timed out)

Config
------
Data\config.ini (created on first run; restart after edits)

controller / secret / panel_url   match mihomo external-controller
switch_program                    optional GUI client to launch
language = system|zh|en
theme = system|light|dark         (default light, FlClash-like)
autostart = true|false            (default false)

Version
-------
Product 2.1.8; local FileVersion may add a 4th build segment.

Unsigned: if SmartScreen warns, More info → Run anyway.
