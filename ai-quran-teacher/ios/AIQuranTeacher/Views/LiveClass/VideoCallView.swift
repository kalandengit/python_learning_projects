import SwiftUI
import WebRTC

/// Wraps RTCMTLVideoView for SwiftUI.
struct RTCVideoView: UIViewRepresentable {
    let track: RTCVideoTrack?

    func makeUIView(context: Context) -> RTCMTLVideoView {
        let view = RTCMTLVideoView()
        view.videoContentMode = .scaleAspectFill
        return view
    }

    func updateUIView(_ uiView: RTCMTLVideoView, context: Context) {
        track?.add(uiView)
    }
}

struct VideoCallView: View {
    @ObservedObject var viewModel: LiveClassViewModel

    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            // Remote participant (teacher/student) fills the screen.
            if let remote = viewModel.remoteVideoTrack {
                RTCVideoView(track: remote)
                    .ignoresSafeArea(edges: .bottom)
            } else {
                ContentUnavailableView(
                    "Waiting for others to join",
                    systemImage: "person.2.wave.2",
                    description: Text("Share the class code with your teacher or students.")
                )
            }

            // Local self-view, picture-in-picture style.
            RTCVideoView(track: viewModel.webRTC.localVideoTrack)
                .frame(width: 110, height: 160)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(.white.opacity(0.6)))
                .padding()
        }
    }
}
