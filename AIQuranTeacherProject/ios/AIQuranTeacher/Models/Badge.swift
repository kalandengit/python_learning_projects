import Foundation

/// Mirrors the backend badge catalogue entry.
struct Badge: Identifiable, Codable {
    let id: String
    let name: String
    let description: String
}

/// Mirrors `GET /api/gamification/me`.
struct GamificationProfile: Codable {
    let userId: String
    let points: Int
    let currentStreak: Int
    let longestStreak: Int
    let lastActivityDate: String?
    let badges: [Badge]
}
