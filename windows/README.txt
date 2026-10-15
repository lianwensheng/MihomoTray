MihomoTray（Windows）2.1.8
========================

托盘小工具：看图标颜色切换 mihomo 规则 / 全局 / 直连（防忘关全局）。

图标
----
规则 = 原色猫　全局 = 红　直连 = 绿　未连接 = 灰

操作
----
左键　　打开面板（panel_url）；secret 为空时气泡提示地址，配好后停止
右键　　菜单：断连时顶栏灰字状态；已连接则从「打开面板」起 | 切换程序 | 模式 | 退出
悬停　　已连接显示模式 / 日志 / 虚拟网卡；未连接显示短原因
　　　　（无法连接 / 鉴权失败 / 连接超时）

配置
----
Data\config.ini（首次自动生成，改完请重启）

controller / secret / panel_url　对照 mihomo 的 external-controller 填写
switch_program　　　　　　　　　「切换程序」要启动的客户端，可留空
language = system|zh|en
theme = system|light|dark　　　　（默认 light，与 FlClash 一致）
autostart = true|false　　　　　（默认 false）

版本
----
产品版本 2.1.8；本地文件版本可带第 4 段构建号。

未签名：SmartScreen 提示时选「更多信息 → 仍要运行」。
