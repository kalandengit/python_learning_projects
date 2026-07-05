import Foundation

/// Loads the list of surahs, preferring the bundled offline copy.
@MainActor
final class SurahListViewModel: ObservableObject {
    @Published var surahs: [Surah] = []
    @Published var searchText = ""
    @Published var isLoading = false
    @Published var errorMessage: String?

    var filteredSurahs: [Surah] {
        guard !searchText.isEmpty else { return surahs }
        return surahs.filter {
            $0.englishName.localizedCaseInsensitiveContains(searchText)
                || $0.name.contains(searchText)
                || String($0.id) == searchText
        }
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        // Ship `quran.json` in the bundle so the reader works fully offline.
        if let url = Bundle.main.url(forResource: "quran", withExtension: "json") {
            do {
                let data = try Data(contentsOf: url)
                surahs = try JSONDecoder().decode([Surah].self, from: data)
                return
            } catch {
                errorMessage = "Failed to load bundled Quran data: \(error.localizedDescription)"
            }
        } else {
            errorMessage = "quran.json is missing from the app bundle."
        }
    }
}
