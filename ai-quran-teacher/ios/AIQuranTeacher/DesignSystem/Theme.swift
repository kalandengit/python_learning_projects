import SwiftUI

/// The AI Quran Teacher design system.
///
/// Design language: a calm, modern "Dark Mode 2.0" surface with soft gradients,
/// an emerald/gold Islamic palette, generous rounding, and tactile depth. Every
/// token adapts to light and dark automatically. Keep colors and spacing on
/// these tokens rather than hard-coding values in views.
enum Theme {
    // MARK: - Brand palette

    /// Emerald — primary brand color, evokes the traditional green of Islam.
    static let emerald = Color(hex: 0x1FA97A)
    static let emeraldDeep = Color(hex: 0x0E6E52)
    /// Warm gold — accents, achievements, certificates.
    static let gold = Color(hex: 0xE9B949)
    /// Lapis — secondary accent for links and highlights.
    static let lapis = Color(hex: 0x3A6EA5)
    static let coral = Color(hex: 0xE8734A)

    // MARK: - Semantic surfaces (adaptive)

    static let background = Color("Background", bundle: nil)
        .fallback(light: 0xF6F4EF, dark: 0x0E1512)
    static let surface = Color("Surface", bundle: nil)
        .fallback(light: 0xFFFFFF, dark: 0x15201B)
    static let surfaceElevated = Color("SurfaceElevated", bundle: nil)
        .fallback(light: 0xFFFFFF, dark: 0x1D2A23)
    static let textPrimary = Color.primary
    static let textSecondary = Color.secondary

    // MARK: - Signature gradients

    /// Hero gradient used on headers, the record button, and primary CTAs.
    static let heroGradient = LinearGradient(
        colors: [emerald, emeraldDeep],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    /// Gold gradient for achievement and certificate surfaces.
    static let goldGradient = LinearGradient(
        colors: [gold, coral],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    /// Subtle ambient background wash (Dark Mode 2.0 depth).
    static let ambientGradient = LinearGradient(
        colors: [emerald.opacity(0.10), lapis.opacity(0.08)],
        startPoint: .top,
        endPoint: .bottom
    )

    // MARK: - Shape & motion

    static let cornerRadius: CGFloat = 20
    static let cornerRadiusSmall: CGFloat = 12
    static let spacing: CGFloat = 16
    static let springy = Animation.spring(response: 0.4, dampingFraction: 0.75)
}

// MARK: - Color helpers

extension Color {
    init(hex: UInt, alpha: Double = 1) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255,
            opacity: alpha
        )
    }

    /// Returns a color that resolves to different hex values in light/dark mode.
    /// Falls back to programmatic colors so the app works without asset catalog
    /// color sets defined.
    func fallback(light: UInt, dark: UInt) -> Color {
        Color(UIColor { traits in
            UIColor(Color(hex: traits.userInterfaceStyle == .dark ? dark : light))
        })
    }
}
