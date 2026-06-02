import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @State private var username = ""
    @State private var password = ""

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 20) {
                VStack(spacing: 10) {
                    WalletAppIconMark()
                        .frame(width: 70, height: 70)

                    Text("小荷包移动工作台")
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundStyle(AppTheme.text)
                }
                .padding(.top, 42)

                VStack(alignment: .leading, spacing: 14) {
                    field("账号", text: $username)
                    secureField("密码", text: $password)
                    if !sessionStore.errorMessage.isEmpty {
                        Text(sessionStore.errorMessage)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundStyle(AppTheme.danger)
                    }
                    Button {
                        Task {
                            await sessionStore.login(username: username, password: password)
                        }
                    } label: {
                        if sessionStore.isLoading {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Text("登录")
                        }
                    }
                    .buttonStyle(LoginPrimaryButtonStyle())
                    .disabled(username.isEmpty || password.isEmpty || sessionStore.isLoading)
                }
                .padding(14)
                .background(
                    RoundedRectangle(cornerRadius: 26, style: .continuous)
                        .fill(Color.white.opacity(0.78))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 26, style: .continuous)
                        .stroke(Color.white.opacity(0.88), lineWidth: 1)
                )
                .shadow(color: Color.black.opacity(0.06), radius: 22, x: 0, y: 12)
                .padding(.top, 8)
            }
            .padding(.horizontal, 22)
            .padding(.bottom, 32)
        }
    }

    private func field(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            TextField(title, text: text)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
                .foregroundStyle(AppTheme.text)
                .tint(AppTheme.primary)
                .padding(.horizontal, 16)
                .frame(height: 46)
                .background(Color.white.opacity(0.92), in: RoundedRectangle(cornerRadius: 23, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 23, style: .continuous)
                        .stroke(Color.white.opacity(0.92), lineWidth: 1)
                )
        }
    }

    private func secureField(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            SecureField(title, text: text)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
                .foregroundStyle(AppTheme.text)
                .tint(AppTheme.primary)
                .padding(.horizontal, 16)
                .frame(height: 46)
                .background(Color.white.opacity(0.92), in: RoundedRectangle(cornerRadius: 23, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 23, style: .continuous)
                        .stroke(Color.white.opacity(0.92), lineWidth: 1)
                )
        }
    }
}

private struct LoginPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 15, weight: .semibold))
            .foregroundStyle(Color.white)
            .frame(maxWidth: .infinity)
            .frame(height: 48)
            .background(
                LinearGradient(
                    colors: [AppTheme.primary, AppTheme.secondary],
                    startPoint: .leading,
                    endPoint: .trailing
                ),
                in: Capsule(style: .continuous)
            )
            .overlay(
                Capsule(style: .continuous)
                    .stroke(Color.white.opacity(0.32), lineWidth: 1)
            )
            .shadow(color: AppTheme.primary.opacity(0.18), radius: 16, x: 0, y: 8)
            .scaleEffect(configuration.isPressed ? 0.985 : 1.0)
    }
}

private struct WalletAppIconMark: View {
    private let orange = Color(red: 245 / 255, green: 167 / 255, blue: 61 / 255)
    private let cream = Color(red: 253 / 255, green: 234 / 255, blue: 202 / 255)

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(orange)

            GeometryReader { proxy in
                let width = proxy.size.width
                let height = proxy.size.height
                ZStack {
                    Path { path in
                        path.move(to: CGPoint(x: width * 0.30, y: height * 0.38))
                        path.addLine(to: CGPoint(x: width * 0.54, y: height * 0.20))
                        path.addQuadCurve(
                            to: CGPoint(x: width * 0.71, y: height * 0.36),
                            control: CGPoint(x: width * 0.66, y: height * 0.17)
                        )
                        path.addLine(to: CGPoint(x: width * 0.35, y: height * 0.38))
                        path.closeSubpath()
                    }
                    .fill(cream.opacity(0.72))

                    RoundedRectangle(cornerRadius: width * 0.10, style: .continuous)
                        .fill(Color.white)
                        .frame(width: width * 0.60, height: height * 0.42)
                        .offset(x: -width * 0.04, y: height * 0.12)

                    RoundedRectangle(cornerRadius: width * 0.08, style: .continuous)
                        .fill(orange)
                        .frame(width: width * 0.28, height: height * 0.14)
                        .offset(x: width * 0.24, y: height * 0.14)

                    Circle()
                        .fill(Color.white)
                        .frame(width: width * 0.09, height: height * 0.09)
                        .offset(x: width * 0.17, y: height * 0.14)
                }
            }
            .padding(6)
        }
        .shadow(color: orange.opacity(0.28), radius: 26, x: 0, y: 14)
    }
}
