import SwiftUI
import Combine
import AVFoundation

@MainActor
final class QuranReaderViewModel: ObservableObject {
    @Published var selectedSurah: Surah?
    @Published var currentAyahIndex: Int = 0
    @Published var isRecording: Bool = false
    @Published var recitationText: String = ""
    @Published var tajweedMistakes: [TajweedMistake] = []
    @Published var isPlayingReference: Bool = false
    @Published var isPlayingUser: Bool = false
    @Published var bookmarkedAyahs: Set<Int> = []

    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private let speechRecognizer = SpeechRecognizer()
    private var cancellables = Set<AnyCancellable>()

    func loadSurah(_ surah: Surah) {
        selectedSurah = surah
        currentAyahIndex = 0
        tajweedMistakes = []
        bookmarkedAyahs = CoreDataManager.shared.getBookmarkedAyahs()
    }

    func startRecording() {
        guard selectedSurah != nil else { return }
        isRecording = true
        recitationText = ""
        tajweedMistakes = []

        let audioSession = AVAudioSession.sharedInstance()
        try? audioSession.setCategory(.playAndRecord, mode: .default)
        try? audioSession.setActive(true)

        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let audioFilename = documentsPath.appendingPathComponent("recitation-\(Date().timeIntervalSince1970).m4a")
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 12000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        audioRecorder = try? AVAudioRecorder(url: audioFilename, settings: settings)
        audioRecorder?.record()

        speechRecognizer.startTranscribing { [weak self] text in
            Task { @MainActor in
                self?.recitationText = text
                self?.detectTajweedMistakes(text: text)
            }
        }
    }

    func stopRecording() {
        isRecording = false
        audioRecorder?.stop()
        speechRecognizer.stopTranscribing()
    }

    func playReferenceRecitation() {
        guard let surah = selectedSurah, currentAyahIndex < surah.ayahs.count else { return }
        playAudio(from: surah.ayahs[currentAyahIndex].referenceAudioURL)
    }

    func playUserRecitation() {
        guard let surah = selectedSurah, currentAyahIndex < surah.ayahs.count else { return }
        playAudio(from: surah.ayahs[currentAyahIndex].userRecordingURL)
    }

    private func playAudio(from url: URL?) {
        guard let url = url else { return }
        audioPlayer = try? AVAudioPlayer(contentsOf: url)
        audioPlayer?.play()
    }

    private func detectTajweedMistakes(text: String) {
        guard let surah = selectedSurah, currentAyahIndex < surah.ayahs.count else { return }
        let ayah = surah.ayahs[currentAyahIndex]

        // Fast on-device heuristic for immediate feedback...
        let localMistakes = TajweedEngine.detectLocalMistakes(text: text, ayah: ayah)
        tajweedMistakes = localMistakes

        // ...then authoritative AI analysis from the backend.
        APIService.shared.analyzeTajweed(
            surahId: surah.id,
            ayahNumber: ayah.number,
            transcript: text
        ) { [weak self] result in
            Task { @MainActor in
                switch result {
                case .success(let backendMistakes):
                    self?.tajweedMistakes = localMistakes + backendMistakes
                case .failure(let error):
                    print("Error detecting Tajweed mistakes: \(error)")
                }
            }
        }
    }

    func toggleBookmark(for ayahId: Int) {
        if bookmarkedAyahs.contains(ayahId) {
            bookmarkedAyahs.remove(ayahId)
        } else {
            bookmarkedAyahs.insert(ayahId)
        }
        CoreDataManager.shared.toggleBookmark(ayahId: ayahId)
    }
}
