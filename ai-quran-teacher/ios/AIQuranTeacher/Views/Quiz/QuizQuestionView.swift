import SwiftUI

struct QuizQuestionView: View {
    let question: QuizQuestion
    let questionNumber: Int
    let totalQuestions: Int
    let selectedIndex: Int?
    let onSelect: (Int) -> Void
    let onNext: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            ProgressView(value: Double(questionNumber - 1), total: Double(max(totalQuestions, 1)))

            Text("Question \(questionNumber) of \(totalQuestions)")
                .font(.caption)
                .foregroundStyle(.secondary)

            Text(question.question)
                .font(.title3.weight(.semibold))

            ForEach(Array(question.options.enumerated()), id: \.offset) { index, option in
                Button {
                    onSelect(index)
                } label: {
                    HStack {
                        Image(systemName: selectedIndex == index ? "largecircle.fill.circle" : "circle")
                        Text(option).multilineTextAlignment(.leading)
                        Spacer()
                    }
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(selectedIndex == index ? Color.accentColor.opacity(0.15) : Color(.secondarySystemBackground))
                    )
                }
                .buttonStyle(.plain)
            }

            Spacer()

            Button {
                onNext()
            } label: {
                Text(questionNumber == totalQuestions ? "Submit" : "Next")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding()
            }
            .buttonStyle(.borderedProminent)
            .disabled(selectedIndex == nil)
        }
        .padding()
    }
}
