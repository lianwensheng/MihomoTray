import AppKit
import Foundation

/// Menubar status item: poll mihomo, switch modes, open dashboard.
final class TrayController: NSObject {
    private static let modes = ["rule", "global", "direct"]

    private let cfg: AppConfig
    private let client: MihomoClient
    private var statusItem: NSStatusItem!
    private var timer: Timer?
    private var icons: [String: NSImage] = [:]
    private var mode: String?
    private var connected = false
    private var disposed = false
    private var polling = false
    private var switching = 0
    private var switchSeq = 0
    private var lastPanelOpen = Date.distantPast
    private var menu = NSMenu()

    init(cfg: AppConfig) {
        self.cfg = cfg
        self.client = MihomoClient(controller: cfg.controller, secret: cfg.secret)
        super.init()
        loadIcons()

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let btn = statusItem.button {
            btn.image = icons["offline"]
            btn.imagePosition = .imageOnly
            btn.toolTip = TrayTip.offline
            btn.target = self
            btn.action = #selector(statusItemAction(_:))
            btn.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }

        rebuildMenu()
        let interval = TimeInterval(max(1, cfg.pollSeconds))
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            self?.poll()
        }
        RunLoop.main.add(timer!, forMode: .common)
        poll()

        if let err = Autostart.sync(cfg.autostart) {
            cfg.errors.append(Loc.autostartFailed + (Loc.en ? ": " : "：") + err)
        }

        if !cfg.errors.isEmpty {
            warn(Loc.badConfig, cfg.errors.joined(separator: "\n"))
        }
    }

    private func loadIcons() {
        for name in ["rule", "global", "direct", "offline"] {
            icons[name] = Self.loadIcon(named: name)
        }
    }

    /// rule → template mono; global/direct/offline → colored non-template
    private static func loadIcon(named name: String) -> NSImage {
        let fm = FileManager.default
        var urls: [URL] = []

        let overrideDir = AppConfig.iconsDir
        urls.append(URL(fileURLWithPath: (overrideDir as NSString).appendingPathComponent("tray_\(name)@2x.png")))
        urls.append(URL(fileURLWithPath: (overrideDir as NSString).appendingPathComponent("tray_\(name).png")))

        if let u = Bundle.main.url(forResource: "tray_\(name)", withExtension: "png", subdirectory: nil) {
            let two = u.deletingLastPathComponent().appendingPathComponent("tray_\(name)@2x.png")
            if fm.fileExists(atPath: two.path) { urls.append(two) }
            urls.append(u)
        }
        // Resource folder copy inside bundle
        if let res = Bundle.main.resourceURL {
            urls.append(res.appendingPathComponent("tray_\(name)@2x.png"))
            urls.append(res.appendingPathComponent("tray_\(name).png"))
            urls.append(res.appendingPathComponent("Assets/tray_\(name)@2x.png"))
            urls.append(res.appendingPathComponent("Assets/tray_\(name).png"))
        }

        let cwd = fm.currentDirectoryPath
        for root in [cwd, (cwd as NSString).appendingPathComponent("Assets"),
                     ((Bundle.main.bundlePath as NSString).deletingLastPathComponent as NSString).appendingPathComponent("Assets")] {
            urls.append(URL(fileURLWithPath: (root as NSString).appendingPathComponent("tray_\(name)@2x.png")))
            urls.append(URL(fileURLWithPath: (root as NSString).appendingPathComponent("tray_\(name).png")))
        }

        for u in urls {
            guard fm.fileExists(atPath: u.path), let img = NSImage(contentsOf: u) else { continue }
            img.size = NSSize(width: 18, height: 18)
            img.isTemplate = (name == "rule")
            return img
        }

        let fallback = NSImage(size: NSSize(width: 18, height: 18))
        fallback.isTemplate = true
        return fallback
    }

    @objc private func statusItemAction(_ sender: Any?) {
        guard let event = NSApp.currentEvent else { return }
        if event.type == .rightMouseUp {
            poll()
            rebuildMenu()
            if let btn = statusItem.button {
                // Pop up menu under the status item
                let ep = btn.convert(btn.bounds.origin, to: nil)
                menu.popUp(positioning: nil, at: NSPoint(x: ep.x, y: ep.y - 4), in: btn)
            }
            return
        }
        if Date().timeIntervalSince(lastPanelOpen) < 0.8 { return }
        lastPanelOpen = Date()
        openPanel()
    }

    private func rebuildMenu() {
        menu.removeAllItems()
        menu.autoenablesItems = false

        let dash = menu.addItem(withTitle: Loc.openPanel, action: #selector(openPanel), keyEquivalent: "")
        dash.target = self

        let sw = menu.addItem(withTitle: Loc.switchProgram, action: #selector(launchSwitchProgram), keyEquivalent: "")
        sw.target = self
        sw.isEnabled = cfg.hasSwitchProgram

        menu.addItem(.separator())

        for m in Self.modes {
            let label = m == "rule" ? Loc.modeRule : m == "global" ? Loc.modeGlobal : Loc.modeDirect
            let item = menu.addItem(withTitle: label, action: #selector(switchModeFromMenu(_:)), keyEquivalent: "")
            item.target = self
            item.representedObject = m
            item.isEnabled = connected
            item.state = (connected && mode == m) ? .on : .off
        }

        menu.addItem(.separator())
        let quit = menu.addItem(withTitle: Loc.exit, action: #selector(quit), keyEquivalent: "q")
        quit.target = self
    }

    private func poll() {
        if disposed || polling { return }
        polling = true
        let seqAtStart = switchSeq
        DispatchQueue.global(qos: .utility).async { [weak self] in
            guard let self = self else { return }
            var st: MihomoStatus?
            var err: Error?
            do { st = try self.client.getStatus() } catch { err = error }
            DispatchQueue.main.async {
                self.polling = false
                if self.switching > 0 || seqAtStart != self.switchSeq { return }
                self.updateState(st, err)
            }
        }
    }

    private func updateState(_ st: MihomoStatus?, _ err: Error?) {
        if disposed { return }
        guard let btn = statusItem.button else { return }
        if err != nil || st == nil {
            connected = false
            btn.image = icons["offline"]
            btn.toolTip = TrayTip.text(connected: false, mode: nil, tunEnabled: false, logLevel: nil)
        } else if let st = st {
            connected = true
            mode = st.mode
            let key = Self.modes.contains(st.mode) ? st.mode : "rule"
            btn.image = icons[key]
            btn.toolTip = TrayTip.text(connected: true, mode: st.mode, tunEnabled: st.tunEnabled, logLevel: st.logLevel)
        }
        rebuildMenu()
    }

    @objc private func switchModeFromMenu(_ sender: NSMenuItem) {
        guard let m = sender.representedObject as? String else { return }
        switchMode(m)
    }

    private func switchMode(_ mode: String) {
        if disposed { return }
        switchSeq += 1
        let seq = switchSeq
        switching += 1
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            var err: Error?
            var now: MihomoStatus?
            do {
                try self.client.setMode(mode)
                if self.cfg.closeConnections {
                    try? self.client.closeAllConnections()
                }
                now = try self.client.getStatus()
            } catch {
                err = error
            }
            DispatchQueue.main.async {
                self.switching = max(0, self.switching - 1)
                if self.disposed || seq != self.switchSeq { return }
                if let err = err {
                    self.updateState(nil, err)
                    self.warn(Loc.switchFailed, err.localizedDescription + "\n" + Loc.controllerLabel + self.cfg.controller)
                } else {
                    self.updateState(now, nil)
                }
            }
        }
    }

    @objc func openPanel() {
        guard let url = URL(string: cfg.panelUrl) else {
            warn(Loc.cantOpenPanel, cfg.panelUrl)
            return
        }
        if !NSWorkspace.shared.open(url) {
            warn(Loc.cantOpenPanel, cfg.panelUrl)
        }
    }

    @objc private func launchSwitchProgram() {
        if !cfg.hasSwitchProgram {
            warn(Loc.cantOpenApp, Loc.switchNotSet)
            return
        }
        guard let path = AppConfig.resolveProgramPath(cfg.switchProgram, baseDir: AppConfig.appDir),
              FileManager.default.fileExists(atPath: path) else {
            warn(Loc.cantOpenApp, Loc.fileNotFound(AppConfig.resolveProgramPath(cfg.switchProgram, baseDir: AppConfig.appDir) ?? cfg.switchProgram))
            return
        }
        let url = URL(fileURLWithPath: path)
        if path.hasSuffix(".app") || FileManager.default.fileExists(atPath: (path as NSString).appendingPathComponent("Contents/MacOS")) {
            let config = NSWorkspace.OpenConfiguration()
            if !cfg.effectiveSwitchArgs.isEmpty {
                config.arguments = cfg.effectiveSwitchArgs.split(whereSeparator: { $0.isWhitespace }).map(String.init)
            }
            NSWorkspace.shared.openApplication(at: url, configuration: config) { _, error in
                if let error = error {
                    DispatchQueue.main.async {
                        self.warn(Loc.cantOpenApp, error.localizedDescription + "\n" + path)
                    }
                }
            }
        } else {
            do {
                try NSWorkspace.shared.open([url], withApplicationAt: URL(fileURLWithPath: "/usr/bin/open"),
                                            configuration: NSWorkspace.OpenConfiguration())
            } catch {
                // Fallback: open file URL directly
                if !NSWorkspace.shared.open(url) {
                    warn(Loc.cantOpenApp, error.localizedDescription + "\n" + path)
                }
            }
        }
    }

    private func warn(_ title: String, _ text: String) {
        if disposed { return }
        var t = text
        if t.count > 250 { t = String(t.prefix(247)) + "..." }
        let alert = NSAlert()
        alert.messageText = title
        alert.informativeText = t
        alert.alertStyle = .warning
        alert.addButton(withTitle: "OK")
        NSApp.activate(ignoringOtherApps: true)
        alert.runModal()
    }

    @objc func quit() {
        if disposed { return }
        disposed = true
        timer?.invalidate()
        timer = nil
        if let item = statusItem {
            NSStatusBar.system.removeStatusItem(item)
        }
        statusItem = nil
        NSApp.terminate(nil)
    }
}
