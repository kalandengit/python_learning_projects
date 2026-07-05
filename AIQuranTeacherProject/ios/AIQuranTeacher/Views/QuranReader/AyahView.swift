import SwiftUI

/// Renders a single ayah with its translation and any detected tajweed hints.
struct AyahView: View {
    let ayah: Ayah
    let isSelected: Bool
    let mistakes: [TajweedMistake]
    let isBookmarked: Bool

    var body: some View {
        VStack(alignment: .trailing, spacing: 8) {
            HStack {
                if isBookmarked {
                    Image(systemName: "bookmark.fill").foregroundColor(.accentColor)
                }
                Spacer()
                Text("\(ayah.number)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Text(ayah.text)
                .font(.system(size: 26, weight: .medium))
                .multilineTextAlignment(.trailing)
                .frame(maxWidth: .infinity, alignment: .trailing)
            if let translation = ayah.translation {
                Text(translation)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            if !mistakes.isEmpty {
                Text("\(mistakes.count) tajweed note\(mistakes.count == 1 ? "" : "s")")
                    .font(.caption)
                    .foregroundColor(.orange)
            }
        }
        .padding()
        .background(isSelected ? Color.accentColor.opacity(0.1) : Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}
