import SwiftUI

@main
struct XiaoHeBaoIOSApp: App {
    @StateObject private var sessionStore = SessionStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(sessionStore)
                .preferredColorScheme(.light)
        }
    }
}
