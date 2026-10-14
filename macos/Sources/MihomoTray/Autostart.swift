import Foundation

/// 开机自启：~/Library/LaunchAgents/com.mihomotray.MihomoTray.plist（RunAtLoad，用 /usr/bin/open 打开本 .app）。
/// 每次启动按 config.ini 的 autostart 同步：true 写入/更新，false 只删除自己这个 plist。
/// 目标系统是 macOS 12，所以不用 macOS 13 才有的 SMAppService。
enum Autostart {
    static let label = "com.mihomotray.MihomoTray"

    static var plistPath: String {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        return (home as NSString).appendingPathComponent("Library/LaunchAgents/\(label).plist")
    }

    /// 本程序的 .app 路径；不是从 .app 里运行时退回可执行文件本身。
    static var launchTarget: [String] {
        let bundle = Bundle.main.bundlePath
        if bundle.hasSuffix(".app") { return ["/usr/bin/open", bundle] }
        return [Bundle.main.executablePath ?? CommandLine.arguments[0]]
    }

    static func plistData(_ args: [String]) -> Data? {
        let dict: [String: Any] = [
            "Label": label,
            "ProgramArguments": args,
            "RunAtLoad": true,
            "ProcessType": "Interactive",
        ]
        return try? PropertyListSerialization.data(fromPropertyList: dict, format: .xml, options: 0)
    }

    /// 成功返回 nil，失败返回原因。
    static func sync(_ enabled: Bool) -> String? {
        let fm = FileManager.default
        let path = plistPath
        if !enabled {
            guard fm.fileExists(atPath: path) else { return nil }
            do { try fm.removeItem(atPath: path) } catch { return error.localizedDescription }
            return nil
        }
        guard let data = plistData(launchTarget) else { return "plist" }
        if let cur = fm.contents(atPath: path), cur == data { return nil }
        do {
            try fm.createDirectory(atPath: (path as NSString).deletingLastPathComponent, withIntermediateDirectories: true)
            try data.write(to: URL(fileURLWithPath: path), options: .atomic)
        } catch { return error.localizedDescription }
        return nil
    }
}
