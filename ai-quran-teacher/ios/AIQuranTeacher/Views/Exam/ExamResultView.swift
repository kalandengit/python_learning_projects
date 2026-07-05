import SwiftUI

struct ExamResultView: View {
    let result: ExamResult
    let onDone: () -> Void

    var body: some View {
        ScrollView {
            VStack(spacing: Theme.spacing) {
                ProgressRing(
                    progress: Double(result.percent) / 100,
                    lineWidth: 14,
                    gradient: result.passed ? Theme.heroGradient : Theme.goldGradient,
                    label: "\(result.percent)%"
                )
                .frame(width: 150, height: 150)
                .padding(.top)

                Text(result.passed ? "Passed! 🎉" : "Keep practicing")
                    .font(.title.bold())
                Text("\(result.score) of \(result.total) correct · +\(result.xpEarned) XP")
                    .foregroundStyle(.secondary)

                if let certificate = result.certificate {
                    CertificateCard(certificate: certificate)
                } else if result.expired {
                    Chip(text: "Time expired", tint: Theme.coral)
                }

                // Review.
                GlassCard {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Review").font(.headline)
                        ForEach(result.review) { item in
                            HStack(alignment: .top, spacing: 10) {
                                Image(systemName: item.correct ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundStyle(item.correct ? Theme.emerald : Theme.coral)
                                Text(item.explanation).font(.subheadline).foregroundStyle(.secondary)
                            }
                        }
                    }
                }

                PrimaryButton(title: "Done", gradient: Theme.heroGradient, action: onDone)
            }
            .padding()
        }
    }
}

/// A gold, credential-style card for an earned certificate.
struct CertificateCard: View {
    let certificate: Certificate

    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: "rosette").font(.system(size: 40)).foregroundStyle(.white)
            Text("Certified · \(certificate.level.title)")
                .font(.headline).foregroundStyle(.white)
            Text("Tajweed Proficiency")
                .font(.subheadline).foregroundStyle(.white.opacity(0.9))
            Divider().background(.white.opacity(0.4)).padding(.vertical, 4)
            Text("Verification code")
                .font(.caption2).foregroundStyle(.white.opacity(0.8))
            Text(certificate.verificationCode)
                .font(.system(.body, design: .monospaced).weight(.semibold))
                .foregroundStyle(.white)
                .textSelection(.enabled)
        }
        .frame(maxWidth: .infinity)
        .padding(24)
        .background(Theme.goldGradient)
        .clipShape(RoundedRectangle(cornerRadius: Theme.cornerRadius, style: .continuous))
        .shadow(color: Theme.gold.opacity(0.4), radius: 16, x: 0, y: 8)
    }
}
