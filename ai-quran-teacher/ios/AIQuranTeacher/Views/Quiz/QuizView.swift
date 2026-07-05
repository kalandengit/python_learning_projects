import SwiftUI

struct QuizView: View {
    @StateObject var viewModel: QuizViewModel

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.phase {
                case .pickingDifficulty:
                    difficultyPicker
                case .answering:
                    if let question = viewModel.currentQuestion {
                        QuizQuestionView(
                            question: question,
                            questionNumber: viewModel.currentQuestionIndex + 1,
                            totalQuestions: viewModel.quiz?.questions.count ?? 0,
                            selectedIndex: viewModel.selectedAnswers[viewModel.currentQuestionIndex],
                            onSelect: { viewModel.select(answer: $0) },
                            onNext: { Task { await viewModel.advance() } }
                        )
                    }
                case .submitting:
                    ProgressView("Grading…")
                case let .finished(result):
                    QuizResultView(result: result) {
                        viewModel.reset()
                    }
                }
            }
            .navigationTitle("Tajweed Quiz")
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }

    private var difficultyPicker: some View {
        VStack(spacing: 20) {
            Image(systemName: "questionmark.circle.fill")
                .font(.system(size: 56))
                .foregroundStyle(Color.accentColor)
            Text("Choose a difficulty")
                .font(.title2.bold())
            ForEach(QuizDifficulty.allCases) { difficulty in
                Button {
                    Task { await viewModel.start(difficulty: difficulty) }
                } label: {
                    Text(difficulty.rawValue.capitalized)
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 12).fill(Color.accentColor.opacity(0.12)))
                }
            }
        }
        .padding()
    }
}
