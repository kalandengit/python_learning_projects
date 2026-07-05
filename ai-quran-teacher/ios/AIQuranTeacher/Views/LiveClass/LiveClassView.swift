import SwiftUI

struct LiveClassView: View {
    @StateObject var viewModel: LiveClassViewModel
    @State private var selectedTab: Tab = .video

    enum Tab: String, CaseIterable {
        case video = "Video"
        case whiteboard = "Whiteboard"
        case chat = "Chat"
    }

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Circle()
                    .fill(viewModel.connectionState == "Connected" ? .green : .orange)
                    .frame(width: 10, height: 10)
                Text(viewModel.connectionState)
                    .font(.caption)
                Spacer()
                Text("\(viewModel.participants.count + 1) in class")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal)
            .padding(.vertical, 8)

            Picker("Section", selection: $selectedTab) {
                ForEach(Tab.allCases, id: \.self) { tab in
                    Text(tab.rawValue).tag(tab)
                }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal)

            switch selectedTab {
            case .video:
                VideoCallView(viewModel: viewModel)
            case .whiteboard:
                WhiteboardView(viewModel: viewModel)
            case .chat:
                ChatView(viewModel: viewModel)
            }
        }
        .navigationTitle("Live Class")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { viewModel.join() }
        .onDisappear { viewModel.leave() }
    }
}
