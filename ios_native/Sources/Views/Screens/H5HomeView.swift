import SwiftUI
import WebKit
import CoreLocation

struct H5HomeView: View {
    @ObservedObject var sessionStore: SessionStore
    var body: some View { H5WebView(token: sessionStore.token, onLogout: sessionStore.logout).ignoresSafeArea() }
}

private struct H5WebView: UIViewRepresentable {
    let token: String
    let onLogout: () -> Void

    func makeCoordinator() -> Coordinator { Coordinator(token: token, onLogout: onLogout) }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.preferences.javaScriptEnabled = true
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        let url = AppConfig.webBaseURL.appendingPathComponent("home")
        webView.load(URLRequest(url: url))
        context.coordinator.webView = webView
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        guard !token.isEmpty else { return }
        context.coordinator.token = token
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, CLLocationManagerDelegate {
        weak var webView: WKWebView?
        let locationManager = CLLocationManager()
        var token: String
        let onLogout: () -> Void
        init(token: String, onLogout: @escaping () -> Void) { self.token = token; self.onLogout = onLogout; super.init(); locationManager.delegate = self }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            let escaped = token.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "'", with: "\\'")
            webView.evaluateJavaScript("localStorage.setItem('token','\(escaped)'); window.dispatchEvent(new Event('storage'));", completionHandler: nil)
            locationManager.requestWhenInUseAuthorization()
        }

        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if let url = navigationAction.request.url, url.host != AppConfig.webBaseURL.host { decisionHandler(.cancel) } else { decisionHandler(.allow) }
        }
    }
}
