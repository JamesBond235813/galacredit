import SwiftUI

enum AppTheme {
    static let pageBackground = LinearGradient(
        colors: [
            Color(red: 1.0, green: 0.98, blue: 0.95),
            Color(red: 0.965, green: 0.97, blue: 0.975)
        ],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let cardBackground = Color.white.opacity(0.92)
    static let secondaryCardBackground = Color(red: 0.93, green: 0.95, blue: 0.98)
    static let stroke = Color(red: 0.82, green: 0.86, blue: 0.92).opacity(0.72)
    static let text = Color(red: 0.12, green: 0.16, blue: 0.24)
    static let muted = Color(red: 0.45, green: 0.5, blue: 0.6)
    // 与 UniApp、Android 原生登录壳和 AppIcon 统一 GalaCredit 橙色品牌，避免原生工作区出现旧蓝色主题。
    static let primary = Color(red: 234 / 255, green: 149 / 255, blue: 24 / 255)
    static let secondary = Color(red: 247 / 255, green: 190 / 255, blue: 103 / 255)
    static let positive = Color(red: 0.2, green: 0.65, blue: 0.48)
    static let danger = Color(red: 0.88, green: 0.31, blue: 0.41)
    static let warning = Color(red: 0.96, green: 0.65, blue: 0.27)
}

/// GalaCredit 统一品牌标记，供启动页和登录页复用，避免使用未授权的系统图标替代品牌 Logo。
struct GalaCreditMark: View {
    var body: some View {
        Canvas { context, size in
            let card = CGRect(x: 3, y: size.height * 0.18, width: size.width - 6, height: size.height * 0.64)
            context.fill(Path(roundedRect: card, cornerRadius: size.width * 0.12), with: .color(AppTheme.primary))
            context.fill(Path(CGRect(x: 3, y: size.height * 0.42, width: size.width - 6, height: size.height * 0.08)), with: .color(.white.opacity(0.96)))
            context.fill(Path(CGRect(x: size.width * 0.54, y: size.height * 0.62, width: size.width * 0.23, height: size.height * 0.10)), with: .color(.white))
        }
        .accessibilityLabel("GalaCredit")
    }
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
