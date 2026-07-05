import SwiftUI

struct StreakView: View {
    let streak: StreakInfo

    var body: some View {
        HStack(spacing: 0) {
            stat(value: streak.current, label: "Current streak", icon: "flame.fill", tint: .orange)
            Divider().padding(.vertical, 8)
            stat(value: streak.longest, label: "Longest streak", icon: "crown.fill", tint: .yellow)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))
    }

    private func stat(value: Int, label: String, icon: String, tint: Color) -> some View {
        VStack(spacing: 4) {
            Image(systemName: icon).foregroundStyle(tint)
            Text("\(value)").font(.title.bold())
            Text(label).font(.caption).foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}
