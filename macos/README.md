# MihomoTray（macOS）1.0.6

Mihomo 菜单栏小工具，按不同颜色图标显示当前代理模式，防止忘关全局模式；左键打开控制器面板，右键菜单切换模式，方便轻量操作 Mihomo。英文见 `README_en.md`。

## 使用方法

1. 把应用放在任意位置打开即可，菜单栏会出现 Clash 小猫图标。
   - **规则**：template 单色 CFW 猫（保留眼睛），随系统浅/深色反色
   - **全局**：红色（非 template）
   - **直连**：绿色（非 template）
   - **未连接**：灰色（非 template）
   - 鼠标悬停（已连接时 3 行，取自 mihomo `GET /configs`）：
     - 模式：规则 / 全局 / 直连
     - 日志级别：静默 / 错误 / 警告 / 信息 / 调试（未知显示 —）
     - 虚拟网卡：开启 / 关闭（对应 `tun.enable`；日志对应 `log-level`）
     - **已连接**显示模式 / 日志 / 虚拟网卡；**未连接**显示短原因（无法连接 / 鉴权失败 / 连接超时）

2. 左键：打开面板 `http://127.0.0.1:9090/ui/`（由 `panel_url` 决定）；`secret` 为空时通知提示地址，配好后停止  
   右键菜单：（**断连时**顶栏灰字状态；已连接从「打开面板」起）
   - 打开面板 → 用默认浏览器打开 `panel_url`
   - 切换程序 → 启动 `Data/config.ini` 里 `switch_program` 指定的程序；未设置则灰显；找不到或启动失败会通知说明原因
   - 规则 / 全局 / 直连 → 切换 mihomo 模式（当前模式打勾）
   - 退出

3. 默认约每 3 秒轮询模式与 TUN；在面板或其他客户端改了，图标和悬停也会变。  
4. 单实例。开机自启：将 `autostart` 改为 `true` 后重启本应用（默认 `false`），会写入 `~/Library/LaunchAgents/com.mihomotray.MihomoTray.plist`。

## 文件夹结构

```
MihomoTray.app/
Data/config.ini      配置（首次自动生成）
Data/Icons/          可选覆盖托盘图（同名 PNG；资源默认在 Assets/，含 18×18 与 @2x）
```

## 配置（`Data/config.ini`，改完请重启）

| 键 | 说明 |
|----|------|
| `controller` | mihomo external-controller，默认 `127.0.0.1:9090`，须带端口；`:9090` / `0.0.0.0:9090` 会当成 `127.0.0.1:9090` |
| `secret` | 访问密钥，在 mihomo 配置中查询填入；仅 ASCII；整行都是密钥、不支持行尾注释；打开面板时若为空会提示，配好后停止 |
| `panel_url` | 左键与「打开面板」打开的网址 |
| `switch_program` | 「切换程序」启动的路径，可留空 |
| `switch_program_args` | 附加参数，一般留空 |
| `poll_interval` | 轮询间隔（秒），默认 3 |
| `close_connections` | 切换模式后是否断开连接（默认 true） |
| `language` | `system` / `zh` / `en`（默认 system） |
| `autostart` | 开机自启（默认 false） |

无 `theme`（与 Windows 不同）。删掉 `config.ini` 会再生成默认；升级时会把缺少的新键追加到末尾，已有项不改。

## 构建（需在 Mac 上）

```bash
./build.sh          # -> dist/arm64/、dist/x86_64/、dist/universal/
./build.sh arm64    # 仅 Apple Silicon
./build.sh x86_64   # 仅 Intel
./build.sh native   # 仅本机架构
```

需要 Xcode 或 CLT（`swiftc`）。`./build.sh`（both）会再用 `lipo` 打出通用二进制（Universal 2）。发布三个 zip：`MihomoTray_macos_<版本>.zip`（通用）、`_AppleSilicon.zip`、`_Intel.zip`。

## 版本与 CI

- 发版号 `CFBundleShortVersionString` = **1.0.6**
- 构建号 `CFBundleVersion` = **1.0.6.N**（本地只加第 4 段 N）
- Actions：`build-mac.yml`；标签 `mac-v*`

未签名/未公证：首次请在 Finder 右键 → 打开。

## 常见问题

- 除 `secret` 外，值后可写 `;` / `#` 注释（前面留空格）
- 配置写错会提示并用默认值
- 图标一直灰：确认 mihomo 已开且 `external-controller` / `secret` 与 `Data/config.ini` 一致
- 切换失败会通知原因（无法连接 / 鉴权失败等）

图标设计意图：用颜色区分模式，避免全局模式开着却忘记。托盘图源自 Clash for Windows 风格小猫，红/绿/灰为调色。
