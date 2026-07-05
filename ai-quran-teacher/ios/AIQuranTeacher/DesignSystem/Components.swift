import SwiftUI

/// A rounded, softly-shadowed content card — the primary container in the app.
struct GlassCard<Content: View>: View {
    var padding: CGFloat = Theme.spacing
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(padding)
            .background(
                RoundedRectangle(cornerRadius: Theme.cornerRadius, style: .continuous)
                    .fill(Theme.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: Theme.cornerRadius, style: .continuous)
                    .strokeBorder(Theme.emerald.opacity(0.10), lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.08), radius: 14, x: 0, y: 8)
    }
}

/// Full-width gradient primary button.
struct PrimaryButton: View {
    let title: String
    var icon: String? = nil
    var gradient: LinearGradient = Theme.heroGradient
    var isLoading = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                if isLoading {
                    ProgressView().tint(.white)
                } else if let icon {
                    Image(systemName: icon)
                }
                Text(title).fontWeight(.semibold)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 15)
            .foregroundStyle(.white)
            .background(gradient)
            .clipShape(RoundedRectangle(cornerRadius: Theme.cornerRadius, style: .continuous))
            .shadow(color: Theme.emerald.opacity(0.35), radius: 12, x: 0, y: 6)
        }
        .disabled(isLoading)
    }
}

/// A large gradient header used at the top of feature screens.
struct FeatureHeader: View {
    let title: String
    let subtitle: String
    var systemImage: String

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: systemImage)
                .font(.system(size: 28, weight: .semibold))
                .foregroundStyle(.white)
                .frame(width: 56, height: 56)
                .background(Circle().fill(.white.opacity(0.18)))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.title2.bold()).foregroundStyle(.white)
                Text(subtitle).font(.subheadline).foregroundStyle(.white.opacity(0.85))
            }
            Spacer()
        }
        .padding(20)
        .frame(maxWidth: .infinity)
        .background(Theme.heroGradient)
        .clipShape(RoundedRectangle(cornerRadius: Theme.cornerRadius, style: .continuous))
    }
}

/// A pill-shaped tag/chip.
struct Chip: View {
    let text: String
    var tint: Color = Theme.emerald

    var body: some View {
        Text(text)
            .font(.caption.weight(.medium))
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(Capsule().fill(tint.opacity(0.15)))
            .foregroundStyle(tint)
    }
}

/// A circular progress ring (used for accuracy, exam timers, XP).
struct ProgressRing: View {
    let progress: Double // 0...1
    var lineWidth: CGFloat = 10
    var gradient: LinearGradient = Theme.heroGradient
    var label: String? = nil

    var body: some View {
        ZStack {
            Circle().stroke(Theme.emerald.opacity(0.12), lineWidth: lineWidth)
            Circle()
                .trim(from: 0, to: max(0.001, min(1, progress)))
                .stroke(gradient, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(Theme.springy, value: progress)
            if let label {
                Text(label).font(.headline.bold().monospacedDigit())
            }
        }
    }
}
