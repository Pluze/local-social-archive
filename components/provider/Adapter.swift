import AppKit
import WebKit

final class StubAdapter: NSObject, ArchiveBridge {
    weak var webView: WKWebView?

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let body = message.body as? [String: Any], let id = body["id"] as? String else { return }
        let action = body["action"] as? String ?? ""
        let response: [String: Any]
        if action == "bootstrap" {
            response = [
                "ok": true, "archiveMode": true,
                "chat": ["ready": false, "conversationCount": 0, "messageCount": 0, "plainTextCount": 0, "resourceCount": 0, "availableResourceCount": 0],
                "moments": ["ready": false, "postCount": 0],
                "conversations": [], "provider": "stub",
                "sourceProfile": [
                    "sourceName": "Source",
                    "sourceApplicationName": "source application",
                    "conversationName": "Conversation",
                    "conversationPlural": "Conversations",
                    "timelineName": "Timeline",
                    "ownTimelineName": "My Timeline",
                    "timelineMediaName": "Timeline media",
                    "timelineNavigationHint": "Open your own timeline in the source application, view the required items, then return and rescan."
                ],
            ]
        } else if action == "credentialStatus" {
            response = credentialStatus()
        } else if action == "sourceStatus" {
            let credentials = credentialStatus()
            let unavailable = ["state": "not_started", "message": "Not available in this build · install a compatible authorized source component."]
            response = [
                "ok": true,
                "checkedAt": ISO8601DateFormatter().string(from: Date()),
                "credentials": credentials,
                "steps": ["capture": unavailable, "media": unavailable, "chats": unavailable, "moments": unavailable],
                "tasks": [:]
            ]
        } else if action == "resetCredentials" {
            do {
                for service in credentialServices { try clearCredentialService(service) }
                let root = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!.appendingPathComponent("Local Social Archive")
                try? FileManager.default.removeItem(at: root.appendingPathComponent("Shadow"))
                try? FileManager.default.removeItem(at: root.appendingPathComponent("State/chat-db"))
                try? FileManager.default.removeItem(at: root.appendingPathComponent("State/sns.sqlite"))
                response = ["ok": true, "message": "Credentials and decrypted source snapshots were cleared. Existing archives, backups, and exports were preserved."]
            } catch { response = ["ok": false, "error": error.localizedDescription] }
        } else if action == "openPrivacy" {
            if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles") { NSWorkspace.shared.open(url) }
            response = ["ok": true]
        } else if action == "openBackup" {
            let panel = NSOpenPanel()
            panel.canChooseFiles = true; panel.canChooseDirectories = true; panel.allowsMultipleSelection = false
            panel.prompt = "Open Archive"
            if panel.runModal() == .OK, let selected = panel.url {
                let index = selected.hasDirectoryPath ? selected.appendingPathComponent("index.html") : selected
                if index.lastPathComponent == "index.html", FileManager.default.fileExists(atPath: index.path) {
                    webView?.loadFileURL(index, allowingReadAccessTo: index.deletingLastPathComponent())
                    response = ["ok": true]
                } else {
                    response = ["ok": false, "error": "Choose an exported archive's index.html file or its containing folder."]
                }
            } else {
                response = ["ok": false, "cancelled": true]
            }
        } else {
            response = ["ok": false, "error": "This build has no acquisition component. Standard archive creation, validation, and offline viewing remain available."]
        }
        guard let data = try? JSONSerialization.data(withJSONObject: response) else { return }
        let encoded = data.base64EncodedString()
        DispatchQueue.main.async { [weak self] in
            self?.webView?.evaluateJavaScript("window.__bridgeResolveBase64(\(String(reflecting: id)),\(String(reflecting: encoded)))")
        }
    }
}

func makeArchiveBridge() -> ArchiveBridge { StubAdapter() }
