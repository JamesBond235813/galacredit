import Foundation
import SwiftUI

@MainActor
final class SessionStore: ObservableObject {
    @Published var token: String
    @Published var admin: JSONMap?
    @Published var errorMessage = ""
    @Published var isLoading = false

    let apiClient: APIClient
    private let tokenKey = "xhb_ios_native_token"

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
        self.token = UserDefaults.standard.string(forKey: tokenKey) ?? ""
    }

    var isLoggedIn: Bool {
        !token.isEmpty && admin != nil
    }

    /// 使用管理员账号登录。
    ///
    /// :param username: 管理员账号
    /// :param password: 管理员密码
    /// :return: 无
    func login(username: String, password: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await apiClient.login(username: username, password: password)
            let accessToken = response.string("access_token")
            token = accessToken
            UserDefaults.standard.set(accessToken, forKey: tokenKey)
            admin = try await apiClient.get(path: "/admin/me", token: accessToken)
            errorMessage = ""
        } catch {
            logout()
            errorMessage = error.localizedDescription
        }
    }

    /// 使用本地 token 恢复登录态。
    ///
    /// :param none: 无
    /// :return: 无
    func restoreSession() async {
        guard !token.isEmpty else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            admin = try await apiClient.get(path: "/admin/me", token: token)
            errorMessage = ""
        } catch {
            logout()
            errorMessage = error.localizedDescription
        }
    }

    /// 退出当前账号并清空本地凭证。
    ///
    /// :param none: 无
    /// :return: 无
    func logout() {
        token = ""
        admin = nil
        UserDefaults.standard.removeObject(forKey: tokenKey)
    }
}
