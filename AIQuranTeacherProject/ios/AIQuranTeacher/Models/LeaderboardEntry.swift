import Foundation

/// Mirrors an entry from `GET /api/gamification/leaderboard`.
struct LeaderboardEntry: Identifiable, Codable {
    var id: String { userId }
    let rank: Int
    let userId: String
    let displayName: String
    let points: Int
    let currentStreak: Int
}
