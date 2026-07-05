import SwiftUI

struct ExamView: View {
    @StateObject var viewModel: ExamViewModel

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.background.ignoresSafeArea()
                Theme.ambientGradient.ignoresSafeArea()

                switch viewModel.phase {
                case .pickingLevel:
                    levelPicker
                case .inProgress:
                    if let question = viewModel.currentQuestion {
                        examQuestion(question)
                    }
                case .submitting:
                    ProgressView("Grading your exam…")
                case let .finished(result):
                    ExamResultView(result: result) { viewModel.reset() }
                }
            }
            .navigationTitle("Certification")
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }

    private var levelPicker: some View {
        ScrollView {
            VStack(spacing: Theme.spacing) {
                FeatureHeader(
                    title: "Earn a Certificate",
                    subtitle: "Timed Tajweed exams with a verifiable credential",
                    systemImage: "rosette"
                )

                ForEach(ExamLevel.allCases) { level in
                    Button {
                        Task { await viewModel.start(level: level) }
                    } label: {
                        GlassCard {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(level.title).font(.headline)
                                    Text(examBlurb(level))
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .foregroundStyle(Theme.emerald)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding()
        }
    }

    private func examBlurb(_ level: ExamLevel) -> String {
        switch level {
        case .foundation: "8 questions · 15 min · pass 70%"
        case .intermediate: "10 questions · 20 min · pass 70%"
        case .advanced: "10 questions · 30 min · pass 80%"
        }
    }

    private func examQuestion(_ question: QuizQuestion) -> some View {
        VStack(spacing: Theme.spacing) {
            // Timer + progress header.
            HStack {
                Label(viewModel.timeString, systemImage: "clock")
                    .font(.headline.monospacedDigit())
                    .foregroundStyle(viewModel.secondsRemaining < 60 ? Theme.coral : Theme.emerald)
                Spacer()
                if let exam = viewModel.exam {
                    Text("\(viewModel.currentIndex + 1) / \(exam.questions.count)")
                        .font(.subheadline).foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal)

            ScrollView {
                GlassCard {
                    VStack(alignment: .leading, spacing: 16) {
                        Text(question.question).font(.title3.weight(.semibold))
                        ForEach(Array(question.options.enumerated()), id: \.offset) { index, option in
                            Button {
                                viewModel.select(index)
                            } label: {
                                HStack {
                                    Image(systemName: viewModel.answers[viewModel.currentIndex] == index
                                          ? "largecircle.fill.circle" : "circle")
                                        .foregroundStyle(Theme.emerald)
                                    Text(option).multilineTextAlignment(.leading)
                                    Spacer()
                                }
                                .padding()
                                .background(
                                    RoundedRectangle(cornerRadius: Theme.cornerRadiusSmall)
                                        .fill(viewModel.answers[viewModel.currentIndex] == index
                                              ? Theme.emerald.opacity(0.12) : Theme.background)
                                )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding(.horizontal)
            }

            PrimaryButton(
                title: viewModel.currentIndex == (viewModel.exam?.questions.count ?? 1) - 1
                    ? "Submit exam" : "Next question"
            ) {
                Task { await viewModel.advance() }
            }
            .padding()
            .disabled(viewModel.answers[viewModel.currentIndex] == nil)
        }
    }
}
