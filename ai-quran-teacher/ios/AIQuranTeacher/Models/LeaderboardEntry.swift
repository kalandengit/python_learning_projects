import Foundation

/// One row of `GET /gamification/leaderboard`.
struct LeaderboardEntry: Identifiable, Codable, Hashable {
    let id: String
    let userId: String
    let xp: Int
    let level: Int
}
