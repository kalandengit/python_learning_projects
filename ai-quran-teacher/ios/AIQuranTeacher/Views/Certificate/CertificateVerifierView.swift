import SwiftUI

/// Public certificate verifier — an employer or institute enters a code to
/// confirm a student's Tajweed certification.
struct CertificateVerifierView: View {
    @State private var code = ""
    @State private var result: CertificateVerification?
    @State private var isChecking = false
    @State private var errorMessage: String?

    private let api = APIService.shared

    var body: some View {
        ZStack {
            Theme.background.ignoresSafeArea()
            Theme.ambientGradient.ignoresSafeArea()

            ScrollView {
                VStack(spacing: Theme.spacing) {
                    FeatureHeader(
                        title: "Verify a Certificate",
                        subtitle: "Confirm a Tajweed credential by its code",
                        systemImage: "checkmark.seal.fill"
                    )

                    GlassCard {
                        VStack(spacing: 12) {
                            TextField("Verification code", text: $code)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .font(.system(.body, design: .monospaced))
                                .padding(12)
                                .background(RoundedRectangle(cornerRadius: Theme.cornerRadiusSmall).fill(Theme.background))
                            PrimaryButton(title: "Verify", isLoading: isChecking) {
                                Task { await verify() }
                            }
                            .disabled(code.trimmingCharacters(in: .whitespaces).isEmpty)
                        }
                    }

                    if let result {
                        resultCard(result)
                    }
                }
                .padding()
            }
        }
        .navigationTitle("Verify")
        .alert("Error", isPresented: .constant(errorMessage != nil)) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
    }

    @ViewBuilder
    private func resultCard(_ result: CertificateVerification) -> some View {
        GlassCard {
            if result.valid {
                VStack(spacing: 8) {
                    Image(systemName: "checkmark.seal.fill")
                        .font(.system(size: 40)).foregroundStyle(Theme.emerald)
                    Text("Valid certificate").font(.headline)
                    if let level = result.level {
                        Chip(text: "\(level.title) Tajweed", tint: Theme.emerald)
                    }
                    if let issued = result.issuedAt {
                        Text("Issued \(issued.formatted(date: .abbreviated, time: .omitted))")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
                .frame(maxWidth: .infinity)
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "xmark.seal.fill")
                        .font(.system(size: 40)).foregroundStyle(Theme.coral)
                    Text("No matching certificate").font(.headline)
                    Text("Check the code and try again.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
            }
        }
    }

    private func verify() async {
        isChecking = true
        errorMessage = nil
        defer { isChecking = false }
        do {
            result = try await api.verifyCertificate(
                code: code.trimmingCharacters(in: .whitespaces)
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
