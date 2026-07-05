import SwiftUI

/// Renders one ayah: Arabic text (with mistake highlighting), translation,
/// bookmark control, and the Tajweed rules present in the ayah.
struct AyahView: View {
    let ayah: Ayah
    let mistakes: [TajweedMistake]
    let rules: [TajweedRuleOccurrence]
    let isBookmarked: Bool
    let onBookmark: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Ayah \(ayah.numberInSurah)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Spacer()
                Button(action: onBookmark) {
                    Image(systemName: isBookmarked ? "bookmark.fill" : "bookmark")
                }
                .accessibilityLabel(isBookmarked ? "Remove bookmark" : "Add bookmark")
            }

            highlightedArabicText
                .font(.custom("KFGQPC Uthmanic Script HAFS", size: 30, relativeTo: .title))
                .lineSpacing(14)
                .frame(maxWidth: .infinity, alignment: .trailing)
                .environment(\.layoutDirection, .rightToLeft)

            if let translation = ayah.translation {
                Text(translation)
                    .font(.body)
                    .foregroundStyle(.secondary)
            }

            if !rules.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(rules, id: \.self) { rule in
                            Text(rule.rule.replacingOccurrences(of: "_", with: " "))
                                .font(.caption2)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Capsule().fill(Color.accentColor.opacity(0.12)))
                        }
                    }
                }
            }
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(.background.secondary))
    }

    /// Word-level highlighting: words the engine flagged are tinted red.
    private var highlightedArabicText: Text {
        let words = ayah.text.split(separator: " ").map(String.init)
        let flaggedIndexes = Set(mistakes.map(\.wordIndex))
        var result = Text("")
        for (index, word) in words.enumerated() {
            let piece = Text(word)
                .foregroundColor(flaggedIndexes.contains(index) ? .red : .primary)
            result = index == 0 ? piece : result + Text(" ") + piece
        }
        return result
    }
}
