import SwiftUI

struct RootView: View {
    @EnvironmentObject private var sessionStore: SessionStore

    var body: some View {
        ZStack {
            AppTheme.pageBackground
                .ignoresSafeArea()

            if sessionStore.isRestoring {
                SecureLaunchView()
            } else if sessionStore.isLoggedIn {
                H5HomeView(sessionStore: sessionStore)
            } else {
                LoginView()
            }
        }
        .task {
            await sessionStore.restoreSession()
        }
        .animation(.spring(duration: 0.35), value: sessionStore.isLoggedIn)
    }
}

private struct SecureLaunchView: View {
    var body: some View {
        VStack(spacing: 16) {
            GalaCreditMark()
                .frame(width: 64, height: 64)
            Text("GalaCredit")
                .font(.system(size: 28, weight: .bold, design: .rounded))
            Text("Loading securely…")
                .font(.subheadline)
                .foregroundStyle(AppTheme.muted)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppTheme.pageBackground.ignoresSafeArea())
    }
}
