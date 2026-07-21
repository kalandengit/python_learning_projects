import Foundation

/// Fast, offline heuristics for immediate tajweed hints while the authoritative
/// AI analysis is in flight. Scaffold: extend with real rule detection.
enum TajweedEngine {
    static func detectLocalMistakes(text: String, ayah: Ayah) -> [TajweedMistake] {
        // TODO: implement lightweight local checks (e.g. missing words, obvious
        // elongation errors). Returning an empty set keeps the UI clean until
        // the backend responds.
        []
    }
}
