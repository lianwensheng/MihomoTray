import Foundation

struct MihomoStatus {
    var mode: String = ""
    var tunEnabled: Bool = false
    var logLevel: String = ""
}

enum MihomoError: Error, LocalizedError {
    case message(String)
    var errorDescription: String? {
        switch self {
        case .message(let m): return m
        }
    }
}

/// Minimal mihomo external-controller REST client.
final class MihomoClient {
    private let base: String
    private let secret: String
    var timeoutMs: Int = 2000

    init(controller: String, secret: String) {
        self.base = AppConfig.normalizeController(controller)
        self.secret = secret
    }

    private func request(method: String, path: String, jsonBody: String?) throws -> String {
        for ch in secret.utf8 {
            if ch > 127 { throw MihomoError.message(Loc.badSecretChars) }
        }
        guard let url = URL(string: base + path) else {
            throw MihomoError.message(Loc.invalidController(base))
        }
        var req = URLRequest(url: url, timeoutInterval: TimeInterval(timeoutMs) / 1000.0)
        req.httpMethod = method
        req.setValue("MihomoTray/1.0.6", forHTTPHeaderField: "User-Agent")
        req.cachePolicy = .reloadIgnoringLocalCacheData
        if !secret.isEmpty {
            req.setValue("Bearer \(secret)", forHTTPHeaderField: "Authorization")
        }
        if let jsonBody = jsonBody {
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = jsonBody.data(using: .utf8)
        }

        // Bypass system proxy (may be mihomo itself)
        let config = URLSessionConfiguration.ephemeral
        config.connectionProxyDictionary = [:]
        config.timeoutIntervalForRequest = TimeInterval(timeoutMs) / 1000.0
        config.timeoutIntervalForResource = TimeInterval(timeoutMs) / 1000.0
        let session = URLSession(configuration: config)

        let sem = DispatchSemaphore(value: 0)
        var dataOut: Data?
        var respOut: URLResponse?
        var errOut: Error?
        session.dataTask(with: req) { data, resp, err in
            dataOut = data
            respOut = resp
            errOut = err
            sem.signal()
        }.resume()
        let wait = sem.wait(timeout: .now() + .milliseconds(timeoutMs + 500))
        if wait == .timedOut {
            throw MihomoError.message(Loc.controllerTimeout)
        }
        if let err = errOut {
            let ns = err as NSError
            if ns.domain == NSURLErrorDomain && ns.code == NSURLErrorTimedOut {
                throw MihomoError.message(Loc.controllerTimeout)
            }
            throw MihomoError.message(Loc.cantConnect)
        }
        guard let http = respOut as? HTTPURLResponse else {
            throw MihomoError.message(Loc.cantConnect)
        }
        let code = http.statusCode
        if code == 401 || code == 403 {
            throw MihomoError.message(Loc.authFailed)
        }
        if code < 200 || code >= 300 {
            throw MihomoError.message(Loc.controllerHttp(code))
        }
        return String(data: dataOut ?? Data(), encoding: .utf8) ?? ""
    }

    func getStatus() throws -> MihomoStatus {
        try Self.parseStatus(request(method: "GET", path: "/configs", jsonBody: nil))
    }

    func setMode(_ mode: String) throws {
        _ = try request(method: "PATCH", path: "/configs", jsonBody: "{\"mode\":\"\(mode)\"}")
    }

    func closeAllConnections() throws {
        _ = try request(method: "DELETE", path: "/connections", jsonBody: nil)
    }

    static func parseStatus(_ json: String) throws -> MihomoStatus {
        var st = MihomoStatus()
        st.mode = try parseMode(json)
        st.tunEnabled = parseTunEnabled(json)
        st.logLevel = parseLogLevel(json)
        return st
    }

    static func parseTunEnabled(_ json: String) -> Bool {
        guard let tun = MiniJson.topLevel(json)["tun"], tun.hasPrefix("{") else { return false }
        return MiniJson.topLevel(tun)["enable"] == "true"
    }

    static func parseLogLevel(_ json: String) -> String {
        guard let v = MiniJson.topLevel(json)["log-level"], v.count >= 2, v.first == "\"" else { return "" }
        return String(v.dropFirst().dropLast()).lowercased()
    }

    static func parseMode(_ json: String) throws -> String {
        guard let v = MiniJson.topLevel(json)["mode"],
              v.count >= 2, v.first == "\"", v.last == "\"",
              v.dropFirst().dropLast().allSatisfy({ $0.isLetter }) else {
            throw MihomoError.message(Loc.cantParseConfigs)
        }
        return String(v.dropFirst().dropLast()).lowercased()
    }
}

enum TrayTip {
    static var offline: String { Loc.disconnected }

    static func modeLabel(_ mode: String?) -> String {
        switch mode {
        case "rule": return Loc.modeRule
        case "global": return Loc.modeGlobal
        case "direct": return Loc.modeDirect
        default: return mode ?? ""
        }
    }

    static func logLabel(_ level: String?) -> String {
        switch level {
        case "silent": return Loc.logSilent
        case "error": return Loc.logError
        case "warning", "warn": return Loc.logWarning
        case "info": return Loc.logInfo
        case "debug": return Loc.logDebug
        default: return Loc.dash
        }
    }

    static func text(connected: Bool, mode: String?, tunEnabled: Bool, logLevel: String?) -> String {
        let m: String
        if connected {
            let ml = modeLabel(mode)
            m = ml.isEmpty ? Loc.dash : ml
        } else {
            m = Loc.disconnected
        }
        let tun = connected ? (tunEnabled ? Loc.on : Loc.off) : Loc.dash
        let log = connected ? logLabel(logLevel) : Loc.dash
        return Loc.tipMode + m + "\n" + Loc.tipLog + log + "\n" + Loc.tipTun + tun
    }
}

/// Minimal JSON scanner: top-level object key → raw value text.
enum MiniJson {
    static func topLevel(_ json: String?) -> [String: String] {
        var d: [String: String] = [:]
        guard let json = json else { return d }
        var i = skipWs(json, 0)
        guard i < json.count, char(json, i) == "{" else { return d }
        i += 1
        let n = json.count
        while i < n {
            i = skipWs(json, i)
            if i >= n || char(json, i) == "}" { break }
            if char(json, i) == "," { i += 1; continue }
            if char(json, i) != "\"" { break }
            guard let ke = endOfString(json, i) else { break }
            let key = substring(json, i + 1, ke - 1)
            i = skipWs(json, ke)
            if i >= n || char(json, i) != ":" { break }
            i = skipWs(json, i + 1)
            guard let ve = endOfValue(json, i) else { break }
            d[key] = substring(json, i, ve).trimmingCharacters(in: .whitespacesAndNewlines)
            i = ve
        }
        return d
    }

    private static func skipWs(_ s: String, _ i: Int) -> Int {
        var j = i
        while j < s.count {
            let c = char(s, j)
            if c == " " || c == "\t" || c == "\n" || c == "\r" { j += 1 } else { break }
        }
        return j
    }

    private static func endOfString(_ s: String, _ i: Int) -> Int? {
        var j = i + 1
        while j < s.count {
            let c = char(s, j)
            if c == "\\" { j += 2; continue }
            if c == "\"" { return j + 1 }
            j += 1
        }
        return nil
    }

    private static func endOfValue(_ s: String, _ i: Int) -> Int? {
        guard i < s.count else { return nil }
        let c = char(s, i)
        if c == "\"" { return endOfString(s, i) }
        if c == "{" || c == "[" {
            var depth = 0
            var j = i
            while j < s.count {
                let ch = char(s, j)
                if ch == "\"" {
                    guard let e = endOfString(s, j) else { return nil }
                    j = e
                    continue
                }
                if ch == "{" || ch == "[" { depth += 1 }
                else if ch == "}" || ch == "]" {
                    depth -= 1
                    if depth == 0 { return j + 1 }
                }
                j += 1
            }
            return nil
        }
        var k = i
        while k < s.count {
            let ch = char(s, k)
            if ch == "," || ch == "}" || ch == "]" { break }
            k += 1
        }
        return k
    }

    private static func char(_ s: String, _ i: Int) -> Character {
        s[s.index(s.startIndex, offsetBy: i)]
    }

    private static func substring(_ s: String, _ start: Int, _ end: Int) -> String {
        let a = s.index(s.startIndex, offsetBy: start)
        let b = s.index(s.startIndex, offsetBy: end)
        return String(s[a..<b])
    }
}
