import Foundation

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
        if let token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(body)
        }

        let (data, response) = try await session.data(for: request)
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
        if let token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await session.data(for: request)
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
}
