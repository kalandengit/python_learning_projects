import Foundation
import WebRTC

/// Manages the RTCPeerConnection for live classes.
/// Add the SPM dependency: https://github.com/stasel/WebRTC
protocol WebRTCManagerDelegate: AnyObject {
    func webRTC(_ manager: WebRTCManager, didGenerateCandidate candidate: RTCIceCandidate)
    func webRTC(_ manager: WebRTCManager, didReceiveRemoteVideoTrack track: RTCVideoTrack)
    func webRTC(_ manager: WebRTCManager, didChangeConnectionState state: RTCIceConnectionState)
}

final class WebRTCManager: NSObject {
    weak var delegate: WebRTCManagerDelegate?

    private static let factory: RTCPeerConnectionFactory = {
        RTCInitializeSSL()
        return RTCPeerConnectionFactory(
            encoderFactory: RTCDefaultVideoEncoderFactory(),
            decoderFactory: RTCDefaultVideoDecoderFactory()
        )
    }()

    private var peerConnection: RTCPeerConnection?
    private(set) var localVideoTrack: RTCVideoTrack?
    private(set) var localAudioTrack: RTCAudioTrack?
    private var videoCapturer: RTCCameraVideoCapturer?

    private let mediaConstraints = RTCMediaConstraints(
        mandatoryConstraints: [
            kRTCMediaConstraintsOfferToReceiveAudio: kRTCMediaConstraintsValueTrue,
            kRTCMediaConstraintsOfferToReceiveVideo: kRTCMediaConstraintsValueTrue,
        ],
        optionalConstraints: nil
    )

    func setup(iceServers: [String] = ["stun:stun.l.google.com:19302"]) {
        let config = RTCConfiguration()
        config.iceServers = [RTCIceServer(urlStrings: iceServers)]
        config.sdpSemantics = .unifiedPlan
        config.continualGatheringPolicy = .gatherContinually

        peerConnection = Self.factory.peerConnection(
            with: config,
            constraints: RTCMediaConstraints(mandatoryConstraints: nil, optionalConstraints: nil),
            delegate: self
        )
        setupLocalMedia()
    }

    private func setupLocalMedia() {
        guard let peerConnection else { return }

        let audioSource = Self.factory.audioSource(
            with: RTCMediaConstraints(mandatoryConstraints: nil, optionalConstraints: nil)
        )
        let audioTrack = Self.factory.audioTrack(with: audioSource, trackId: "audio0")
        localAudioTrack = audioTrack
        peerConnection.add(audioTrack, streamIds: ["stream0"])

        let videoSource = Self.factory.videoSource()
        videoCapturer = RTCCameraVideoCapturer(delegate: videoSource)
        let videoTrack = Self.factory.videoTrack(with: videoSource, trackId: "video0")
        localVideoTrack = videoTrack
        peerConnection.add(videoTrack, streamIds: ["stream0"])
    }

    func startCapture() {
        guard let capturer = videoCapturer,
              let camera = RTCCameraVideoCapturer.captureDevices()
                .first(where: { $0.position == .front }),
              let format = RTCCameraVideoCapturer.supportedFormats(for: camera)
                .sorted(by: { dimensions(of: $0) < dimensions(of: $1) })
                .last,
              let fps = format.videoSupportedFrameRateRanges.first
        else { return }
        capturer.startCapture(with: camera, format: format, fps: Int(fps.maxFrameRate))
    }

    private func dimensions(of format: AVCaptureDevice.Format) -> Int32 {
        let dims = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
        return dims.width * dims.height
    }

    // MARK: - SDP negotiation

    func createOffer() async throws -> String {
        guard let peerConnection else { throw WebRTCError.notConfigured }
        let sdp = try await peerConnection.offer(for: mediaConstraints)
        try await peerConnection.setLocalDescription(sdp)
        return sdp.sdp
    }

    func createAnswer(forRemoteOffer sdp: String) async throws -> String {
        guard let peerConnection else { throw WebRTCError.notConfigured }
        try await peerConnection.setRemoteDescription(
            RTCSessionDescription(type: .offer, sdp: sdp)
        )
        let answer = try await peerConnection.answer(for: mediaConstraints)
        try await peerConnection.setLocalDescription(answer)
        return answer.sdp
    }

    func setRemoteAnswer(_ sdp: String) async throws {
        guard let peerConnection else { throw WebRTCError.notConfigured }
        try await peerConnection.setRemoteDescription(
            RTCSessionDescription(type: .answer, sdp: sdp)
        )
    }

    func addRemoteCandidate(sdp: String, sdpMLineIndex: Int32, sdpMid: String?) async throws {
        guard let peerConnection else { throw WebRTCError.notConfigured }
        try await peerConnection.add(
            RTCIceCandidate(sdp: sdp, sdpMLineIndex: sdpMLineIndex, sdpMid: sdpMid)
        )
    }

    func close() {
        videoCapturer?.stopCapture()
        peerConnection?.close()
        peerConnection = nil
        localVideoTrack = nil
        localAudioTrack = nil
    }

    enum WebRTCError: Error {
        case notConfigured
    }
}

extension WebRTCManager: RTCPeerConnectionDelegate {
    func peerConnection(_ peerConnection: RTCPeerConnection, didGenerate candidate: RTCIceCandidate) {
        delegate?.webRTC(self, didGenerateCandidate: candidate)
    }

    func peerConnection(_ peerConnection: RTCPeerConnection, didChange newState: RTCIceConnectionState) {
        delegate?.webRTC(self, didChangeConnectionState: newState)
    }

    func peerConnection(_ peerConnection: RTCPeerConnection, didStartReceivingOn transceiver: RTCRtpTransceiver) {
        if let track = transceiver.receiver.track as? RTCVideoTrack {
            delegate?.webRTC(self, didReceiveRemoteVideoTrack: track)
        }
    }

    // Unused delegate requirements.
    func peerConnection(_ peerConnection: RTCPeerConnection, didChange stateChanged: RTCSignalingState) {}
    func peerConnection(_ peerConnection: RTCPeerConnection, didAdd stream: RTCMediaStream) {}
    func peerConnection(_ peerConnection: RTCPeerConnection, didRemove stream: RTCMediaStream) {}
    func peerConnectionShouldNegotiate(_ peerConnection: RTCPeerConnection) {}
    func peerConnection(_ peerConnection: RTCPeerConnection, didChange newState: RTCIceGatheringState) {}
    func peerConnection(_ peerConnection: RTCPeerConnection, didRemove candidates: [RTCIceCandidate]) {}
    func peerConnection(_ peerConnection: RTCPeerConnection, didOpen dataChannel: RTCDataChannel) {}
}
