import SwiftUI

struct QuranReaderView: View {
    @StateObject private var viewModel = QuranReaderViewModel()
    @State private var showSurahList = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                headerView
                ScrollView {
                    VStack(spacing: 20) {
                        if let surah = viewModel.selectedSurah {
                            ForEach(surah.ayahs.indices, id: \.self) { index in
                                AyahView(
                                    ayah: surah.ayahs[index],
                                    isSelected: index == viewModel.currentAyahIndex,
                                    mistakes: viewModel.tajweedMistakes.filter {
                                        $0.ayahId == surah.ayahs[index].id
                                    },
                                    isBookmarked: viewModel.bookmarkedAyahs.contains(surah.ayahs[index].id)
                                )
                                .onTapGesture {
                                    viewModel.currentAyahIndex = index
                                }
                                .id(index)
                            }
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 10)
                }
                RecitationControlsView(
                    isRecording: viewModel.isRecording,
                    onRecord: {
                        if viewModel.isRecording {
                            viewModel.stopRecording()
                        } else {
                            viewModel.startRecording()
                        }
                    },
                    onPlayReference: viewModel.playReferenceRecitation,
                    onPlayUser: viewModel.playUserRecitation
                )
                .padding()
            }
            .navigationTitle(viewModel.selectedSurah?.name ?? "Quran Reader")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(action: { showSurahList = true }) {
                        Image(systemName: "list.bullet")
                    }
                }
            }
            .sheet(isPresented: $showSurahList) {
                SurahListView(selectedSurah: $viewModel.selectedSurah)
            }
            .onAppear {
                if let lastSurah = CoreDataManager.shared.getLastReadSurah() {
                    viewModel.loadSurah(lastSurah)
                }
            }
        }
    }

    private var headerView: some View {
        VStack(alignment: .leading, spacing: 8) {
            if let surah = viewModel.selectedSurah {
                Text(surah.arabicName)
                    .font(.system(size: 28, weight: .bold))
                    .foregroundColor(.primary)
                    .padding(.horizontal)
                Text(surah.name)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.secondary)
                    .padding(.horizontal)
                Divider()
            }
        }
        .background(Color(.systemBackground))
    }
}
