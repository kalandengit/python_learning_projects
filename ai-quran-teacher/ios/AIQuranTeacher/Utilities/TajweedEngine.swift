import Foundation

/// On-device fallback of the backend Tajweed engine, used when offline.
/// Mirrors `backend/src/tajweed/tajweed.rules.ts` — keep the two in sync.
enum TajweedEngine {
    private static let sukoon: Character = "ْ"
    private static let shadda: Character = "ّ"
    private static let noon: Character = "ن"
    private static let meem: Character = "م"
    private static let tanween: Set<Character> = ["ً", "ٌ", "ٍ"]

    private static let izharLetters: Set<Character> = ["ء", "أ", "إ", "ئ", "ؤ", "ه", "ع", "ح", "غ", "خ"]
    private static let idghamGhunnahLetters: Set<Character> = ["ي", "ن", "م", "و"]
    private static let idghamNoGhunnahLetters: Set<Character> = ["ل", "ر"]
    private static let qalqalahLetters: Set<Character> = ["ق", "ط", "ب", "ج", "د"]

    static func analyze(_ text: String) -> [TajweedRuleOccurrence] {
        var occurrences: [TajweedRuleOccurrence] = []
        let chars = Array(text)

        for (index, char) in chars.enumerated() {
            let cluster = diacriticCluster(in: chars, after: index)

            if (char == noon && cluster.contains(sukoon)) || tanween.contains(char) {
                if let next = nextBaseLetter(in: chars, from: index + 1) {
                    let rule = classifyNoonSakinah(before: next)
                    occurrences.append(occurrence(rule: rule, position: index, trigger: String(char)))
                }
                continue
            }
            if qalqalahLetters.contains(char), cluster.contains(sukoon) {
                occurrences.append(occurrence(rule: "qalqalah", position: index, trigger: String(char)))
                continue
            }
            if (char == noon || char == meem), cluster.contains(shadda) {
                occurrences.append(occurrence(rule: "ghunnah", position: index, trigger: String(char)))
            }
        }
        return occurrences
    }

    /// Word-level comparison of a transcript against the expected ayah text.
    static func compare(recited: String, expected: String) -> [TajweedMistake] {
        let expectedWords = normalize(expected).split(separator: " ").map(String.init)
        let recitedWords = normalize(recited).split(separator: " ").map(String.init)
        var mistakes: [TajweedMistake] = []

        // Simple positional comparison; the backend performs full alignment.
        for (index, expectedWord) in expectedWords.enumerated() {
            guard index < recitedWords.count else {
                mistakes.append(TajweedMistake(
                    type: .missingWord, severity: .major, wordIndex: index,
                    expectedWord: expectedWord, actualWord: "",
                    suggestion: "The word \"\(expectedWord)\" was skipped."
                ))
                continue
            }
            if recitedWords[index] != expectedWord {
                mistakes.append(TajweedMistake(
                    type: .wordMismatch, severity: .major, wordIndex: index,
                    expectedWord: expectedWord, actualWord: recitedWords[index],
                    suggestion: "Expected \"\(expectedWord)\" but heard \"\(recitedWords[index])\"."
                ))
            }
        }
        return mistakes
    }

    static func normalize(_ text: String) -> String {
        let diacritics = CharacterSet(charactersIn: "ًٌٍَُِّْٰ")
        let stripped = text.unicodeScalars.filter { !diacritics.contains($0) }
        return String(String.UnicodeScalarView(stripped))
            .replacingOccurrences(of: "أ", with: "ا")
            .replacingOccurrences(of: "إ", with: "ا")
            .replacingOccurrences(of: "آ", with: "ا")
            .replacingOccurrences(of: "ٱ", with: "ا")
            .replacingOccurrences(of: "ى", with: "ي")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    // MARK: - Helpers

    private static let ruleDescriptions: [String: String] = [
        "izhar": "Pronounce the noon clearly before throat letters.",
        "idgham_with_ghunnah": "Merge into the next letter with nasalization.",
        "idgham_without_ghunnah": "Merge into the next letter without nasalization.",
        "iqlab": "Convert the noon into a hidden meem before ب.",
        "ikhfa": "Hide the noon with light nasalization.",
        "qalqalah": "Give an echoing bounce to the saakin letter.",
        "ghunnah": "Hold the nasal sound for two counts.",
    ]

    private static func occurrence(rule: String, position: Int, trigger: String) -> TajweedRuleOccurrence {
        TajweedRuleOccurrence(
            rule: rule,
            position: position,
            trigger: trigger,
            description: ruleDescriptions[rule] ?? rule
        )
    }

    private static func classifyNoonSakinah(before letter: Character) -> String {
        if izharLetters.contains(letter) { return "izhar" }
        if idghamGhunnahLetters.contains(letter) { return "idgham_with_ghunnah" }
        if idghamNoGhunnahLetters.contains(letter) { return "idgham_without_ghunnah" }
        if letter == "ب" { return "iqlab" }
        return "ikhfa"
    }

    private static func isDiacritic(_ char: Character) -> Bool {
        ("ً"..."ْ").contains(char) || char == "ٰ"
    }

    private static func diacriticCluster(in chars: [Character], after index: Int) -> Set<Character> {
        var cluster: Set<Character> = []
        var i = index + 1
        while i < chars.count, isDiacritic(chars[i]) {
            cluster.insert(chars[i])
            i += 1
        }
        return cluster
    }

    private static func nextBaseLetter(in chars: [Character], from index: Int) -> Character? {
        var i = index
        while i < chars.count {
            let char = chars[i]
            if ("ء"..."ي").contains(char) { return char }
            i += 1
        }
        return nil
    }
}
