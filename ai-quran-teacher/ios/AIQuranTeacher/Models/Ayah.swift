import Foundation

/// A single verse, with its mushaf text and translation.
struct Ayah: Identifiable, Codable, Hashable {
    let id: Int              // global ayah number (1...6236)
    let surahId: Int
    let numberInSurah: Int
    let text: String         // fully vocalized Arabic text
    let translation: String?
    let audioURL: URL?
    var isBookmarked: Bool = false

    enum CodingKeys: String, CodingKey {
        case id, surahId, numberInSurah, text, translation, audioURL
    }
}
