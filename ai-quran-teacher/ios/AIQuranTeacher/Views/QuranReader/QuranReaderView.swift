import SwiftUI

struct QuranReaderView: View {
    @StateObject var viewModel: QuranReaderViewModel

    var body: some View {
        VStack(spacing: 0) {
            if let ayah = viewModel.currentAyah {
                ScrollView {
                    AyahView(
                        ayah: ayah,
                        mistakes: viewModel.detectionResult?.mistakes ?? [],
                        rules: viewModel.detectionResult?.rulesToObserve ?? [],
                        isBookmarked: viewModel.bookmarkedAyahIds.contains(ayah.id),
                        onBookmark: { viewModel.toggleBookmark(for: ayah) }
                    )
                    .padding()

                    if let result = viewModel.detectionResult {
                        feedbackSection(result)
                            .padding(.horizontal)
                    }

                    if !viewModel.speechRecognizer.transcript.isEmpty {
                        GroupBox("Heard") {
                            Text(viewModel.speechRecognizer.transcript)
                                .frame(maxWidth: .infinity, alignment: .trailing)
                                .environment(\.layoutDirection, .rightToLeft)
                        }
                        .padding(.horizontal)
                    }
                }
            } else {
                ContentUnavailableView("No ayahs", systemImage: "book")
            }

            RecitationControlsView(viewModel: viewModel)
        }
        .navigationTitle(viewModel.surah.englishName)
        .navigationBarTitleDisplayMode(.inline)
        .alert("Error", isPresented: .constant(viewModel.errorMessage != nil)) {
            Button("OK") { viewModel.errorMessage = nil }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    @ViewBuilder
    private func feedbackSection(_ result: TajweedDetectionResult) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(
                "Accuracy: \(Int(result.accuracy * 100))%",
                systemImage: result.accuracy >= 0.9 ? "checkmark.seal.fill" : "exclamationmark.triangle"
            )
            .font(.headline)
            .foregroundStyle(result.accuracy >= 0.9 ? .green : .orange)

            ForEach(result.mistakes) { mistake in
                VStack(alignment: .leading, spacing: 2) {
                    Text(mistake.suggestion).font(.subheadline)
                    Text(mistake.severity.rawValue.capitalized)
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Capsule().fill(severityColor(mistake.severity).opacity(0.2)))
                }
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 8).fill(.quaternary.opacity(0.5)))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func severityColor(_ severity: TajweedMistake.Severity) -> Color {
        switch severity {
        case .minor: .yellow
        case .moderate: .orange
        case .major: .red
        }
    }
}
