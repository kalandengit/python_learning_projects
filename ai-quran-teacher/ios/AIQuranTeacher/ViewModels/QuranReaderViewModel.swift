import Foundation

/// Drives the Quran reader: recitation capture, Tajweed feedback, bookmarks.
@MainActor
final class QuranReaderViewModel: ObservableObject {
    @Published var surah: Surah
    @Published var currentAyahIndex = 0
    @Published var detectionResult: TajweedDetectionResult?
    @Published var isAnalyzing = false
    @Published var errorMessage: String?
    @Published var bookmarkedAyahIds: Set<Int> = []

    let speechRecognizer = SpeechRecognizer()

    private let api: APIService
    private let coreData: CoreDataManager
    private let userId: String?

    var currentAyah: Ayah? {
        guard surah.ayahs.indices.contains(currentAyahIndex) else { return nil }
        return surah.ayahs[currentAyahIndex]
    }

    init(
        surah: Surah,
        userId: String? = nil,
        api: APIService = .shared,
        coreData: CoreDataManager = .shared
    ) {
        self.surah = surah
        self.userId = userId
        self.api = api
        self.coreData = coreData
        bookmarkedAyahIds = coreData.bookmarkedAyahIds()
    }

    func startRecitation() async {
        guard await speechRecognizer.requestAuthorization() else {
            errorMessage = "Microphone or speech recognition permission was denied."
            return
        }
        detectionResult = nil
        do {
            try speechRecognizer.start()
        } catch {
            errorMessage = "Could not start recording: \(error.localizedDescription)"
        }
    }

    /// Stops recording and sends the transcript for Tajweed analysis.
    func finishRecitation() async {
        speechRecognizer.stop()
        guard let ayah = currentAyah else { return }
        let transcript = speechRecognizer.transcript
        guard !transcript.isEmpty else { return }

        isAnalyzing = true
        defer { isAnalyzing = false }
        do {
            let result = try await api.detectTajweed(
                text: transcript,
                ayahId: ayah.id,
                expectedText: ayah.text,
                userId: userId
            )
            detectionResult = result
            coreData.recordSession(ayahId: ayah.id, accuracy: result.accuracy, mistakes: result.mistakes)
            if let userId {
                _ = try? await api.recordActivity(userId: userId)
            }
        } catch {
            // Offline fallback: run the on-device engine instead.
            let mistakes = TajweedEngine.compare(recited: transcript, expected: ayah.text)
            let accuracy = ayah.text.isEmpty ? 1 : 1 - Double(mistakes.count) /
                Double(max(1, ayah.text.split(separator: " ").count))
            detectionResult = TajweedDetectionResult(
                ayahId: ayah.id,
                accuracy: max(0, accuracy),
                mistakes: mistakes,
                rulesToObserve: TajweedEngine.analyze(ayah.text)
            )
            coreData.recordSession(ayahId: ayah.id, accuracy: max(0, accuracy), mistakes: mistakes)
        }
    }

    func toggleBookmark(for ayah: Ayah) {
        coreData.toggleBookmark(ayahId: ayah.id)
        bookmarkedAyahIds = coreData.bookmarkedAyahIds()
    }

    func goToNextAyah() {
        guard currentAyahIndex < surah.ayahs.count - 1 else { return }
        currentAyahIndex += 1
        detectionResult = nil
    }

    func goToPreviousAyah() {
        guard currentAyahIndex > 0 else { return }
        currentAyahIndex -= 1
        detectionResult = nil
    }
}
