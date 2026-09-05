import Foundation
import UIKit
import CryptoKit

enum APIError: LocalizedError, Equatable {
    case invalidURL
    case invalidResponse
    case server(status: Int, message: String)
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "接口地址无效"
        case .invalidResponse:
            return "服务返回格式无效"
        case .server(_, let message):
            return message
        case .unauthorized:
            return "登录已失效，请重新登录"
        }
    }
}

final class APIClient: @unchecked Sendable {
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    /// 发送登录请求并返回 token 信息。
    ///
    /// :param username: 管理员账号
    /// :param password: 管理员密码
    /// :return: 登录响应 JSON
    func login(username: String, password: String) async throws -> JSONMap {
        let payload: JSONMap = [
            "username": .string(username),
            "password": .string(password),
            "client_type": .string("MOBILE")
        ]
        return try await request(path: "/admin/login", method: "POST", body: payload, token: nil)
    }

    /// 创建滑块验证码挑战。
    /// :param phone: 加纳手机号（含国家码）
    /// :param width: 客户端可用宽度
    /// :return: 验证码挑战信息
    func createSliderCaptcha(phone: String, width: Int) async throws -> JSONMap {
        try await post(path: "/auth/slider-captcha/create", body: ["phone": .string(phone), "width": .number(Double(width))], token: nil)
    }

    /// 校验滑块并取得一次性发送票据。
    /// :param phone: 加纳手机号
    /// :param captchaID: 挑战标识
    /// :param offsetX: 滑块横向偏移
    /// :param elapsedMs: 拖动耗时
    /// :return: captcha_ticket
    func verifySliderCaptcha(phone: String, captchaID: String, offsetX: Double, elapsedMs: Int) async throws -> JSONMap {
        try await post(path: "/auth/slider-captcha/verify", body: ["phone": .string(phone), "captcha_id": .string(captchaID), "offset_x": .number(offsetX), "elapsed_ms": .number(Double(elapsedMs))], token: nil)
    }

    /// 发送短信验证码。
    /// :param phone: 加纳手机号
    /// :param captchaTicket: 已通过滑块验证的票据
    /// :return: 发送结果
    func sendCode(phone: String, captchaTicket: String) async throws -> JSONMap {
        try await post(path: "/auth/send-code", body: ["phone": .string(phone), "captcha_ticket": .string(captchaTicket)], token: nil)
    }

    /// 使用短信验证码登录用户端。
    /// :param phone: 加纳手机号
    /// :param smsCode: 六位短信验证码
    /// :return: token 信息
    func smsLogin(phone: String, smsCode: String) async throws -> JSONMap {
        try await post(path: "/auth/sms-login", body: ["phone": .string(phone), "sms_code": .string(smsCode)], token: nil)
    }

    /// 发起 GET 请求。
    ///
    /// :param path: 接口路径
    /// :param query: 查询参数
    /// :param token: Bearer token
    /// :return: JSON 对象
    func get(path: String, query: [URLQueryItem] = [], token: String?) async throws -> JSONMap {
        try await request(path: path, method: "GET", query: query, body: nil, token: token)
    }

    /// 发起 GET 请求并解析数组响应。
    ///
    /// :param path: 接口路径
    /// :param query: 查询参数
    /// :param token: Bearer token
    /// :return: JSON 对象数组
    func getArray(path: String, query: [URLQueryItem] = [], token: String?) async throws -> [JSONMap] {
        try await requestArray(path: path, method: "GET", query: query, token: token)
    }

    /// 发起 POST 请求。
    ///
    /// :param path: 接口路径
    /// :param body: 请求体
    /// :param token: Bearer token
    /// :return: JSON 对象
    func post(path: String, body: JSONMap, token: String?) async throws -> JSONMap {
        try await request(path: path, method: "POST", query: [], body: body, token: token)
    }

    /// 提交 iOS 设备基础风险摘要；不包含短信、通讯录或完整应用列表。
    ///
    /// :param phone: 当前登录用户的国际手机号
    /// :param token: 当前用户访问令牌
    /// :param devicePayload: 已最小化的设备载荷
    /// :return: 服务端风险任务摘要
    func submitDeviceRiskSignals(phone: String, token: String, devicePayload: JSONMap) async throws -> JSONMap {
        let body: JSONMap = [
            "phone": .string(phone),
            "accepted_user_agreement": .bool(true),
            "accepted_personal_authorization": .bool(true),
            "accepted_sensitive_collection": .bool(true),
            "device_payload": .object(devicePayload)
        ]
        return try await post(path: "/user/risk-signals", body: body, token: token)
    }

    /// 发起 PATCH 请求。
    ///
    /// :param path: 接口路径
    /// :param body: 请求体
    /// :param token: Bearer token
    /// :return: JSON 对象
    func patch(path: String, body: JSONMap, token: String?) async throws -> JSONMap {
        try await request(path: path, method: "PATCH", query: [], body: body, token: token)
    }

    /// 统一发送 HTTP 请求。
    ///
    /// :param path: 接口路径
    /// :param method: HTTP 方法
    /// :param query: 查询参数
    /// :param body: JSON 请求体
    /// :param token: Bearer token
    /// :return: JSON 对象
    private func request(
        path: String,
        method: String,
        query: [URLQueryItem] = [],
        body: JSONMap?,
        token: String?
    ) async throws -> JSONMap {
        guard var components = URLComponents(url: AppConfig.apiBaseURL, resolvingAgainstBaseURL: false) else {
            throw APIError.invalidURL
        }
        components.path = AppConfig.apiBaseURL.path + path
        components.queryItems = query.isEmpty ? nil : query
        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 20
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("galacredit-ios", forHTTPHeaderField: "client-id")
        if let token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(body)
        }

        let (data, response) = try await send(request, retries: method == "GET" || method == "HEAD" ? 2 : 0)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        let payload = try decodeJSONObject(from: data)
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        if !(200...299).contains(httpResponse.statusCode) {
            let message = payload.string("msg", fallback: payload.string("detail", fallback: "请求失败：\(httpResponse.statusCode)"))
            throw APIError.server(status: httpResponse.statusCode, message: message)
        }
        if let code = payload["code"]?.intValue, code != 0 && code != 200 {
            let message = payload.string("msg", fallback: payload.string("detail", fallback: "请求未成功"))
            throw APIError.server(status: httpResponse.statusCode, message: message)
        }
        return payload
    }

    /// 统一发送并解析数组响应的 HTTP 请求。
    ///
    /// :param path: 接口路径
    /// :param method: HTTP 方法
    /// :param query: 查询参数
    /// :param token: Bearer token
    /// :return: JSON 对象数组
    private func requestArray(
        path: String,
        method: String,
        query: [URLQueryItem],
        token: String?
    ) async throws -> [JSONMap] {
        guard var components = URLComponents(url: AppConfig.apiBaseURL, resolvingAgainstBaseURL: false) else {
            throw APIError.invalidURL
        }
        components.path = AppConfig.apiBaseURL.path + path
        components.queryItems = query.isEmpty ? nil : query
        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 20
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("galacredit-ios", forHTTPHeaderField: "client-id")
        if let token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await send(request, retries: method == "GET" || method == "HEAD" ? 2 : 0)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }
        let value = try JSONDecoder().decode(JSONValue.self, from: data)
        if !(200...299).contains(httpResponse.statusCode) {
            let payload = value.objectValue ?? [:]
            let message = payload.string("msg", fallback: payload.string("detail", fallback: "请求失败：\(httpResponse.statusCode)"))
            throw APIError.server(status: httpResponse.statusCode, message: message)
        }
        if let payload = value.objectValue,
           let code = payload["code"]?.intValue,
           code != 0 && code != 200 {
            let message = payload.string("msg", fallback: payload.string("detail", fallback: "请求未成功"))
            throw APIError.server(status: httpResponse.statusCode, message: message)
        }
        guard let array = value.arrayValue else {
            throw APIError.invalidResponse
        }
        return array.compactMap(\.objectValue)
    }

    /// 解析 JSON 对象响应。
    ///
    /// :param data: 原始响应数据
    /// :return: JSON 对象
    private func decodeJSONObject(from data: Data) throws -> JSONMap {
        if data.isEmpty {
            return [:]
        }
        let value = try JSONDecoder().decode(JSONValue.self, from: data)
        guard let object = value.objectValue else {
            throw APIError.invalidResponse
        }
        return object
    }

    /// 对只读请求执行有限指数退避，避免弱网下重复提交 POST 造成业务副作用。
    ///
    /// :param request: 待发送请求
    /// :param retries: 允许的重试次数
    /// :return: 响应数据及 HTTP 响应
    private func send(_ request: URLRequest, retries: Int) async throws -> (Data, URLResponse) {
        var attempt = 0
        while true {
            do {
                let result = try await session.data(for: request)
                if let response = result.1 as? HTTPURLResponse,
                   response.statusCode >= 500,
                   attempt < retries {
                    attempt += 1
                    try await Task.sleep(nanoseconds: UInt64(250_000_000 * (1 << (attempt - 1))))
                    continue
                }
                return result
            } catch {
                guard attempt < retries else { throw error }
                attempt += 1
                try await Task.sleep(nanoseconds: UInt64(250_000_000 * (1 << (attempt - 1))))
            }
        }
    }
}

/// 为共用 UniApp 页面提供最小化的 iOS 运行环境摘要。
///
/// 原始 identifierForVendor 只在本地参与哈希，不进入网络载荷。
enum NativeEnvironment {
    /// 构造可注入 WebView 和提交风控接口的环境摘要。
    ///
    /// :return: 可安全传输的环境信息
    static func info() -> [String: Any] {
        let device = UIDevice.current
        let screen = UIScreen.main.bounds
        let vendorID = device.identifierForVendor?.uuidString ?? ""
        let fingerprint = vendorID.isEmpty ? "" : sha256("com.galacredit.ios:\(vendorID)")
        return [
            "platform": "ios",
            "app_channel": "appstore",
            "source": "NATIVE_IOS",
            "native_bridge": "GalaCreditIOS",
            "model": device.model,
            "system": "\(device.systemName) \(device.systemVersion)",
            "device_type": "phone",
            "brand": "Apple",
            "language": Locale.preferredLanguages.first ?? Locale.current.identifier,
            "screen_width": Int(screen.width * UIScreen.main.scale),
            "screen_height": Int(screen.height * UIScreen.main.scale),
            "app_version": (Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String) ?? "",
            "device_fingerprint": fingerprint
        ]
    }

    /// 将环境摘要映射成服务端风险接口的最小载荷。
    ///
    /// :return: 不含短信和完整应用列表的设备风险载荷
    static func riskPayload() -> JSONMap {
        let environment = info()
        let profile: JSONMap = [
            "model": .string(environment["model"] as? String ?? ""),
            "os": .string(environment["system"] as? String ?? ""),
            "device_type": .string(environment["device_type"] as? String ?? ""),
            "brand": .string(environment["brand"] as? String ?? ""),
            "language": .string(environment["language"] as? String ?? ""),
            "screen_width": .number(Double(environment["screen_width"] as? Int ?? 0)),
            "screen_height": .number(Double(environment["screen_height"] as? Int ?? 0))
        ]
        return [
            "consent_sms": .bool(false),
            "consent_app_list": .bool(false),
            "consent_device_fingerprint": .bool(true),
            "sms_messages": .array([]),
            "installed_apps": .array([]),
            "device_profile": .object(profile),
            "native_bridge": .string(environment["native_bridge"] as? String ?? "GalaCreditIOS"),
            "source": .string(environment["source"] as? String ?? "NATIVE_IOS"),
            "app_channel": .string(environment["app_channel"] as? String ?? "appstore"),
            "app_version": .string(environment["app_version"] as? String ?? ""),
            "platform": .string("ios"),
            "timezone": .string(TimeZone.current.identifier),
            "language": .string(environment["language"] as? String ?? ""),
            "screen_width": .number(Double(environment["screen_width"] as? Int ?? 0)),
            "screen_height": .number(Double(environment["screen_height"] as? Int ?? 0)),
            "device_fingerprint": .string(environment["device_fingerprint"] as? String ?? ""),
            "consent_version": .string("2026-09"),
            "risk_flags": .array([])
        ]
    }

    /// 生成不可逆设备摘要。
    ///
    /// :param value: 命名空间和设备标识
    /// :return: 小写十六进制 SHA-256
    private static func sha256(_ value: String) -> String {
        SHA256.hash(data: Data(value.utf8)).map { String(format: "%02x", $0) }.joined()
    }
}
