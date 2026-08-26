import Foundation
import SwiftUI

@MainActor
final class SessionStore: ObservableObject {
    @Published var token: String
    @Published var admin: JSONMap?
    @Published var errorMessage = ""
    @Published var isLoading = false

    let apiClient: APIClient
    private let tokenKey = "galacredit_ios_token"
    private let phoneKey = "galacredit_ios_phone"

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
        self.token = UserDefaults.standard.string(forKey: tokenKey) ?? ""
        self.phone = UserDefaults.standard.string(forKey: phoneKey) ?? ""
    }

    var isLoggedIn: Bool {
        !token.isEmpty
    }

    @Published var phone: String

    /// 请求滑块验证码挑战。
    /// :param phone: 加纳本地九位手机号
    /// :return: 挑战信息
    func createCaptcha(phone: String) async throws -> JSONMap {
        try await apiClient.createSliderCaptcha(phone: "+233\(phone)", width: 320)
    }

    /// 校验滑块并发送短信验证码。
    /// :param phone: 加纳本地九位手机号
    /// :param captchaID: 挑战标识
    /// :param offsetX: 滑块偏移
    /// :param elapsedMs: 拖动时长
    /// :return: 发送结果
    func verifyAndSendCode(phone: String, captchaID: String, offsetX: Double, elapsedMs: Int) async throws -> JSONMap {
        let ticket = try await apiClient.verifySliderCaptcha(phone: "+233\(phone)", captchaID: captchaID, offsetX: offsetX, elapsedMs: elapsedMs)
        return try await apiClient.sendCode(phone: "+233\(phone)", captchaTicket: ticket.string("captcha_ticket"))
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

    /// 使用短信验证码登录用户端。
    /// :param phone: 加纳本地九位手机号
    /// :param smsCode: 六位验证码
    /// :return: 无
    func login(phone: String, smsCode: String) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await apiClient.smsLogin(phone: "+233\(phone)", smsCode: smsCode)
            let accessToken = response.string("access_token")
            guard !accessToken.isEmpty else { throw APIError.invalidResponse }
            token = accessToken
            self.phone = phone
            UserDefaults.standard.set(accessToken, forKey: tokenKey)
            UserDefaults.standard.set(phone, forKey: phoneKey)
            admin = nil
            errorMessage = ""
        } catch {
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
        phone = ""
        UserDefaults.standard.removeObject(forKey: tokenKey)
        UserDefaults.standard.removeObject(forKey: phoneKey)
    }
}
