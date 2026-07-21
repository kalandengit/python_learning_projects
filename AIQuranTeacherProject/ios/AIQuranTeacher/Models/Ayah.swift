import Foundation

struct Ayah: Identifiable, Codable {
    let id: Int
    let surahId: Int
    let number: Int
    let text: String
    let translation: String?
    let referenceAudioURL: URL?
    let userRecordingURL: URL?
}
