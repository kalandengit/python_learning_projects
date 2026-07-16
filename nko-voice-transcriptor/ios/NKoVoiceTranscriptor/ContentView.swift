import SwiftUI
import WebKit

struct ContentView: View {
    @AppStorage("serverURL") private var serverURL = ""
    @State private var draftURL = ""

    var body: some View {
        NavigationStack {
            if let url = validatedURL(serverURL) {
                NKoWebView(url: url)
                    .ignoresSafeArea(edges: .bottom)
                    .navigationTitle("ߒߞߏ Voice")
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar { Button("Server") { serverURL = "" } }
            } else {
                Form {
                    Section {
                        Text("ߒߞߏ").font(.system(size: 56)).frame(maxWidth: .infinity)
                        Text("Choose your interface language in the workspace, then record or import Manding speech.")
                    } header: { Text("N'Ko Voice Transcriptor") }
                    Section("Connect to your private backend") {
                    TextField("https://nko.example.com", text: $draftURL)
                        .textInputAutocapitalization(.never).keyboardType(.URL)
                    Button("Connect") {
                        if validatedURL(draftURL) != nil { serverURL = draftURL.trimmingCharacters(in: .whitespacesAndNewlines) }
                    }.disabled(validatedURL(draftURL) == nil)
                    }
                    Section("Privacy") {
                        Label("The server address stays on this device.", systemImage: "lock.shield")
                        Text("Use the separate offline edition when audio must never leave the device.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }.navigationTitle("Welcome")
            }
        }
    }

    private func validatedURL(_ value: String) -> URL? {
        guard let url = URL(string: value.trimmingCharacters(in: .whitespacesAndNewlines)),
              ["http", "https"].contains(url.scheme?.lowercased()), url.host != nil else { return nil }
        return url
    }
}

struct NKoWebView: UIViewRepresentable {
    let url: URL
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        let view = WKWebView(frame: .zero, configuration: config)
        view.navigationDelegate = context.coordinator
        return view
    }
    func updateUIView(_ webView: WKWebView, context: Context) {
        if webView.url != url { webView.load(URLRequest(url: url)) }
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    final class Coordinator: NSObject, WKNavigationDelegate {
        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            webView.loadHTMLString("<meta name='viewport' content='width=device-width'><h2>Server unavailable</h2><p>Check the address and your connection, then use the Server button to try again.</p>", baseURL: nil)
        }
    }
}
