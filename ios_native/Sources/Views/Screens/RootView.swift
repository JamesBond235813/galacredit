import SwiftUI

struct RootView: View {
    @EnvironmentObject private var sessionStore: SessionStore

    var body: some View {
        ZStack {
            AppTheme.pageBackground
                .ignoresSafeArea()

            if sessionStore.isLoggedIn {
                WorkspaceView(viewModel: WorkspaceViewModel(sessionStore: sessionStore))
            } else {
                LoginView()
            }
        }
        .task {
            if sessionStore.admin == nil {
                await sessionStore.restoreSession()
            }
        }
        .animation(.spring(duration: 0.35), value: sessionStore.isLoggedIn)
    }
}
