import Foundation

/// A Tajweed or recitation mistake reported by the backend engine
/// (or the on-device fallback in `TajweedEngine.swift`).
struct TajweedMistake: Identifiable, Codable, Hashable {
    enum MistakeType: String, Codable {
        case wordMismatch = "word_mismatch"
        case missingWord = "missing_word"
        case extraWord = "extra_word"
    }

    enum Severity: String, Codable {
        case minor, moderate, major
    }

    var id: UUID = UUID()
    let type: MistakeType
    let severity: Severity
    let wordIndex: Int
    let expectedWord: String
    let actualWord: String
    let suggestion: String

    enum CodingKeys: String, CodingKey {
        case type, severity, wordIndex, expectedWord, actualWord, suggestion
    }
}

/// A Tajweed rule occurrence within an ayah, used to color/annotate text.
struct TajweedRuleOccurrence: Codable, Hashable {
    let rule: String
    let position: Int
    let trigger: String
    let description: String
}

/// Response shape of `POST /tajweed/detect`.
struct TajweedDetectionResult: Codable {
    let ayahId: Int
    let accuracy: Double
    let mistakes: [TajweedMistake]
    let rulesToObserve: [TajweedRuleOccurrence]
}
