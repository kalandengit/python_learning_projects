import SwiftUI

struct GamificationView: View {
    @StateObject var viewModel: GamificationViewModel

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    if let profile = viewModel.profile {
                        levelHeader(profile)
                        StreakView(streak: profile.streak)
                        BadgesView(badges: profile.badges)
                    }
                    LeaderboardView(entries: viewModel.leaderboard,
                                    currentUserId: viewModel.profile?.userId)
                }
                .padding()
            }
            .navigationTitle("Progress")
            .overlay {
                if viewModel.isLoading && viewModel.profile == nil {
                    ProgressView()
                }
            }
            .refreshable { await viewModel.load() }
            .task { await viewModel.load() }
        }
    }

    private func levelHeader(_ profile: GamificationProfile) -> some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(Color.accentColor.opacity(0.15))
                    .frame(width: 72, height: 72)
                Text("Lv \(profile.level)")
                    .font(.headline)
            }
            VStack(alignment: .leading) {
                Text("\(profile.xp) XP")
                    .font(.title2.bold())
                Text("Keep practicing to level up")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))
    }
}
