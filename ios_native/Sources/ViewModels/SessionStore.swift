import Foundation
import SwiftUI

@MainActor
final class SessionStore: ObservableObject {
    @Published var token: String
    @Published var admin: JSONMap?
    @Published var riskTask: JSONMap?
    @Published var errorMessage = ""
    @Published var isLoading = false
    @Published var isRestoring = true

    let apiClient: APIClient
    private let tokenKey = "galacredit_ios_token"
    private let phoneKey = "galacredit_ios_phone"
    private let riskTaskKey = "galacredit_ios_risk_task"
    private var riskSubmissionTask: Task<Void, Never>?

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
        self.token = KeychainStore.read(key: tokenKey) ?? ""
        self.phone = KeychainStore.read(key: phoneKey) ?? ""
        if let value = KeychainStore.read(key: riskTaskKey),
           let data = value.data(using: .utf8),
           let decoded = try? JSONDecoder().decode(JSONValue.self, from: data) {
            self.riskTask = decoded.objectValue
        } else {
            self.riskTask = nil
        }
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
            KeychainStore.save(accessToken, key: tokenKey)
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
        riskSubmissionTask?.cancel()
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await apiClient.smsLogin(phone: "+233\(phone)", smsCode: smsCode)
            let accessToken = response.string("access_token")
            guard !accessToken.isEmpty else { throw APIError.invalidResponse }
            token = accessToken
            self.phone = phone
            KeychainStore.save(accessToken, key: tokenKey)
            KeychainStore.save(phone, key: phoneKey)
            admin = nil
            errorMessage = ""
            // iOS 不读取短信，但登录后仍提交一次最小设备摘要，使三端风控输入保持一致。
            // 网络失败不阻断登录，用户可在安全检查页面再次提交。
            let riskPhone = "+233\(phone)"
            let riskClient = apiClient
            let riskToken = accessToken
            riskSubmissionTask = Task { [weak self] in
                guard let self else { return }
                if let result = try? await riskClient.submitDeviceRiskSignals(phone: riskPhone, token: riskToken, devicePayload: NativeEnvironment.riskPayload()),
                   result["task_number"]?.stringValue?.isEmpty == false,
                   !Task.isCancelled,
                   self.token == riskToken {
                    self.riskTask = result
                    if let data = try? JSONEncoder().encode(JSONValue.object(result)),
                       let value = String(data: data, encoding: .utf8) {
                        KeychainStore.save(value, key: self.riskTaskKey)
                    }
                }
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 使用本地 token 恢复登录态。
    ///
    /// :param none: 无
    /// :return: 无
    func restoreSession() async {
        guard !token.isEmpty else {
            isRestoring = false
            return
        }
        isLoading = true
        defer {
            isLoading = false
            isRestoring = false
        }
        do {
            _ = try await apiClient.get(path: "/user/info", token: token)
            errorMessage = ""
        } catch {
            // 只有服务端明确返回 401 才清除 Keychain 会话；弱网或服务暂时不可用时保留会话，
            // 让 WebView 自己展示可重试的离线状态，避免用户被无故踢回登录页。
            if case APIError.unauthorized = error {
                logout()
            }
            errorMessage = error.localizedDescription
        }
    }

    /// 退出当前账号并清空本地凭证。
    ///
    /// :param none: 无
    /// :return: 无
    func logout() {
        riskSubmissionTask?.cancel()
        riskSubmissionTask = nil
        token = ""
        admin = nil
        phone = ""
        riskTask = nil
        KeychainStore.remove(key: tokenKey)
        KeychainStore.remove(key: phoneKey)
        KeychainStore.remove(key: riskTaskKey)
    }
}
