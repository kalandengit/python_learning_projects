import Foundation

/// A chapter of the Quran.
struct Surah: Identifiable, Codable, Hashable {
    let id: Int                 // 1...114
    let name: String            // Arabic name, e.g. "الفاتحة"
    let englishName: String     // e.g. "Al-Fatihah"
    let englishMeaning: String  // e.g. "The Opening"
    let revelationType: RevelationType
    let numberOfAyahs: Int
    var ayahs: [Ayah]

    enum RevelationType: String, Codable {
        case meccan
        case medinan
    }
}
