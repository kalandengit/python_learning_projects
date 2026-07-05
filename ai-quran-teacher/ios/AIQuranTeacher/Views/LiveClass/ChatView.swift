import SwiftUI

struct ChatView: View {
    @ObservedObject var viewModel: LiveClassViewModel
    @State private var draft = ""

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(viewModel.chatMessages) { message in
                            bubble(for: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.chatMessages.count) {
                    if let last = viewModel.chatMessages.last {
                        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                    }
                }
            }

            HStack {
                TextField("Message", text: $draft)
                    .textFieldStyle(.roundedBorder)
                Button {
                    viewModel.sendChat(draft)
                    draft = ""
                } label: {
                    Image(systemName: "paperplane.fill")
                }
                .disabled(draft.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            .padding()
            .background(.bar)
        }
    }

    private func bubble(for message: ChatMessage) -> some View {
        HStack {
            if message.isMine { Spacer() }
            VStack(alignment: message.isMine ? .trailing : .leading, spacing: 2) {
                if !message.isMine {
                    Text(message.userId)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                Text(message.text)
                    .padding(10)
                    .background(
                        RoundedRectangle(cornerRadius: 14)
                            .fill(message.isMine ? Color.accentColor : Color(.secondarySystemBackground))
                    )
                    .foregroundStyle(message.isMine ? .white : .primary)
            }
            if !message.isMine { Spacer() }
        }
    }
}
