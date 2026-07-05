import Foundation
import SocketIO

/// Socket.IO client for the signaling server (`signaling-server/server.js`).
/// Add the SPM dependency: https://github.com/socketio/socket.io-client-swift
protocol SignalingClientDelegate: AnyObject {
    func signaling(_ client: SignalingClient, didReceiveOffer sdp: String, from socketId: String)
    func signaling(_ client: SignalingClient, didReceiveAnswer sdp: String, from socketId: String)
    func signaling(_ client: SignalingClient, didReceiveCandidate candidate: [String: Any], from socketId: String)
    func signaling(_ client: SignalingClient, userJoined userId: String, socketId: String)
    func signaling(_ client: SignalingClient, userLeft userId: String, socketId: String)
    func signaling(_ client: SignalingClient, didReceiveChat message: String, from userId: String)
    func signaling(_ client: SignalingClient, didReceiveDrawing drawing: [String: Any], from userId: String)
}

final class SignalingClient {
    weak var delegate: SignalingClientDelegate?

    private let manager: SocketManager
    private var socket: SocketIOClient { manager.defaultSocket }
    private let roomId: String
    private let userId: String

    init(serverURL: URL, roomId: String, userId: String) {
        self.roomId = roomId
        self.userId = userId
        manager = SocketManager(socketURL: serverURL, config: [.compress, .reconnects(true)])
        registerHandlers()
    }

    func connect() {
        socket.connect()
    }

    func disconnect() {
        socket.emit("leave", ["roomId": roomId])
        socket.disconnect()
    }

    // MARK: - Outbound

    func send(offer sdp: String, to socketId: String? = nil) {
        var payload: [String: Any] = ["sdp": sdp, "roomId": roomId, "userId": userId]
        if let socketId { payload["to"] = socketId }
        socket.emit("offer", payload)
    }

    func send(answer sdp: String, to socketId: String? = nil) {
        var payload: [String: Any] = ["sdp": sdp, "roomId": roomId, "userId": userId]
        if let socketId { payload["to"] = socketId }
        socket.emit("answer", payload)
    }

    func send(candidate: [String: Any], to socketId: String? = nil) {
        var payload: [String: Any] = ["candidate": candidate, "roomId": roomId, "userId": userId]
        if let socketId { payload["to"] = socketId }
        socket.emit("iceCandidate", payload)
    }

    func send(chatMessage: String) {
        socket.emit("chatMessage", ["message": chatMessage, "roomId": roomId, "userId": userId])
    }

    func send(drawing: [String: Any]) {
        socket.emit("drawing", ["drawing": drawing, "roomId": roomId, "userId": userId])
    }

    // MARK: - Inbound

    private func registerHandlers() {
        socket.on(clientEvent: .connect) { [weak self] _, _ in
            guard let self else { return }
            self.socket.emit("join", ["roomId": self.roomId, "userId": self.userId])
        }
        socket.on("offer") { [weak self] data, _ in
            guard let self, let payload = data.first as? [String: Any],
                  let sdp = payload["sdp"] as? String,
                  let socketId = payload["socketId"] as? String else { return }
            self.delegate?.signaling(self, didReceiveOffer: sdp, from: socketId)
        }
        socket.on("answer") { [weak self] data, _ in
            guard let self, let payload = data.first as? [String: Any],
                  let sdp = payload["sdp"] as? String,
                  let socketId = payload["socketId"] as? String else { return }
            self.delegate?.signaling(self, didReceiveAnswer: sdp, from: socketId)
        }
        socket.on("iceCandidate") { [weak self] data, _ in
            guard let self, let payload = data.first as? [String: Any],
                  let candidate = payload["candidate"] as? [String: Any],
                  let socketId = payload["socketId"] as? String else { return }
            self.delegate?.signaling(self, didReceiveCandidate: candidate, from: socketId)
        }
        socket.on("userJoined") { [weak self] data, _ in
            guard let self, let payload = data.first as? [String: Any],
                  let userId = payload["userId"] as? String,
                  let socketId = payload["socketId"] as? String else { return }
            self.delegate?.signaling(self, userJoined: userId, socketId: socketId)
        }
        socket.on("userLeft") { [weak self] data, _ in
            guard let self, let payload = data.first as? [String: Any],
                  let userId = payload["userId"] as? String,
                  let socketId = payload["socketId"] as? String else { return }
            self.delegate?.signaling(self, userLeft: userId, socketId: socketId)
        }
        socket.on("chatMessage") { [weak self] data, _ in
            guard let self, let payload = data.first as? [String: Any],
                  let message = payload["message"] as? String,
                  let userId = payload["userId"] as? String else { return }
            self.delegate?.signaling(self, didReceiveChat: message, from: userId)
        }
        socket.on("drawing") { [weak self] data, _ in
            guard let self, let payload = data.first as? [String: Any],
                  let drawing = payload["drawing"] as? [String: Any],
                  let userId = payload["userId"] as? String else { return }
            self.delegate?.signaling(self, didReceiveDrawing: drawing, from: userId)
        }
    }
}
