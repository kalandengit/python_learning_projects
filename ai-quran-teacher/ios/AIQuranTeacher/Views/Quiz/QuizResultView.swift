import SwiftUI

struct QuizResultView: View {
    let result: QuizResult
    let onDone: () -> Void

    private var percentage: Int {
        result.total == 0 ? 0 : Int(Double(result.score) / Double(result.total) * 100)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                Image(systemName: percentage == 100 ? "trophy.fill" : "checkmark.circle.fill")
                    .font(.system(size: 56))
                    .foregroundStyle(percentage == 100 ? .yellow : .green)

                Text("\(result.score) / \(result.total)")
                    .font(.system(size: 44, weight: .bold, design: .rounded))
                Text("+\(result.xpEarned) XP")
                    .font(.headline)
                    .foregroundStyle(Color.accentColor)

                if !result.newBadges.isEmpty {
                    Label("New badge: \(result.newBadges.joined(separator: ", "))",
                          systemImage: "rosette")
                        .font(.subheadline.bold())
                        .padding(8)
                        .background(Capsule().fill(.yellow.opacity(0.2)))
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text("Review").font(.title3.bold())
                    ForEach(result.review) { item in
                        HStack(alignment: .top, spacing: 10) {
                            Image(systemName: item.correct ? "checkmark.circle.fill" : "xmark.circle.fill")
                                .foregroundStyle(item.correct ? .green : .red)
                            Text(item.explanation)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))

                Button("Take another quiz", action: onDone)
                    .buttonStyle(.borderedProminent)
            }
            .padding()
        }
    }
}
