import AppKit
import Foundation
import Darwin

private let singleInstanceId = "com.mihomotray.MihomoTray"

final class AppDelegate: NSObject, NSApplicationDelegate {
    var tray: TrayController?
    private var lockFd: Int32 = -1

    func applicationDidFinishLaunching(_ notification: Notification) {
        Loc.apply("system")
        if !acquireSingleInstance() {
            let alert = NSAlert()
            alert.messageText = Loc.appTitle
            alert.informativeText = Loc.alreadyRunning
            alert.alertStyle = .informational
            alert.addButton(withTitle: "OK")
            alert.runModal()
            NSApp.terminate(nil)
            return
        }
        NSApp.setActivationPolicy(.accessory) // menubar-only, no dock icon
        let cfg = AppConfig.load()
        tray = TrayController(cfg: cfg)
    }

    func applicationWillTerminate(_ notification: Notification) {
        tray?.quit()
        releaseSingleInstance()
    }

    private func acquireSingleInstance() -> Bool {
        let path = NSTemporaryDirectory() + "MihomoTrayModeSwitcher.lock"
        let fd = open(path, O_CREAT | O_RDWR, 0o644)
        if fd < 0 { return true } // if lock file fails, still run
        if flock(fd, LOCK_EX | LOCK_NB) != 0 {
            close(fd)
            return false
        }
        lockFd = fd
        return true
    }

    private func releaseSingleInstance() {
        if lockFd >= 0 {
            flock(lockFd, LOCK_UN)
            close(lockFd)
            lockFd = -1
        }
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
