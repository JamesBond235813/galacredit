import SwiftUI

@main
struct GalaCreditIOSApp: App {
    @StateObject private var sessionStore = SessionStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(sessionStore)
                .preferredColorScheme(.light)
        }
    }
}
