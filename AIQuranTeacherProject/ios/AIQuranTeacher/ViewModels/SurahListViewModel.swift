import Foundation

@MainActor
final class SurahListViewModel: ObservableObject {
    @Published var surahs: [Surah] = []
    @Published var isLoading = false

    /// Loads the surah list from the backend (`GET /api/quran/surahs`).
    func load() async {
        // TODO: fetch from APIService. Scaffold uses an empty list.
        isLoading = false
    }
}
