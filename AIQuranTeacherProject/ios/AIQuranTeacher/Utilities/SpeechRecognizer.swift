import Foundation
import Speech
import AVFoundation

/// On-device Arabic speech-to-text using `SFSpeechRecognizer`.
/// Scaffold: wire up real recognition and request authorization before use.
final class SpeechRecognizer {
    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "ar-SA"))
    private let audioEngine = AVAudioEngine()
    private var request: SFSpeechAudioBufferRecognitionRequest?
    private var task: SFSpeechRecognitionTask?

    /// Request the permissions required for recognition.
    static func requestAuthorization(_ completion: @escaping (Bool) -> Void) {
        SFSpeechRecognizer.requestAuthorization { status in
            DispatchQueue.main.async { completion(status == .authorized) }
        }
    }

    func startTranscribing(onResult: @escaping (String) -> Void) {
        // TODO: install a tap on the audio engine input node, feed buffers to
        // `request`, and forward partial transcripts to `onResult`.
    }

    func stopTranscribing() {
        task?.cancel()
        audioEngine.stop()
        request = nil
        task = nil
    }
}
