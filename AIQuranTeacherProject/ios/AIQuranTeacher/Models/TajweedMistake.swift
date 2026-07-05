import Foundation

enum TajweedRule: String, Codable {
    case noonSakin = "Noon Sakin"
    case madd = "Madd"
    case ikhfa = "Ikhfa"
    case idgham = "Idgham"
    case izhar = "Izhar"
    case iqlab = "Iqlab"
    case qalqalah = "Qalqalah"
    case ghunnah = "Ghunnah"
    case laamShamsiyyah = "Laam Shamsiyyah"
    case makharij = "Makharij"
}

enum Severity: String, Codable {
    case minor, moderate, major
}

struct TajweedMistake: Identifiable, Codable {
    let id: UUID
    let ayahId: Int
    let rule: TajweedRule
    let position: Int
    let severity: Severity
    let suggestion: String?
}
