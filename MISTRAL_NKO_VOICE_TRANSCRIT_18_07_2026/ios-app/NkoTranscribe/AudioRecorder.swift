import AVFoundation
import Foundation

/// Records 16 kHz mono AAC to a temporary file that is deleted after upload.
final class AudioRecorder: NSObject, ObservableObject {

    @Published private(set) var isRecording = false
    private var recorder: AVAudioRecorder?
    private var fileURL: URL?

    func requestPermission() async -> Bool {
        await AVAudioApplication.requestRecordPermission()
    }

    func start() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement)
        try session.setActive(true)

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("nko-\(UUID().uuidString).m4a")
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatMPEG4AAC,
            AVSampleRateKey: 16_000,
            AVNumberOfChannelsKey: 1,
            AVEncoderBitRateKey: 48_000,
        ]
        let audioRecorder = try AVAudioRecorder(url: url, settings: settings)
        audioRecorder.record()
        recorder = audioRecorder
        fileURL = url
        isRecording = true
    }

    /// Stops and returns the recorded file URL (caller deletes after upload).
    func stop() -> URL? {
        recorder?.stop()
        recorder = nil
        isRecording = false
        try? AVAudioSession.sharedInstance().setActive(false)
        return fileURL
    }

    func discard(_ url: URL?) {
        if let url { try? FileManager.default.removeItem(at: url) }
    }
}
