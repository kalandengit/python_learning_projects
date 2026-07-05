import SwiftUI

struct LeaderboardView: View {
    let entries: [LeaderboardEntry]
    let currentUserId: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Leaderboard").font(.title3.bold())
            ForEach(Array(entries.enumerated()), id: \.element.id) { rank, entry in
                HStack {
                    Text("\(rank + 1)")
                        .font(.headline.monospacedDigit())
                        .frame(width: 28)
                        .foregroundStyle(rank < 3 ? Color.accentColor : .secondary)
                    VStack(alignment: .leading) {
                        Text(entry.userId == currentUserId ? "You" : "Student \(entry.userId.prefix(6))")
                            .font(.subheadline.bold())
                        Text("Level \(entry.level)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Text("\(entry.xp) XP")
                        .font(.subheadline.monospacedDigit())
                }
                .padding(10)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(entry.userId == currentUserId
                              ? Color.accentColor.opacity(0.12)
                              : Color(.secondarySystemBackground))
                )
            }
            if entries.isEmpty {
                Text("The leaderboard is empty — be the first!")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
