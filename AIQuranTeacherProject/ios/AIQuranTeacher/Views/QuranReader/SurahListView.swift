import SwiftUI

/// Sheet listing available surahs, backed by `SurahListViewModel`.
struct SurahListView: View {
    @Binding var selectedSurah: Surah?
    @StateObject private var viewModel = SurahListViewModel()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List(viewModel.surahs) { surah in
                Button {
                    selectedSurah = surah
                    dismiss()
                } label: {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(surah.name).font(.headline)
                            Text("\(surah.ayahs.count) ayahs")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        Text(surah.arabicName).font(.title3)
                    }
                }
            }
            .navigationTitle("Surahs")
            .task { await viewModel.load() }
        }
    }
}
