import SwiftUI
import WebKit
import Security
import LocalAuthentication

struct ContentView: View {
    @AppStorage("serverURL") private var serverURL = ""
    @AppStorage("biometricLock") private var biometricLock = false
    @State private var draftURL = ""

    var body: some View {
        NavigationStack {
            if let url = validatedURL(serverURL) {
                SecureGate(enabled: biometricLock) {
                    NKoWebView(url: url)
                }
                .ignoresSafeArea(edges: .bottom)
                .navigationTitle("ߒߞߏ Voice")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    Button("Server") { serverURL = "" }
                    Toggle("Biometric lock", isOn: $biometricLock)
                }
            } else {
                Form {
                    Section {
                        Text("ߒߞߏ").font(.system(size: 56)).frame(maxWidth: .infinity)
                        Text("Choose your language, then record or import Manding speech.")
                    } header: { Text("N'Ko Voice Transcriptor") }
                    Section("Connect to your private backend") {
                        TextField("https://nko.example.com", text: $draftURL)
                            .textInputAutocapitalization(.never).keyboardType(.URL)
                        Button("Connect") {
                            if validatedURL(draftURL) != nil {
                                serverURL = draftURL.trimmingCharacters(in: .whitespacesAndNewlines)
                            }
                        }.disabled(validatedURL(draftURL) == nil)
                    }
                    Section("Privacy") {
                        Toggle("Require Face ID / Touch ID", isOn: $biometricLock)
                        Label("Session credentials are stored in Keychain.", systemImage: "lock.shield")
                        Text("Use the offline edition when audio must never leave the device.")
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

struct SecureGate<Content: View>: View {
    let enabled: Bool
    let content: Content
    @State private var unlocked = false

    init(enabled: Bool, @ViewBuilder content: () -> Content) {
        self.enabled = enabled
        self.content = content()
    }

    var body: some View {
        Group {
            if !enabled || unlocked { content }
            else { ProgressView("Unlocking…").task { await authenticate() } }
        }
    }

    private func authenticate() async {
        let context = LAContext()
        var error: NSError?
        guard context.canEvaluatePolicy(.deviceOwnerAuthentication, error: &error) else { return }
        unlocked = (try? await context.evaluatePolicy(
            .deviceOwnerAuthentication,
            localizedReason: "Protect your N'Ko transcripts"
        )) ?? false
    }
}

enum KeychainStore {
    private static let service = "net.nkotools.transcriptor"
    private static let account = "access-token"

    static func set(_ value: String) {
        clear()
        let data = Data(value.utf8)
        SecItemAdd([
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: service,
            kSecAttrAccount: account,
            kSecAttrAccessible: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
            kSecValueData: data
        ] as CFDictionary, nil)
    }

    static func get() -> String {
        var result: CFTypeRef?
        let status = SecItemCopyMatching([
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: service,
            kSecAttrAccount: account,
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne
        ] as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return "" }
        return String(data: data, encoding: .utf8) ?? ""
    }

    static func clear() {
        SecItemDelete([
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: service,
            kSecAttrAccount: account
        ] as CFDictionary)
    }
}

struct NKoWebView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        let controller = config.userContentController
        controller.add(context.coordinator, name: "secureSet")
        controller.add(context.coordinator, name: "secureClear")
        let tokenData = try? JSONSerialization.data(withJSONObject: KeychainStore.get())
        let tokenJSON = tokenData.flatMap { String(data: $0, encoding: .utf8) } ?? "\"\""
        controller.addUserScript(WKUserScript(
            source: """
            window.NkoSecureStore = {
              _token: \(tokenJSON),
              getToken() { return this._token || ''; },
              setToken(value) { this._token = value; window.webkit.messageHandlers.secureSet.postMessage(value); },
              clear() { this._token = ''; window.webkit.messageHandlers.secureClear.postMessage(''); }
            };
            """,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
        let view = WKWebView(frame: .zero, configuration: config)
        view.navigationDelegate = context.coordinator
        view.uiDelegate = context.coordinator
        return view
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        if webView.url != url { webView.load(URLRequest(url: url)) }
    }

    func makeCoordinator() -> Coordinator { Coordinator(trustedURL: url) }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
        let trustedURL: URL
        init(trustedURL: URL) { self.trustedURL = trustedURL }

        func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
            if message.name == "secureSet", let token = message.body as? String { KeychainStore.set(token) }
            if message.name == "secureClear" { KeychainStore.clear() }
        }

        func webView(
            _ webView: WKWebView,
            decidePolicyFor navigationAction: WKNavigationAction,
            decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
        ) {
            guard let target = navigationAction.request.url else { decisionHandler(.cancel); return }
            if target.scheme == trustedURL.scheme && target.host == trustedURL.host && target.port == trustedURL.port {
                decisionHandler(.allow)
            } else {
                if let scheme = target.scheme, ["http", "https"].contains(scheme) {
                    UIApplication.shared.open(target)
                }
                decisionHandler(.cancel)
            }
        }

        func webView(
            _ webView: WKWebView,
            requestMediaCapturePermissionFor origin: WKSecurityOrigin,
            initiatedByFrame frame: WKFrameInfo,
            type: WKMediaCaptureType,
            decisionHandler: @escaping (WKPermissionDecision) -> Void
        ) {
            let trustedPort = trustedURL.port ?? (trustedURL.scheme == "https" ? 443 : 80)
            let trusted = origin.host == trustedURL.host
                && origin.protocol == trustedURL.scheme
                && origin.port == trustedPort
            decisionHandler(trusted && type == .microphone ? .grant : .deny)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            webView.loadHTMLString("<meta name='viewport' content='width=device-width'><h2>Server unavailable</h2><p>Check the address and connection.</p>", baseURL: nil)
        }
    }
}
