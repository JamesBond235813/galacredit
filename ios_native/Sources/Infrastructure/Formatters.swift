import Foundation

enum AppFormatter {
    private static let currencyFormatter: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.locale = Locale(identifier: "en_GH")
        formatter.currencyCode = "GHS"
        formatter.currencySymbol = "GHS "
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        return formatter
    }()

    private static let numberFormatter: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.minimumFractionDigits = 0
        formatter.maximumFractionDigits = 2
        return formatter
    }()

    static func currency(_ value: Double) -> String {
        currencyFormatter.string(from: NSNumber(value: value)) ?? "GHS 0.00"
    }

    static func number(_ value: Double) -> String {
        numberFormatter.string(from: NSNumber(value: value)) ?? "0"
    }

    static func dateTime(_ rawValue: String) -> String {
        guard !rawValue.isEmpty else { return "--" }
        let normalized = rawValue.replacingOccurrences(of: "T", with: " ")
        return normalized.count > 19 ? String(normalized.prefix(19)) : normalized
    }

    static func simpleDate(_ rawValue: String) -> String {
        let text = dateTime(rawValue)
        return text == "--" ? text : String(text.prefix(10))
    }
}
