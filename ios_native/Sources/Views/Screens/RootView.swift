import SwiftUI

struct RootView: View {
    @EnvironmentObject private var sessionStore: SessionStore

    var body: some View {
        ZStack {
            AppTheme.pageBackground
                .ignoresSafeArea()

            if sessionStore.isLoggedIn { H5HomeView(sessionStore: sessionStore) } else { LoginView() }
        }
        .task {
            await sessionStore.restoreSession()
        }
        .animation(.spring(duration: 0.35), value: sessionStore.isLoggedIn)
    }
}
