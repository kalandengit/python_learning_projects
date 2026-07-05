import Foundation

/// A badge from the backend catalog (`GET /gamification/badges`).
struct Badge: Identifiable, Codable, Hashable {
    let code: String
    let name: String
    let description: String
    let icon: String
    let xpReward: Int
    var id: String { code }
}

/// Streak summary inside the gamification profile.
struct StreakInfo: Codable, Hashable {
    let current: Int
    let longest: Int
    let lastActivityDate: String?
}

/// Response shape of `GET /gamification/profile/:userId`.
struct GamificationProfile: Codable {
    let userId: String
    let xp: Int
    let level: Int
    let streak: StreakInfo
    let badges: [Badge]
}
