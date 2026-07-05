import SwiftUI

/// Bottom bar: previous/next ayah and the record button.
struct RecitationControlsView: View {
    @ObservedObject var viewModel: QuranReaderViewModel

    var body: some View {
        HStack(spacing: 32) {
            Button {
                viewModel.goToPreviousAyah()
            } label: {
                Image(systemName: "chevron.backward.circle")
                    .font(.title)
            }
            .disabled(viewModel.currentAyahIndex == 0)

            Button {
                Task {
                    if viewModel.speechRecognizer.isRecording {
                        await viewModel.finishRecitation()
                    } else {
                        await viewModel.startRecitation()
                    }
                }
            } label: {
                ZStack {
                    Circle()
                        .fill(viewModel.speechRecognizer.isRecording ? Color.red : Color.accentColor)
                        .frame(width: 64, height: 64)
                    if viewModel.isAnalyzing {
                        ProgressView().tint(.white)
                    } else {
                        Image(systemName: viewModel.speechRecognizer.isRecording ? "stop.fill" : "mic.fill")
                            .font(.title2)
                            .foregroundStyle(.white)
                    }
                }
            }
            .disabled(viewModel.isAnalyzing)
            .accessibilityLabel(viewModel.speechRecognizer.isRecording ? "Stop recitation" : "Start recitation")

            Button {
                viewModel.goToNextAyah()
            } label: {
                Image(systemName: "chevron.forward.circle")
                    .font(.title)
            }
            .disabled(viewModel.currentAyahIndex >= viewModel.surah.ayahs.count - 1)
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(.bar)
    }
}
