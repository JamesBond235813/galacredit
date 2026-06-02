import Foundation

enum AppConfig {
    static var apiBaseURL: URL {
        let rawValue = (Bundle.main.object(forInfoDictionaryKey: "XHBApiBase") as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        #if DEBUG
        let fallback = "http://127.0.0.1:8001/api"
        #else
        let fallback = "https://xhbadmin.juxin.pro/api"
        #endif
        return URL(string: rawValue?.isEmpty == false ? rawValue! : fallback)!
    }

    static var flavorName: String {
        let rawValue = (Bundle.main.object(forInfoDictionaryKey: "XHBAppFlavor") as? String)?.trimmingCharacters(in: .whitespacesAndNewlines)
        return rawValue?.isEmpty == false ? rawValue! : "local"
    }
}
