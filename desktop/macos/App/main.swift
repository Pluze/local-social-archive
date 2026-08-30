import AppKit
import WebKit

protocol ArchiveBridge: AnyObject, WKScriptMessageHandler {
    var webView: WKWebView? { get set }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var bridge: ArchiveBridge!

    func applicationDidFinishLaunching(_ notification: Notification) {
        let config = WKWebViewConfiguration()
        let controller = WKUserContentController()
        bridge = makeArchiveBridge()
        controller.add(bridge, name: "bridge")
        config.userContentController = controller
        config.websiteDataStore = .nonPersistent()
        let web = WKWebView(frame: .zero, configuration: config)
        bridge.webView = web
        web.setValue(false, forKey: "drawsBackground")

        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1280, height: 820),
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.title = Bundle.main.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String ?? "Local Archive Assistant"
        window.titlebarAppearsTransparent = true
        window.titleVisibility = .hidden
        window.minSize = NSSize(width: 900, height: 620)
        window.isMovableByWindowBackground = true
        window.isRestorable = false

        let root = NSView()
        let dragRegion = WindowDragRegion()
        web.translatesAutoresizingMaskIntoConstraints = false
        dragRegion.translatesAutoresizingMaskIntoConstraints = false
        root.addSubview(web)
        root.addSubview(dragRegion)
        NSLayoutConstraint.activate([
            web.leadingAnchor.constraint(equalTo: root.leadingAnchor), web.trailingAnchor.constraint(equalTo: root.trailingAnchor),
            web.topAnchor.constraint(equalTo: root.topAnchor), web.bottomAnchor.constraint(equalTo: root.bottomAnchor),
            dragRegion.leadingAnchor.constraint(equalTo: root.leadingAnchor, constant: 76), dragRegion.trailingAnchor.constraint(equalTo: root.trailingAnchor),
            dragRegion.topAnchor.constraint(equalTo: root.topAnchor), dragRegion.heightAnchor.constraint(equalToConstant: 36),
        ])
        window.contentView = root
        window.center()
        window.makeKeyAndOrderFront(nil)
        if let url = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "Web") {
            web.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

final class WindowDragRegion: NSView {
    override var mouseDownCanMoveWindow: Bool { true }

    override func mouseDown(with event: NSEvent) {
        window?.performDrag(with: event)
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
