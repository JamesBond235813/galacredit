import Foundation

enum JSONValue: Codable, Hashable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object([String: JSONValue])
    case array([JSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String: JSONValue].self) {
            self = .object(value)
        } else if let value = try? container.decode([JSONValue].self) {
            self = .array(value)
        } else {
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Unsupported JSON value")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value):
            try container.encode(value)
        case .number(let value):
            try container.encode(value)
        case .bool(let value):
            try container.encode(value)
        case .object(let value):
            try container.encode(value)
        case .array(let value):
            try container.encode(value)
        case .null:
            try container.encodeNil()
        }
    }
}

typealias JSONMap = [String: JSONValue]

extension JSONValue {
    var stringValue: String? {
        switch self {
        case .string(let value):
            return value
        case .number(let value):
            let integer = floor(value)
            return integer == value ? String(Int(value)) : String(value)
        case .bool(let value):
            return value ? "true" : "false"
        default:
            return nil
        }
    }

    var doubleValue: Double? {
        switch self {
        case .number(let value):
            return value
        case .string(let value):
            return Double(value)
        case .bool(let value):
            return value ? 1 : 0
        default:
            return nil
        }
    }

    var intValue: Int? {
        guard let doubleValue else { return nil }
        return Int(doubleValue)
    }

    var boolValue: Bool? {
        switch self {
        case .bool(let value):
            return value
        case .number(let value):
            return value != 0
        case .string(let value):
            return ["1", "true", "yes"].contains(value.lowercased())
        default:
            return nil
        }
    }

    var objectValue: JSONMap? {
        guard case .object(let value) = self else { return nil }
        return value
    }

    var arrayValue: [JSONValue]? {
        guard case .array(let value) = self else { return nil }
        return value
    }
}

extension Dictionary where Key == String, Value == JSONValue {
    func string(_ key: String, fallback: String = "") -> String {
        self[key]?.stringValue ?? fallback
    }

    func double(_ key: String, fallback: Double = 0) -> Double {
        self[key]?.doubleValue ?? fallback
    }

    func int(_ key: String, fallback: Int = 0) -> Int {
        self[key]?.intValue ?? fallback
    }

    func bool(_ key: String, fallback: Bool = false) -> Bool {
        self[key]?.boolValue ?? fallback
    }

    func object(_ key: String) -> JSONMap? {
        self[key]?.objectValue
    }

    func array(_ key: String) -> [JSONValue] {
        self[key]?.arrayValue ?? []
    }
}
