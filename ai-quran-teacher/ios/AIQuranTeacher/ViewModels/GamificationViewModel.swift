import Foundation

@MainActor
final class GamificationViewModel: ObservableObject {
    @Published var profile: GamificationProfile?
    @Published var leaderboard: [LeaderboardEntry] = []
    @Published var badgeCatalog: [Badge] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let api: APIService
    private let userId: String

    init(userId: String, api: APIService = .shared) {
        self.userId = userId
        self.api = api
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }
        errorMessage = nil
        do {
            async let profile = api.fetchProfile(userId: userId)
            async let leaderboard = api.fetchLeaderboard()
            self.profile = try await profile
            self.leaderboard = try await leaderboard
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
