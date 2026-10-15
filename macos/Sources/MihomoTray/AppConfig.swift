import Foundation

/// Reads config.ini next to the app (Data/config.ini), same keys as Windows MihomoTray.
final class AppConfig {
    var controller = "http://127.0.0.1:9090"
    var secret = ""
    var panelUrl = "http://127.0.0.1:9090/ui/"
    var switchProgram = ""
    var switchProgramArgs = ""
    private var switchProgramArgsInline = ""
    var pollSeconds = 3
    var closeConnections = true
    var language = "system"
    var autostart = false
    var errors: [String] = []

    var hasSwitchProgram: Bool { !switchProgram.isEmpty }

    var effectiveSwitchArgs: String {
        if switchProgramArgsInline.isEmpty { return switchProgramArgs }
        if switchProgramArgs.isEmpty { return switchProgramArgsInline }
        return switchProgramArgsInline + " " + switchProgramArgs
    }

    static let defaultIni = """
; MihomoTray 配置文件（修改后重启 MihomoTray 生效）
; MihomoTray config (restart MihomoTray after editing)

[mihomo]
; external-controller 地址，自定义地址在 mihomo 配置里查询并更换
; external-controller address — look it up in the mihomo config
controller = 127.0.0.1:9090

; external-controller 的 secret，没有就留空（请只用 ASCII 字母、数字和符号）
; secret for external-controller (leave empty if none; ASCII letters/digits/symbols only)
secret = 

; 点击“打开面板”时打开的网址，自定义网址在 mihomo 配置里查询并更换
; URL opened by Dashboard / left-click — look it up in the mihomo config
panel_url = http://127.0.0.1:9090/ui/

; 点击“切换程序”时启动的程序（.app / 可执行文件），留空则该菜单项变灰
; Program launched by Open App (.app / binary); leave empty to gray out the item
; 支持 ~、环境变量、相对路径（相对本应用所在文件夹）
; Paths may use ~, env vars, or be relative to this app's folder
; switch_program = /Applications/某客户端.app
; switch_program = /Applications/SomeClient.app
; switch_program = ~/Applications/SomeClient.app
switch_program = 

; 启动上面程序时附带的命令行参数，一般留空
; Extra command-line args for the program above (usually empty)
switch_program_args = 

; 轮询当前模式的间隔（秒）
; Poll interval for current mode (seconds)
poll_interval = 3

; 切换模式后是否断开现有连接，让已建立的连接也立即按新模式走（设为 false 则只影响新连接）
; Close existing connections after switching mode (false = only new connections use the new mode)
close_connections = true

[ui]
; 界面语言：system（跟随系统）/ zh（中文）/ en（英文）
; UI language: system (follow OS) / zh (Chinese) / en (English)
language = system

; 开机自启：true（开启）/ false（关闭，默认）；每次启动时按这里同步系统设置
; Start at login: true / false (default); synced to the system on every start
autostart = false
"""

    static var appDir: String {
        // Prefer bundle parent when running as .app; else executable directory
        let exe = Bundle.main.executableURL?.deletingLastPathComponent().path
            ?? FileManager.default.currentDirectoryPath
        // If inside Foo.app/Contents/MacOS, use Foo.app's parent for Data/
        if exe.hasSuffix("/Contents/MacOS") {
            var p = (exe as NSString).deletingLastPathComponent // Contents
            p = (p as NSString).deletingLastPathComponent       // Foo.app
            p = (p as NSString).deletingLastPathComponent       // parent folder
            return p
        }
        return exe
    }

    static var dataDir: String { (appDir as NSString).appendingPathComponent("Data") }
    static var iconsDir: String { (dataDir as NSString).appendingPathComponent("Icons") }
    static var iniPath: String { (dataDir as NSString).appendingPathComponent("config.ini") }

    /// Sidecar next to config.ini for the one-time first-open panel tip (not written into the ini).
    static var panelTipMarkerPath: String {
        let dir = FileManager.default.fileExists(atPath: dataDir) ? dataDir : appDir
        return (dir as NSString).appendingPathComponent(".panel_tip_shown")
    }

    /// Returns true once: creates the marker; false if already shown or cannot write.
    static func tryClaimPanelTip() -> Bool {
        let path = panelTipMarkerPath
        if FileManager.default.fileExists(atPath: path) { return false }
        do {
            let dir = (path as NSString).deletingLastPathComponent
            try FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
            try "1".write(toFile: path, atomically: true, encoding: .utf8)
            return true
        } catch {
            return false
        }
    }

    @discardableResult
    static func prepareDataDir() -> Bool {
        do {
            try FileManager.default.createDirectory(atPath: dataDir, withIntermediateDirectories: true)
            let legacy = (appDir as NSString).appendingPathComponent("config.ini")
            if FileManager.default.fileExists(atPath: legacy),
               !FileManager.default.fileExists(atPath: iniPath) {
                try FileManager.default.moveItem(atPath: legacy, toPath: iniPath)
            }
            return FileManager.default.fileExists(atPath: dataDir)
        } catch {
            return false
        }
    }

    static func load() -> AppConfig {
        let dataOk = prepareDataDir()
        let c = AppConfig()
        var path = iniPath
        let legacy = (appDir as NSString).appendingPathComponent("config.ini")
        var usedLegacy = false
        do {
            if !FileManager.default.fileExists(atPath: path),
               FileManager.default.fileExists(atPath: legacy) {
                path = legacy
                usedLegacy = true
            } else if !FileManager.default.fileExists(atPath: path) {
                if dataOk {
                    try defaultIni.write(toFile: path, atomically: true, encoding: .utf8)
                }
            }
        } catch {}
        if FileManager.default.fileExists(atPath: path),
           let text = try? String(contentsOfFile: path, encoding: .utf8) {
            c.parse(text.components(separatedBy: .newlines))
        }
        Loc.apply(c.language)
        if usedLegacy {
            c.errors.insert(Loc.dataDirFallback, at: 0)
        } else if !dataOk && !FileManager.default.fileExists(atPath: iniPath)
                    && !FileManager.default.fileExists(atPath: legacy) {
            c.errors.insert(Loc.dataDirFailed, at: 0)
        }
        return c
    }

    func parse(_ lines: [String]) {
        // First pass: language
        for raw in lines {
            let line = raw.trimmingCharacters(in: .whitespaces)
            if line.isEmpty || line.hasPrefix(";") || line.hasPrefix("#") || line.hasPrefix("[") { continue }
            guard let eq = line.firstIndex(of: "=") else { continue }
            let k = line[..<eq].trimmingCharacters(in: .whitespaces).lowercased()
            if k != "language" { continue }
            var rest = ""
            var v = Self.unquote(Self.stripComment(String(line[line.index(after: eq)...]).trimmingCharacters(in: .whitespaces)), rest: &rest).lowercased()
            if v == "system" || v == "zh" || v == "en" { language = v }
        }
        Loc.apply(language)

        for raw in lines {
            let line = raw.trimmingCharacters(in: .whitespaces)
            if line.isEmpty || line.hasPrefix(";") || line.hasPrefix("#") || line.hasPrefix("[") { continue }
            guard let eq = line.firstIndex(of: "=") else { continue }
            let k = line[..<eq].trimmingCharacters(in: .whitespaces).lowercased()
            let value = String(line[line.index(after: eq)...]).trimmingCharacters(in: .whitespaces)
            let rawValue = k == "secret" ? value : Self.stripComment(value)
            var rest = ""
            var v: String
            if k == "secret" {
                if value.count >= 2, value.first == "\"", value.last == "\"" {
                    v = String(value.dropFirst().dropLast())
                } else {
                    v = value
                }
                rest = ""
            } else {
                v = Self.unquote(rawValue, rest: &rest)
            }
            if !rest.isEmpty && k != "switch_program" && k != "switch_program_args" {
                errors.append(Loc.extraAfterQuote(k, rest))
            }
            switch k {
            case "controller":
                if !v.isEmpty {
                    var err: String?
                    if let norm = Self.tryNormalizeController(v, error: &err) {
                        controller = norm
                    } else {
                        errors.append("controller = \(v)" + (Loc.en ? ": " : "：") + (err ?? ""))
                    }
                }
            case "secret":
                secret = v
            case "panel_url":
                if !v.isEmpty {
                    if let u = URL(string: v), u.scheme == "http" || u.scheme == "https" {
                        panelUrl = v
                    } else {
                        errors.append(Loc.badPanelUrl(v))
                    }
                }
            case "switch_program":
                switchProgram = v.trimmingCharacters(in: .whitespaces)
                if !rest.isEmpty { switchProgramArgsInline = rest }
            case "switch_program_args":
                switchProgramArgs = rawValue
            case "poll_interval":
                if let n = Int(v) {
                    pollSeconds = max(1, min(60, n))
                } else {
                    errors.append(Loc.badPoll(v, pollSeconds))
                }
            case "close_connections":
                let lv = v.lowercased()
                closeConnections = !(lv == "false" || lv == "0" || lv == "no" || lv == "off")
            case "autostart":
                let lv = v.lowercased()
                autostart = lv == "true" || lv == "1" || lv == "yes" || lv == "on"
            case "language":
                break
            default:
                break
            }
        }
    }

    static func stripComment(_ v: String) -> String {
        var inQ = false
        let chars = Array(v)
        for i in 0..<chars.count {
            let c = chars[i]
            if c == "\"" { inQ.toggle() }
            else if !inQ && (c == ";" || c == "#") && i > 0 && chars[i - 1].isWhitespace {
                return String(chars[0..<i]).trimmingCharacters(in: .whitespaces)
            }
        }
        return v
    }

    static func unquote(_ v: String, rest: inout String) -> String {
        rest = ""
        if v.first == "\"" {
            if let end = v.dropFirst().firstIndex(of: "\"") {
                rest = String(v[v.index(after: end)...]).trimmingCharacters(in: .whitespaces)
                return String(v[v.index(after: v.startIndex)..<end])
            }
        }
        return v
    }

    static func resolveProgramPath(_ raw: String?, baseDir: String) -> String? {
        guard var p = raw?.trimmingCharacters(in: .whitespaces), !p.isEmpty else { return nil }
        var rest = ""
        p = unquote(p, rest: &rest).trimmingCharacters(in: CharacterSet(charactersIn: "\""))
        if p.isEmpty { return nil }
        if p.hasPrefix("~") {
            p = NSString(string: p).expandingTildeInPath
        }
        // Expand $VAR and ${VAR}
        if let regex = try? NSRegularExpression(pattern: #"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?"#) {
            let ns = p as NSString
            let matches = regex.matches(in: p, range: NSRange(location: 0, length: ns.length)).reversed()
            var out = p
            for m in matches {
                let name = ns.substring(with: m.range(at: 1))
                let val = ProcessInfo.processInfo.environment[name] ?? ""
                let r = Range(m.range, in: out)!
                out.replaceSubrange(r, with: val)
            }
            p = out
        }
        if !p.hasPrefix("/") {
            p = (baseDir as NSString).appendingPathComponent(p)
        }
        return (p as NSString).standardizingPath
    }

    static func normalizeController(_ v: String) -> String {
        var err: String?
        return tryNormalizeController(v, error: &err) ?? basicNormalize(v)
    }

    private static func basicNormalize(_ v: String) -> String {
        var s = v.trimmingCharacters(in: .whitespaces).trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        if !s.lowercased().hasPrefix("http://") && !s.lowercased().hasPrefix("https://") {
            s = "http://" + s
        }
        return s
    }

    static func tryNormalizeController(_ v: String, error: inout String?) -> String? {
        var v = v.trimmingCharacters(in: .whitespaces)
        if v.isEmpty { error = Loc.addrEmpty; return nil }
        var scheme = "http://"
        if v.lowercased().hasPrefix("http://") { v = String(v.dropFirst(7)) }
        else if v.lowercased().hasPrefix("https://") { scheme = "https://"; v = String(v.dropFirst(8)) }
        else if v.contains("://") { error = Loc.onlyHttp; return nil }
        while v.hasSuffix("/") { v = String(v.dropLast()) }
        if v == "0.0.0.0" || v == "[::]" || v == "::" { v = "127.0.0.1" }
        else if v.hasPrefix(":") { v = "127.0.0.1" + v }
        else if v.hasPrefix("0.0.0.0:") { v = "127.0.0.1" + String(v.dropFirst(7)) }
        else if v.hasPrefix("[::]:") { v = "127.0.0.1" + String(v.dropFirst(4)) }
        var hostPort = v
        if let slash = hostPort.firstIndex(of: "/") {
            hostPort = String(hostPort[..<slash])
        }
        // host:port or [ipv6]:port
        let pattern = #"^(\[[0-9A-Fa-f:.]+\]|[^:\[\]]+):(\d{1,5})$"#
        guard let re = try? NSRegularExpression(pattern: pattern),
              let m = re.firstMatch(in: hostPort, range: NSRange(location: 0, length: (hostPort as NSString).length)) else {
            error = Loc.missingPort
            return nil
        }
        let portStr = (hostPort as NSString).substring(with: m.range(at: 2))
        guard let port = Int(portStr), port >= 1, port <= 65535 else {
            error = Loc.portRange(Int(portStr) ?? 0)
            return nil
        }
        let url = scheme + v
        guard let u = URL(string: url), u.host != nil, !v.contains(" ") else {
            error = Loc.badAddrFormat
            return nil
        }
        return url
    }
}

