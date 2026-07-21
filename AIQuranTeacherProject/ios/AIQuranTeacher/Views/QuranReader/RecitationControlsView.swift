import SwiftUI

/// Record / playback controls shown beneath the ayah list.
struct RecitationControlsView: View {
    let isRecording: Bool
    let onRecord: () -> Void
    let onPlayReference: () -> Void
    let onPlayUser: () -> Void

    var body: some View {
        HStack(spacing: 24) {
            Button(action: onPlayReference) {
                Label("Reference", systemImage: "speaker.wave.2.fill")
            }
            Button(action: onRecord) {
                Image(systemName: isRecording ? "stop.circle.fill" : "mic.circle.fill")
                    .font(.system(size: 48))
                    .foregroundColor(isRecording ? .red : .accentColor)
            }
            Button(action: onPlayUser) {
                Label("My reading", systemImage: "play.circle")
            }
        }
        .buttonStyle(.plain)
    }
}
