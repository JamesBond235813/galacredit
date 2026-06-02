import SwiftUI

enum AppTheme {
    static let pageBackground = LinearGradient(
        colors: [
            Color(red: 0.925, green: 0.94, blue: 0.965),
            Color(red: 0.955, green: 0.965, blue: 0.985)
        ],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let cardBackground = Color.white.opacity(0.92)
    static let secondaryCardBackground = Color(red: 0.93, green: 0.95, blue: 0.98)
    static let stroke = Color(red: 0.82, green: 0.86, blue: 0.92).opacity(0.72)
    static let text = Color(red: 0.12, green: 0.16, blue: 0.24)
    static let muted = Color(red: 0.45, green: 0.5, blue: 0.6)
    static let primary = Color(red: 0.36, green: 0.46, blue: 0.92)
    static let secondary = Color(red: 0.56, green: 0.68, blue: 0.98)
    static let positive = Color(red: 0.2, green: 0.65, blue: 0.48)
    static let danger = Color(red: 0.88, green: 0.31, blue: 0.41)
    static let warning = Color(red: 0.96, green: 0.65, blue: 0.27)
}

struct GlassCardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 28, style: .continuous)
                    .fill(AppTheme.cardBackground)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 28, style: .continuous)
                    .stroke(AppTheme.stroke, lineWidth: 1)
            )
            .compositingGroup()
            .shadow(color: Color.white.opacity(0.65), radius: 12, x: -6, y: -6)
            .shadow(color: Color.black.opacity(0.075), radius: 20, x: 0, y: 12)
    }
}

extension View {
    func glassCard() -> some View {
        modifier(GlassCardModifier())
    }
}
