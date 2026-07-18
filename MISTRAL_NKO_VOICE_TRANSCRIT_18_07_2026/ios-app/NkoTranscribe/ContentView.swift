import SwiftUI

struct ContentView: View {
    @StateObject private var recorder = AudioRecorder()
    @State private var latin = ""
    @State private var nko = ""
    @State private var busy = false
    @State private var errorMessage: String?

    private let api = APIClient()

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("ߒߞߏ N'Ko Voice")
                .font(.title2.bold())

            Button {
                Task { await toggleRecording() }
            } label: {
                Text(recorder.isRecording ? "■ Stop" : "● Record")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(recorder.isRecording ? .red : .accentColor)
            .disabled(busy)

            if busy { ProgressView("Transcribing…") }
            if let errorMessage {
                Text(errorMessage).foregroundStyle(.red)
            }

            if !latin.isEmpty {
                Text("Latin").font(.caption.bold())
                Text(latin)
            }
            if !nko.isEmpty {
                Text("N'Ko").font(.caption.bold())
                Text(nko)
                    .font(.system(size: 26))
                    .environment(\.layoutDirection, .rightToLeft)
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
            Spacer()
            Text("Audio is uploaded for transcription and immediately discarded.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .padding()
    }

    private func toggleRecording() async {
        errorMessage = nil
        if recorder.isRecording {
            guard let fileURL = recorder.stop() else { return }
            busy = true
            defer { busy = false }
            do {
                let result = try await api.transcribe(fileURL: fileURL)
                latin = result.latinText
                nko = result.nkoText
            } catch {
                errorMessage = "Transcription failed: \(error)"
            }
            recorder.discard(fileURL)  // audio never persists on device
        } else {
            guard await recorder.requestPermission() else {
                errorMessage = "Microphone permission is required."
                return
            }
            do { try recorder.start() } catch {
                errorMessage = "Could not start recording."
            }
        }
    }
}
