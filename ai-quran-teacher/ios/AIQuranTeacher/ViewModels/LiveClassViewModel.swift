import Foundation
import WebRTC

struct ChatMessage: Identifiable, Hashable {
    let id = UUID()
    let userId: String
    let text: String
    let sentAt: Date
    let isMine: Bool
}

/// Coordinates WebRTC and signaling for a live class room.
@MainActor
final class LiveClassViewModel: NSObject, ObservableObject {
    @Published var connectionState: String = "Connecting…"
    @Published var chatMessages: [ChatMessage] = []
    @Published var participants: [String] = []
    @Published var remoteVideoTrack: RTCVideoTrack?
    @Published var errorMessage: String?

    let webRTC = WebRTCManager()
    private var signaling: SignalingClient?
    private let roomId: String
    private let userId: String
    private let signalingURL: URL

    init(roomId: String, userId: String, signalingURL: URL) {
        self.roomId = roomId
        self.userId = userId
        self.signalingURL = signalingURL
        super.init()
    }

    func join() {
        webRTC.delegate = self
        webRTC.setup()
        webRTC.startCapture()

        let client = SignalingClient(serverURL: signalingURL, roomId: roomId, userId: userId)
        client.delegate = self
        client.connect()
        signaling = client
    }

    func leave() {
        signaling?.disconnect()
        signaling = nil
        webRTC.close()
    }

    func sendChat(_ text: String) {
        guard !text.isEmpty else { return }
        signaling?.send(chatMessage: text)
        chatMessages.append(ChatMessage(userId: userId, text: text, sentAt: Date(), isMine: true))
    }

    func sendDrawing(points: [CGPoint], color: String) {
        let drawing: [String: Any] = [
            "points": points.map { ["x": $0.x, "y": $0.y] },
            "color": color,
        ]
        signaling?.send(drawing: drawing)
    }
}

extension LiveClassViewModel: SignalingClientDelegate {
    nonisolated func signaling(_ client: SignalingClient, didReceiveOffer sdp: String, from socketId: String) {
        Task { @MainActor in
            do {
                let answer = try await webRTC.createAnswer(forRemoteOffer: sdp)
                client.send(answer: answer, to: socketId)
            } catch {
                errorMessage = "Failed to answer call: \(error.localizedDescription)"
            }
        }
    }

    nonisolated func signaling(_ client: SignalingClient, didReceiveAnswer sdp: String, from socketId: String) {
        Task { @MainActor in
            try? await webRTC.setRemoteAnswer(sdp)
        }
    }

    nonisolated func signaling(_ client: SignalingClient, didReceiveCandidate candidate: [String: Any], from socketId: String) {
        Task { @MainActor in
            guard let sdp = candidate["candidate"] as? String else { return }
            let mLineIndex = Int32(candidate["sdpMLineIndex"] as? Int ?? 0)
            let mid = candidate["sdpMid"] as? String
            try? await webRTC.addRemoteCandidate(sdp: sdp, sdpMLineIndex: mLineIndex, sdpMid: mid)
        }
    }

    nonisolated func signaling(_ client: SignalingClient, userJoined userId: String, socketId: String) {
        Task { @MainActor in
            participants.append(userId)
            // Existing participant initiates the offer toward the newcomer.
            do {
                let offer = try await webRTC.createOffer()
                client.send(offer: offer, to: socketId)
            } catch {
                errorMessage = "Failed to start call: \(error.localizedDescription)"
            }
        }
    }

    nonisolated func signaling(_ client: SignalingClient, userLeft userId: String, socketId: String) {
        Task { @MainActor in
            participants.removeAll { $0 == userId }
        }
    }

    nonisolated func signaling(_ client: SignalingClient, didReceiveChat message: String, from userId: String) {
        Task { @MainActor in
            chatMessages.append(ChatMessage(userId: userId, text: message, sentAt: Date(), isMine: false))
        }
    }

    nonisolated func signaling(_ client: SignalingClient, didReceiveDrawing drawing: [String: Any], from userId: String) {
        // Forwarded to WhiteboardView via NotificationCenter to keep the
        // drawing model out of this view model.
        NotificationCenter.default.post(name: .remoteDrawingReceived, object: drawing)
    }
}

extension LiveClassViewModel: WebRTCManagerDelegate {
    nonisolated func webRTC(_ manager: WebRTCManager, didGenerateCandidate candidate: RTCIceCandidate) {
        Task { @MainActor in
            signaling?.send(candidate: [
                "candidate": candidate.sdp,
                "sdpMLineIndex": Int(candidate.sdpMLineIndex),
                "sdpMid": candidate.sdpMid ?? "",
            ])
        }
    }

    nonisolated func webRTC(_ manager: WebRTCManager, didReceiveRemoteVideoTrack track: RTCVideoTrack) {
        Task { @MainActor in
            remoteVideoTrack = track
        }
    }

    nonisolated func webRTC(_ manager: WebRTCManager, didChangeConnectionState state: RTCIceConnectionState) {
        Task { @MainActor in
            switch state {
            case .connected, .completed: connectionState = "Connected"
            case .disconnected: connectionState = "Reconnecting…"
            case .failed, .closed: connectionState = "Disconnected"
            default: connectionState = "Connecting…"
            }
        }
    }
}

extension Notification.Name {
    static let remoteDrawingReceived = Notification.Name("remoteDrawingReceived")
}
