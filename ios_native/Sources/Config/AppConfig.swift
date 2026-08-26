import Foundation

enum AppConfig {
    static var apiBaseURL: URL {
        let rawValue = (Bundle.main.object(forInfoDictionaryKey: "GalaApiBase") as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        #if DEBUG
        let fallback = "https://galacredit.ebamotor.com/api"
        #else
        let fallback = "https://galacredit.ebamotor.com/api"
        #endif
        return URL(string: rawValue?.isEmpty == false ? rawValue! : fallback)!
    }

    static var webBaseURL: URL {
        let apiURL = apiBaseURL.absoluteString
        if apiURL.hasSuffix("/api") {
            return URL(string: String(apiURL.dropLast(4))) ?? apiBaseURL
        }
        return apiBaseURL
    }

    static var flavorName: String {
        let rawValue = (Bundle.main.object(forInfoDictionaryKey: "GalaAppFlavor") as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        return rawValue?.isEmpty == false ? rawValue! : "prod"
    }
}
