import SwiftUI

/// The AI Islamic tutor. One question fans out to several Claude calls on the
/// backend (answer, tafsir, tajweed, follow-ups), each shown as its own card.
struct TutorView: View {
    @StateObject var viewModel: TutorViewModel

    var body: some View {
        NavigationStack {
            ZStack {
                Theme.background.ignoresSafeArea()
                Theme.ambientGradient.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: Theme.spacing) {
                        FeatureHeader(
                            title: "Ask the Teacher",
                            subtitle: "Sourced answers, tafsir, and Tajweed — together",
                            systemImage: "sparkles"
                        )

                        askBox

                        if viewModel.isLoading {
                            loadingCards
                        }

                        if let response = viewModel.response {
                            ForEach(response.aspects) { aspect in
                                aspectCard(aspect)
                            }
                            Text("Answers are AI-generated for study. For religious rulings, consult a qualified scholar.")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.top, 4)
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("AI Tutor")
            .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
        }
    }

    private var askBox: some View {
        GlassCard {
            VStack(spacing: 12) {
                if let context = viewModel.context, !context.isEmpty {
                    Chip(text: "Using current ayah as context", tint: Theme.lapis)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                TextField(
                    "e.g. What is the ruling of Ikhfa here?",
                    text: $viewModel.question,
                    axis: .vertical
                )
                .lineLimit(1...4)
                .padding(12)
                .background(RoundedRectangle(cornerRadius: Theme.cornerRadiusSmall).fill(Theme.background))

                PrimaryButton(
                    title: "Ask",
                    icon: "paperplane.fill",
                    isLoading: viewModel.isLoading
                ) {
                    Task { await viewModel.ask() }
                }
                .disabled(viewModel.question.trimmingCharacters(in: .whitespaces).count < 3)
            }
        }
    }

    private var loadingCards: some View {
        VStack(spacing: Theme.spacing) {
            ForEach(TutorAspect.allCases) { aspect in
                GlassCard {
                    HStack {
                        Image(systemName: aspect.icon).foregroundStyle(Theme.emerald)
                        Text(aspect.title).font(.headline)
                        Spacer()
                        ProgressView()
                    }
                }
            }
        }
    }

    private func aspectCard(_ aspect: TutorAspectResult) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Image(systemName: aspect.aspect.icon).foregroundStyle(Theme.emerald)
                    Text(aspect.aspect.title).font(.headline)
                }
                if let text = aspect.text {
                    Text(text).font(.body)
                } else if let error = aspect.error {
                    Text("Couldn't load this section: \(error)")
                        .font(.caption).foregroundStyle(Theme.coral)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}
