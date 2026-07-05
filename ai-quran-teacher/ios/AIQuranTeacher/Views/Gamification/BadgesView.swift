import SwiftUI

struct BadgesView: View {
    let badges: [Badge]

    private let columns = [GridItem(.adaptive(minimum: 100), spacing: 12)]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Badges").font(.title3.bold())
            if badges.isEmpty {
                Text("No badges yet — complete quizzes and keep your streak going!")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                LazyVGrid(columns: columns, spacing: 12) {
                    ForEach(badges) { badge in
                        VStack(spacing: 6) {
                            Text(badge.icon).font(.system(size: 36))
                            Text(badge.name)
                                .font(.caption.bold())
                                .multilineTextAlignment(.center)
                            Text("+\(badge.xpReward) XP")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(RoundedRectangle(cornerRadius: 12).fill(Color(.secondarySystemBackground)))
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
