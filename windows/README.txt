MihomoTray（Windows）2.1.9
================================

Mihomo 托盘小工具，按不同颜色图标显示当前代理模式，防止忘关全局模式，鼠标左键快捷打开控制器面板，右键菜单切换各种模式，方便轻量模式时简单操作 Mihomo

使用方法
------------------------------------------------------
1. 把本文件夹放在任意位置，双击 MihomoTray.exe 即可，托盘里会出现一只 Clash 的小猫图标。
   - 原色（蓝）= 规则模式　红色 = 全局模式　绿色 = 直连模式　灰色 = 未连接到 mihomo
   - 鼠标悬停提示（已连接时显示 3 行，取自 mihomo 的 GET /configs）：
     模式 : 规则模式 / 全局模式 / 直连模式
     日志级别 : 静默 / 错误 / 警告 / 信息 / 调试（未知显示 —）
     虚拟网卡 : 开启 / 关闭
     虚拟网卡对应 tun.enable，日志级别对应 log-level；本小工具不检测 Windows 系统代理设置。
     已连接显示模式 / 日志级别 / 虚拟网卡；未连接显示短原因（无法连接 / 鉴权失败 / 连接超时）

2. 左键单击图标：直接打开面板 http://127.0.0.1:9090/ui/（地址由 panel_url 决定）；secret 为空时气泡提示地址，配好后停止
   右键单击图标：（断连时顶栏用灰字显示状态）
   - 打开面板　　→ 用默认浏览器打开 http://127.0.0.1:9090/ui/（地址由 panel_url 决定）
   - 切换程序　　→ 启动 Data\config.ini 里 switch_program 指定的程序（比如 Clash Verge / FlClash / Clash Party 的主程序）
                     没设置时这一项是灰色的；文件找不到或启动失败会在右下角弹提示说明原因
   - 规则模式 / 全局模式 / 直连模式 → 切换 mihomo 的代理模式（当前模式前是对勾 ✓）
   - 退出　　　　→ 退出小工具
3. 每 3 秒自动读取一次当前模式和 TUN 状态，在其他地方（面板、Clash Party 等）改了，图标和悬停提示也会跟着变。
4. 只允许运行一个实例。想开机自启：把 Data\config.ini 里的 autostart 改成 true，重启小工具即可（默认 false）。

文件夹结构
------------------------------------------------------
MihomoTray.exe
Data\config.ini                         配置文件（旧版本放在 exe 旁边的 config.ini 首次启动时会自动挪进来）
Data\MihomoTray.exe.config   .NET 运行时声明（仅作备份；.NET 只认 exe 旁边的这个文件，放在 Data 里不起作用，也不影响运行）
Data\Icons\                             托盘图标，可替换成自己的图标：
    tray_rule.ico         规则模式
    tray_global.ico     全局模式
    tray_direct.ico      直连模式
    tray_offline.ico     未连接
  原始图标已经编译进主程序：某个图标文件删掉后，下次启动会自动恢复成原始图标；
  文件损坏、超过 2MB 或读不了时也会改用原始图标。换完图标重启小工具生效。

配置（Data\config.ini，改完重启小工具生效）
------------------------------------------------------
controller                           mihomo 的 external-controller 地址，默认 127.0.0.1:9090，必须带端口
                                也可以直接照抄 mihomo 配置里的写法，:9090、0.0.0.0:9090 会自动当成 127.0.0.1:9090
secret                                external-controller 的密钥，此安全密钥在 mihomo 配置后查询并填入；请只用 ASCII 字母/数字/符号
                                这一行整行都算密钥，不支持行尾注释，打开面板时若 secret 为空会有气泡提示，配好后停止
panel_url                           左键单击和“打开面板”打开的网址
switch_program              “切换程序”要启动的文件，.exe 或 .lnk 快捷方式都行，留空则菜单项变灰。
                                路径带空格不用加引号（加了也行）；可以用环境变量，如 %LOCALAPPDATA%；
                                相对路径按本小工具 exe 所在的文件夹算。程序会在它自己所在的文件夹里启动。
                                例：switch_program = C:\Program Files\FlClash\FlClash.exe
                                      switch_program = %LOCALAPPDATA%\Programs\某客户端\某客户端.exe
                                      switch_program = ..\快捷方式\Clash Verge.lnk
switch_program_args          启动时附带的命令行参数，一般留空（原样传给程序，引号保留）
                                也可以写成 switch_program = "C:\a b\x.exe" --min，引号后面的部分会当作参数
poll_interval                        轮询间隔（秒）
close_connections               切换模式后是否断开现有连接（默认 true，旧连接也立即按新模式走）
language                            界面语言：system 跟随系统 / zh 中文 / en 英文（默认 system）
autostart                            开机自启，默认 false；改成 true 后每次启动会在 HKCU\...\CurrentVersion\Run 写入 MihomoTray 启动项，
                                改回 false 再启动一次会删掉这个启动项（只删自己的，不碰别的启动项）
theme                                菜单主题：system 跟随系统 / light 浅色 / dark 深色
                                默认 light：FlClash 原版没有开启原生菜单的深色模式，系统用深色时它的菜单也还是浅色；
                                想让原生菜单跟着系统变深色就改成 system（需要 Win10 1903 及以上）
（ 删掉 config.ini 后再次启动会自动生成默认配置；从旧版本升级时，config.ini 里缺少的新配置项会被自动追加到文件末尾，已有的不会被改动）

运行环境
------------------------------------------------------
Windows 10 / 11 自带的 .NET Framework 4.x 即可，无需安装其它运行库。
菜单由 Windows 自己绘制：Win11 自带圆角和阴影，Win10 是传统直角菜单。
未签名：SmartScreen 提示时选「更多信息 → 仍要运行」

常见问题
------------------------------------------------------
- 除了 secret，每一行的值后面都可以写注释，前面留个空格再写 ; 或 #，例如 poll_interval = 5 ; 秒
- Data\config.ini 里有写错的项（地址格式不对、不是数字等），启动时会弹提示指出是哪一项，并改用默认值
- 图标一直是灰色：确认 mihomo 正在运行，且配置里开了 external-controller（如 external-controller: 127.0.0.1:9090），
  地址/secret 与 Data\config.ini 一致。
- 切换失败会在右下角弹出提示，说明原因（无法连接 / 鉴权失败等）。
- 部分杀毒软件可能对未签名的小工具误报，可自行添加信任。

图标说明：托盘图标取自 Clash for Windows 0.20.39 安装包内的原版 tray_normal.ico，红/绿/灰色为在原图基础上调色生成。

自己编译
------------------------------------------------------
在合仓 windows 目录双击 build.bat（或运行 build.sh），生成 dist\MihomoTray.exe，以及 dist\Data\（config.ini、MihomoTray.exe.config、Icons\）。

英文说明见同目录 README_en.txt。
