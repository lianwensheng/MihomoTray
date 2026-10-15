import Foundation

/// UI strings. language = zh / en / system (follow OS; non-zh → English).
/// Short UI strings: no trailing period unless necessary (match Windows Loc 2.1.6).
enum Loc {
    static var en = false

    static func apply(_ preference: String) {
        let p = preference.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if p == "en" { en = true }
        else if p == "zh" || p == "zh-cn" || p == "zh-tw" || p == "cn" { en = false }
        else {
            let code = Locale.current.languageCode ?? "en"
            en = code.lowercased() != "zh"
        }
    }

    static var appTitle: String { "MihomoTray" }
    static var alreadyRunning: String {
        en ? "MihomoTray is already running (check the menu bar)" : "MihomoTray 已在运行（请查看菜单栏）"
    }
    static var fatalPrefix: String {
        en ? "MihomoTray hit an error and will exit:\n" : "MihomoTray 遇到错误，即将退出：\n"
    }
    static var unknownError: String { en ? "Unknown error" : "未知错误" }

    static var openPanel: String { en ? "Dashboard" : "打开面板" }
    static var switchProgram: String { en ? "Open App" : "切换程序" }
    static var exit: String { en ? "Quit" : "退出" }
    static var modeRule: String { en ? "Rule" : "规则模式" }
    static var modeGlobal: String { en ? "Global" : "全局模式" }
    static var modeDirect: String { en ? "Direct" : "直连模式" }

    static var tipMode: String { en ? "Mode : " : "模式 : " }
    static var tipTun: String { en ? "TUN Mode : " : "虚拟网卡 : " }
    static var tipLog: String { en ? "Log Level : " : "日志级别 : " }
    static var disconnected: String { en ? "Disconnected" : "未连接" }
    /// Short tray/menu status (hover + grey menu line).
    static var statusCantConnect: String { en ? "Can't connect" : "无法连接" }
    static var statusAuthFailed: String { en ? "Auth failed" : "鉴权失败" }
    static var statusTimeout: String { en ? "Timed out" : "连接超时" }
    static var on: String { en ? "On" : "开启" }
    static var off: String { en ? "Off" : "关闭" }
    static var dash: String { "—" }

    static var logSilent: String { en ? "Silent" : "静默" }
    static var logError: String { en ? "Error" : "错误" }
    static var logWarning: String { en ? "Warn" : "警告" }
    static var logInfo: String { en ? "Info" : "信息" }
    static var logDebug: String { en ? "Debug" : "调试" }

    static var badConfig: String { en ? "Invalid config.ini" : "config.ini 有误" }
    static var switchFailed: String { en ? "Switch failed" : "切换失败" }
    static var controllerLabel: String { en ? "Controller: " : "控制器：" }
    static var cantOpenPanel: String { en ? "Couldn't open dashboard" : "无法打开面板" }
    static var cantOpenApp: String { en ? "Couldn't open app" : "无法切换程序" }
    static var switchNotSet: String {
        en ? "switch_program is not set in config.ini" : "config.ini 中没有设置 switch_program"
    }
    static func fileNotFound(_ path: String) -> String {
        en
            ? "File not found: \(path)\nCheck switch_program in config.ini"
            : "找不到文件：\(path)\n请检查 config.ini 中的 switch_program"
    }

    static var authFailed: String {
        en ? "Authentication failed. Check the secret in config.ini" : "鉴权失败，请检查 config.ini 中的 secret"
    }
    static var cantConnect: String { en ? "Can't connect to the controller" : "无法连接控制器" }
    static var controllerTimeout: String { en ? "Controller timed out" : "控制器响应超时" }
    static func controllerHttp(_ code: Int) -> String {
        en ? "Controller returned HTTP \(code)" : "控制器返回 HTTP \(code)"
    }
    static func controllerRequestFailed(_ msg: String) -> String {
        en ? "Controller request failed: \(msg)" : "请求控制器失败：\(msg)"
    }
    static func invalidController(_ addr: String) -> String {
        en ? "Invalid controller address: \(addr)" : "controller 地址无效：\(addr)"
    }
    static var badSecretChars: String {
        en
            ? "secret contains characters that can't be used in the request header (use ASCII letters, digits, and symbols only)"
            : "secret 含有请求头不支持的字符（请只用英文字母、数字和符号）"
    }
    static var cantParseConfigs: String {
        en ? "Can't parse /configs response" : "无法解析 /configs 返回内容"
    }

    static var addrEmpty: String { en ? "Address is empty" : "地址为空" }
    static var onlyHttp: String {
        en
            ? "Only http:// or https:// is supported (or omit the scheme and use 127.0.0.1:9090)"
            : "只支持 http:// 或 https://（也可以不写，直接写 127.0.0.1:9090）"
    }
    static var missingPort: String {
        en ? "Missing port or bad format (use 127.0.0.1:9090)" : "缺少端口或格式不对，应写成 127.0.0.1:9090 这样"
    }
    static func portRange(_ port: Int) -> String {
        en ? "Port \(port) is not in 1–65535" : "端口 \(port) 不在 1~65535 之间"
    }
    static var badAddrFormat: String {
        en ? "Bad address format (use 127.0.0.1:9090)" : "地址格式不对，应写成 127.0.0.1:9090 这样"
    }
    static func badPanelUrl(_ v: String) -> String {
        en
            ? "panel_url = \(v): must start with http:// or https://"
            : "panel_url = \(v)：只支持 http:// 或 https:// 开头的网址"
    }
    static func badPoll(_ v: String, _ def: Int) -> String {
        en
            ? "poll_interval = \(v): not a number, using default \(def)"
            : "poll_interval = \(v)：不是数字，已使用默认值 \(def)"
    }
    static var dataDirFailed: String {
        en
            ? "Could not create or write the Data folder; using defaults. Check folder permissions."
            : "无法创建或写入 Data 文件夹，已使用默认配置，请检查目录权限"
    }
    static var dataDirFallback: String {
        en
            ? "Could not move config into the Data folder; reading the old config.ini next to the app. Prefer fixing permissions so Data/config.ini can be used."
            : "无法把配置迁入 Data 文件夹，已临时读取应用旁旧版 config.ini，建议修好目录权限后使用 Data/config.ini"
    }
    static var autostartFailed: String {
        en ? "Couldn't update autostart" : "无法设置开机自启"
    }
    static func extraAfterQuote(_ k: String, _ rest: String) -> String {
        en
            ? "\(k): ignored extra text after the closing quote: “\(rest)”"
            : "\(k)：引号后面多出的内容“\(rest)”已忽略"
    }
}
