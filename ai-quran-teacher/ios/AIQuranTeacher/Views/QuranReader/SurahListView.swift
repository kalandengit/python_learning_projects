import SwiftUI

struct SurahListView: View {
    @StateObject private var viewModel = SurahListViewModel()

    var body: some View {
        NavigationStack {
            List(viewModel.filteredSurahs) { surah in
                NavigationLink(value: surah) {
                    HStack(spacing: 12) {
                        Text("\(surah.id)")
                            .font(.caption.bold())
                            .frame(width: 34, height: 34)
                            .background(Circle().fill(Color.accentColor.opacity(0.15)))
                        VStack(alignment: .leading, spacing: 2) {
                            Text(surah.englishName).font(.headline)
                            Text("\(surah.englishMeaning) • \(surah.numberOfAyahs) ayahs")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text(surah.name)
                            .font(.title3)
                            .environment(\.layoutDirection, .rightToLeft)
                    }
                }
            }
            .navigationTitle("Surahs")
            .searchable(text: $viewModel.searchText, prompt: "Search surahs")
            .navigationDestination(for: Surah.self) { surah in
                QuranReaderView(viewModel: QuranReaderViewModel(surah: surah))
            }
            .overlay {
                if viewModel.isLoading {
                    ProgressView()
                } else if let error = viewModel.errorMessage {
                    ContentUnavailableView("Could not load Quran data",
                                           systemImage: "book.closed",
                                           description: Text(error))
                }
            }
            .task { await viewModel.load() }
        }
    }
}

#Preview {
    SurahListView()
}
