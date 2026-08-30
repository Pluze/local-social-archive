import Foundation
import Security

let credentialServices = [
    "org.local-social-archive.database-key",
    "org.local-social-archive.media-key",
    "org.local-social-archive.admin-authorization"
]

func keychainItemCount(service: String) -> Int {
    let query: [CFString: Any] = [
        kSecClass: kSecClassGenericPassword,
        kSecAttrService: service,
        kSecMatchLimit: kSecMatchLimitAll,
        kSecReturnAttributes: true
    ]
    var result: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &result)
    guard status == errSecSuccess else { return 0 }
    if let items = result as? [[String: Any]] { return items.count }
    return result == nil ? 0 : 1
}

func credentialStatus() -> [String: Any] {
    let database = keychainItemCount(service: credentialServices[0])
    let media = keychainItemCount(service: credentialServices[1])
    let authorization = keychainItemCount(service: credentialServices[2])
    return [
        "ok": true,
        "databaseRecords": database,
        "mediaRecords": media,
        "authorizationRecords": authorization,
        "totalRecords": database + media + authorization
    ]
}

func clearCredentialService(_ service: String) throws {
    let query: [CFString: Any] = [kSecClass: kSecClassGenericPassword, kSecAttrService: service]
    let status = SecItemDelete(query as CFDictionary)
    if status != errSecSuccess && status != errSecItemNotFound {
        throw NSError(
            domain: NSOSStatusErrorDomain,
            code: Int(status),
            userInfo: [NSLocalizedDescriptionKey: "Keychain cleanup failed for one credential class."]
        )
    }
}
