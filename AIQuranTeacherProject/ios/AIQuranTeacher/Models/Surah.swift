import Foundation

struct Surah: Identifiable, Codable {
    let id: Int
    let name: String
    let arabicName: String
    let ayahs: [Ayah]
    let translation: String?
}
