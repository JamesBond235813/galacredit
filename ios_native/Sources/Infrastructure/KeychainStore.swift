import Foundation
import Security

/// 使用 iOS Keychain 保存用户会话，避免将长期令牌放入 UserDefaults。
enum KeychainStore {
    /**
     * 保存字符串。
     *
     * :param value: 要保存的字符串
     * :param key: Keychain 键
     * :return: 无
     */
    static func save(_ value: String, key: String) {
        let data = Data(value.utf8)
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrAccount as String: key]
        SecItemDelete(query as CFDictionary)
        var insert = query
        insert[kSecValueData as String] = data
        insert[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        SecItemAdd(insert as CFDictionary, nil)
    }

    /**
     * 读取字符串。
     *
     * :param key: Keychain 键
     * :return: 保存的字符串；不存在时返回 nil
     */
    static func read(key: String) -> String? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrAccount as String: key, kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    /**
     * 删除字符串。
     *
     * :param key: Keychain 键
     * :return: 无
     */
    static func remove(key: String) {
        SecItemDelete([kSecClass as String: kSecClassGenericPassword, kSecAttrAccount as String: key] as CFDictionary)
    }
}
