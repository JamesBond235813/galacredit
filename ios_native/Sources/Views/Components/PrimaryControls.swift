import SwiftUI

struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 16, weight: .semibold))
            .foregroundStyle(Color.white)
            .frame(maxWidth: .infinity)
            .frame(height: 54)
            .background(
                LinearGradient(
                    colors: [AppTheme.primary, AppTheme.secondary],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                in: Capsule(style: .continuous)
            )
            .overlay(
                Capsule(style: .continuous)
                    .stroke(Color.white.opacity(0.35), lineWidth: 1)
            )
            .shadow(color: AppTheme.primary.opacity(0.28), radius: 22, x: 0, y: 10)
            .scaleEffect(configuration.isPressed ? 0.985 : 1.0)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    var danger: Bool = false

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .semibold))
            .foregroundStyle(danger ? AppTheme.danger : AppTheme.text)
            .padding(.horizontal, 16)
            .frame(height: 42)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(danger ? Color.white.opacity(configuration.isPressed ? 0.95 : 0.88) : Color(red: 0.96, green: 0.97, blue: 0.99).opacity(configuration.isPressed ? 0.98 : 0.94))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .stroke(danger ? AppTheme.danger.opacity(0.34) : AppTheme.stroke, lineWidth: 1)
            )
    }
}

struct SearchField: View {
    @Binding var text: String
    let prompt: String

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(AppTheme.muted)
            TextField(prompt, text: $text)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
        }
        .padding(.horizontal, 16)
        .frame(height: 48)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.white.opacity(0.78))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(Color.white.opacity(0.8), lineWidth: 1)
        )
    }
}
