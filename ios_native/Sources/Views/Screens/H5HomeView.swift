import SwiftUI
import WebKit
import ContactsUI
import UIKit
import PhotosUI
import UniformTypeIdentifiers
import CoreLocation

struct H5HomeView: View {
    @ObservedObject var sessionStore: SessionStore
    @Environment(\.scenePhase) private var scenePhase
    var body: some View {
        H5WebView(
            token: sessionStore.token,
            riskTask: sessionStore.riskTask,
            isActive: scenePhase == .active,
            onLogout: sessionStore.logout
        )
        .ignoresSafeArea()
    }
}

private struct H5WebView: UIViewRepresentable {
    let token: String
    let riskTask: JSONMap?
    let isActive: Bool
    let onLogout: () -> Void

    func makeCoordinator() -> Coordinator { Coordinator(token: token, riskTask: riskTask, isActive: isActive, onLogout: onLogout) }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        // Token 保存在原生 Keychain；WebView 使用非持久存储，避免用户退出后残留网页会话。
        configuration.websiteDataStore = .nonPersistent()
        // 使用 iOS 14+ 的页面级 JavaScript 开关，避免调用已弃用的 preferences.javaScriptEnabled。
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        configuration.userContentController.add(context.coordinator, name: "galacreditContactPicker")
        configuration.userContentController.add(context.coordinator, name: "galacreditLogout")
        configuration.userContentController.add(context.coordinator, name: "galacreditRetry")
        configuration.userContentController.add(context.coordinator, name: "galacreditLocation")
        configuration.userContentController.add(context.coordinator, name: "galacreditImagePicker")
        // 让共用 UniApp 业务层知道自己运行在 iOS 原生壳中，避免把 iOS 风控信号误标为 H5。
        // 仅注入设备摘要和渠道，不注入短信、通讯录或原始设备标识。
        let nativeInfo = NativeEnvironment.info()
        if let data = try? JSONSerialization.data(withJSONObject: nativeInfo),
           let json = String(data: data, encoding: .utf8) {
            configuration.userContentController.addUserScript(
                WKUserScript(source: "window.GalaCreditNativeInfo=\(json);", injectionTime: .atDocumentStart, forMainFrameOnly: true)
            )
        }
        // 在业务脚本执行前注入 token，避免首次加载先落到登录页再二次刷新。
        if let tokenData = try? JSONSerialization.data(withJSONObject: token),
           let tokenJSON = String(data: tokenData, encoding: .utf8) {
            // 将已编码的 JSON 字符串直接嵌入脚本，不能把 Swift 变量名原样交给 JavaScript。
            let source = "window.localStorage.setItem('token', \(tokenJSON));"
            configuration.userContentController.addUserScript(
                WKUserScript(source: source, injectionTime: .atDocumentStart, forMainFrameOnly: true)
            )
        }
        if let riskTask,
           let riskData = try? JSONEncoder().encode(JSONValue.object(riskTask)),
           let riskJSON = String(data: riskData, encoding: .utf8) {
            configuration.userContentController.addUserScript(
                WKUserScript(source: "window.localStorage.setItem('galacredit_risk_task',\(riskJSON));", injectionTime: .atDocumentStart, forMainFrameOnly: true)
            )
        }
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        context.coordinator.loadHome(in: webView)
        context.coordinator.webView = webView
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        guard !token.isEmpty else { return }
        context.coordinator.token = token
        context.coordinator.riskTask = riskTask
        context.coordinator.updateActiveState(isActive)
        if let riskTask,
           let data = try? JSONEncoder().encode(JSONValue.object(riskTask)),
           let json = String(data: data, encoding: .utf8) {
            webView.evaluateJavaScript("localStorage.setItem('galacredit_risk_task',\(json));", completionHandler: nil)
        }
    }

    static func dismantleUIView(_ webView: WKWebView, coordinator: Coordinator) {
        coordinator.cancelPendingOperations()
        webView.stopLoading()
        webView.configuration.userContentController.removeScriptMessageHandler(forName: "galacreditContactPicker")
        webView.configuration.userContentController.removeScriptMessageHandler(forName: "galacreditLogout")
        webView.configuration.userContentController.removeScriptMessageHandler(forName: "galacreditRetry")
        webView.configuration.userContentController.removeScriptMessageHandler(forName: "galacreditLocation")
        webView.configuration.userContentController.removeScriptMessageHandler(forName: "galacreditImagePicker")
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler, CNContactPickerDelegate, PHPickerViewControllerDelegate, CLLocationManagerDelegate {
        weak var webView: WKWebView?
        var token: String
        var riskTask: JSONMap?
        private var isActive: Bool
        let onLogout: () -> Void
        private var fileChooserCompletion: (([URL]?) -> Void)?
        private var imagePickerCallbackName: String?
        private var imagePickerSelectionLimit = 1
        private var contactPickerInFlight = false
        private let locationManager = CLLocationManager()
        private var locationCallbackName: String?
        private var locationTimeoutWorkItem: DispatchWorkItem?
        init(token: String, riskTask: JSONMap?, isActive: Bool, onLogout: @escaping () -> Void) {
            self.token = token
            self.riskTask = riskTask
            self.isActive = isActive
            self.onLogout = onLogout
            super.init()
        }

        /// App 回到前台时通知共用页面刷新状态，后台切换不触发网络请求。
        ///
        /// :param active: 当前场景是否处于前台活动状态
        /// :return: 无
        func updateActiveState(_ active: Bool) {
            let shouldNotify = active && !isActive
            isActive = active
            if shouldNotify {
                webView?.evaluateJavaScript("window.dispatchEvent(new Event('galacredit:resume'));", completionHandler: nil)
            }
        }

        /// 清理页面销毁时仍等待系统回调的原生操作，避免旧页面回调新页面。
        ///
        /// :return: 无
        func cancelPendingOperations() {
            fileChooserCompletion?(nil)
            fileChooserCompletion = nil
            imagePickerCallbackName = nil
            contactPickerInFlight = false
            locationTimeoutWorkItem?.cancel()
            locationTimeoutWorkItem = nil
            locationCallbackName = nil
            locationManager.stopUpdatingLocation()
            locationManager.delegate = nil
        }

        func loadHome(in webView: WKWebView) {
            let url = AppConfig.webBaseURL.appendingPathComponent("home")
            var request = URLRequest(url: url)
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            request.setValue("galacredit-ios", forHTTPHeaderField: "client-id")
            webView.load(request)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            // 用 JSON 字面量注入 token，避免手工转义遗漏换行或特殊字符导致脚本失效。
            guard let data = try? JSONSerialization.data(withJSONObject: token),
                  let tokenLiteral = String(data: data, encoding: .utf8) else { return }
            webView.evaluateJavaScript("localStorage.setItem('token',\(tokenLiteral)); window.dispatchEvent(new Event('storage'));", completionHandler: nil)
            if let riskTask,
               let riskData = try? JSONEncoder().encode(JSONValue.object(riskTask)),
               let riskJSON = String(data: riskData, encoding: .utf8) {
                webView.evaluateJavaScript("localStorage.setItem('galacredit_risk_task',\(riskJSON));", completionHandler: nil)
            }
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            showOfflineState(in: webView)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            showOfflineState(in: webView)
        }

        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }
            if url.scheme?.lowercased() == "tel" {
                UIApplication.shared.open(url, options: [:], completionHandler: nil)
                decisionHandler(.cancel)
                return
            }
            // 与 Android 壳保持一致：只允许 HTTPS 配置源站，拒绝明文和同主机不同端口的伪造页面。
            guard url.scheme?.lowercased() == "https",
                  url.host?.lowercased() == AppConfig.webBaseURL.host?.lowercased(),
                  (AppConfig.webBaseURL.port == nil || url.port == AppConfig.webBaseURL.port) else {
                decisionHandler(.cancel)
                return
            }
            decisionHandler(.allow)
        }

        /// 为 H5 的身份证和人脸上传提供系统图片选择器，并将临时文件 URL 回传给 WKWebView。
        ///
        /// :param webView: 当前网页容器
        /// :param parameters: 网页文件选择参数
        /// :param frame: 发起选择的网页 frame
        /// :param completionHandler: 文件选择结果回调
        /// :return: 无
        @available(iOS 18.4, *)
        func webView(
            _ webView: WKWebView,
            runOpenPanelWith parameters: WKOpenPanelParameters,
            initiatedByFrame frame: WKFrameInfo,
            completionHandler: @escaping ([URL]?) -> Void
        ) {
            guard let presenter = topViewController(from: webView.window?.rootViewController) else {
                completionHandler(nil)
                return
            }
            fileChooserCompletion?(nil)
            fileChooserCompletion = completionHandler
            var configuration = PHPickerConfiguration(photoLibrary: .shared())
            configuration.filter = .images
            configuration.selectionLimit = parameters.allowsMultipleSelection ? 2 : 1
            let picker = PHPickerViewController(configuration: configuration)
            picker.delegate = self
            presenter.present(picker, animated: true)
        }

        /// 接收 UniApp/H5 的一次性联系人选择请求。
        ///
        /// :param userContentController: WebKit 内容控制器
        /// :param message: JavaScript bridge 消息
        /// :return: 无
        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            if message.name == "galacreditLogout" {
                webView?.evaluateJavaScript("localStorage.removeItem('token'); localStorage.removeItem('galacredit_risk_task'); sessionStorage.clear();", completionHandler: nil)
                onLogout()
                return
            }
            if message.name == "galacreditRetry", let webView {
                loadHome(in: webView)
                return
            }
            if message.name == "galacreditLocation" {
                requestOneTimeLocation(message.body)
                return
            }
            if message.name == "galacreditImagePicker" {
                requestImagePicker(message.body)
                return
            }
            guard message.name == "galacreditContactPicker", let webView else { return }
            guard !contactPickerInFlight else {
                rejectContact(webView: webView)
                return
            }
            guard let presenter = topViewController(from: webView.window?.rootViewController) else {
                rejectContact(webView: webView)
                return
            }
            contactPickerInFlight = true
            let picker = CNContactPickerViewController()
            picker.delegate = self
            presenter.present(picker, animated: true)
        }

        /// 返回用户主动选择的一条联系人，不读取完整通讯录。
        ///
        /// :param picker: 系统联系人选择器
        /// :param contact: 用户选择的联系人
        /// :return: 无
        func contactPicker(_ picker: CNContactPickerViewController, didSelect contact: CNContact) {
            contactPickerInFlight = false
            let name = CNContactFormatter.string(from: contact, style: .fullName) ?? ""
            let phone = contact.phoneNumbers.first?.value.stringValue ?? ""
            guard let webView else { return }
            let payload: [String: String] = ["name": name, "phone": phone]
            let jsonData = (try? JSONSerialization.data(withJSONObject: payload)) ?? Data("{}".utf8)
            let json = String(data: jsonData, encoding: .utf8) ?? "{}"
            webView.evaluateJavaScript("window.__gcContactPickerResolve && window.__gcContactPickerResolve(\(json));", completionHandler: nil)
        }

        /// 联系人选择取消时通知页面。
        ///
        /// :param picker: 系统联系人选择器
        /// :return: 无
        func contactPickerDidCancel(_ picker: CNContactPickerViewController) {
            contactPickerInFlight = false
            guard let webView else { return }
            rejectContact(webView: webView)
        }

        /// 将用户选择的图片复制到应用临时目录，确保 WKWebView 在回调结束后仍可读取。
        ///
        /// :param picker: 图片选择器
        /// :param results: 用户选择的图片结果
        /// :return: 无
        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            picker.dismiss(animated: true)
            if let callback = imagePickerCallbackName {
                imagePickerCallbackName = nil
                deliverImageData(results, callbackName: callback)
                return
            }
            guard let completion = fileChooserCompletion else {
                fileChooserCompletion = nil
                return
            }
            fileChooserCompletion = nil
            guard !results.isEmpty else {
                completion(nil)
                return
            }
            let group = DispatchGroup()
            let lock = NSLock()
            var urls = Array<URL?>(repeating: nil, count: results.count)
            for (index, result) in results.enumerated() {
                group.enter()
                result.itemProvider.loadFileRepresentation(forTypeIdentifier: UTType.image.identifier) { sourceURL, _ in
                    defer { group.leave() }
                    guard let sourceURL else { return }
                    let ext = sourceURL.pathExtension.isEmpty ? "jpg" : sourceURL.pathExtension
                    let targetURL = FileManager.default.temporaryDirectory
                        .appendingPathComponent("galacredit-upload-\(UUID().uuidString).\(ext)")
                    do {
                        try FileManager.default.copyItem(at: sourceURL, to: targetURL)
                        lock.lock()
                        urls[index] = targetURL
                        lock.unlock()
                    } catch {
                        // 单张图片复制失败不应让其他已选图片丢失。
                    }
                }
            }
            group.notify(queue: .main) {
                completion(urls.compactMap { $0 })
            }
        }

        /// 为 iOS 18.0–18.3 提供不依赖 WKOpenPanelParameters 的图片选择桥接。
        ///
        /// :param body: JavaScript 传入的回调名和选择数量
        /// :return: 无；图片以压缩后的 data URL 回传
        private func requestImagePicker(_ body: Any) {
            guard let payload = body as? [String: Any],
                  let callback = payload["callbackName"] as? String,
                  callback.range(of: "^[A-Za-z_$][A-Za-z0-9_$]{0,80}$", options: .regularExpression) != nil,
                  let presenter = topViewController(from: webView?.window?.rootViewController) else {
                return
            }
            fileChooserCompletion?(nil)
            fileChooserCompletion = nil
            if let previousCallback = imagePickerCallbackName, let webView {
                imagePickerCallbackName = nil
                webView.evaluateJavaScript("window[\(jsonLiteral(previousCallback))] && window[\(jsonLiteral(previousCallback))]({images:[]});", completionHandler: nil)
            }
            imagePickerCallbackName = callback
            let requestedCount = (payload["count"] as? NSNumber)?.intValue ?? 1
            imagePickerSelectionLimit = max(1, min(2, requestedCount))
            var configuration = PHPickerConfiguration(photoLibrary: .shared())
            configuration.filter = .images
            configuration.selectionLimit = imagePickerSelectionLimit
            let picker = PHPickerViewController(configuration: configuration)
            picker.delegate = self
            presenter.present(picker, animated: true)
        }

        /// 压缩并回传原生选择的图片，避免把大尺寸原图直接放入 JavaScript 内存。
        ///
        /// :param results: PHPicker 返回的图片结果
        /// :param callbackName: 页面回调名
        /// :return: 无
        private func deliverImageData(_ results: [PHPickerResult], callbackName: String) {
            guard let webView else { return }
            if results.isEmpty {
                webView.evaluateJavaScript("window[\(jsonLiteral(callbackName))] && window[\(jsonLiteral(callbackName))]({images:[]});", completionHandler: nil)
                return
            }
            let group = DispatchGroup()
            let lock = NSLock()
            var dataURLs = Array<String?>(repeating: nil, count: results.count)
            for (index, result) in results.enumerated() {
                group.enter()
                result.itemProvider.loadDataRepresentation(forTypeIdentifier: UTType.image.identifier) { data, _ in
                    defer { group.leave() }
                    guard let data, let image = UIImage(data: data), let compressed = self.compressedImageData(image) else { return }
                    lock.lock()
                    dataURLs[index] = "data:image/jpeg;base64,\(compressed.base64EncodedString())"
                    lock.unlock()
                }
            }
            group.notify(queue: .main) {
                let payload: [String: Any] = ["images": dataURLs.compactMap { $0 }]
                guard let payloadData = try? JSONSerialization.data(withJSONObject: payload),
                      let payloadJSON = String(data: payloadData, encoding: .utf8) else { return }
                webView.evaluateJavaScript("window[\(self.jsonLiteral(callbackName))] && window[\(self.jsonLiteral(callbackName))](\(payloadJSON));", completionHandler: nil)
            }
        }

        private func compressedImageData(_ image: UIImage) -> Data? {
            let maxDimension: CGFloat = 2000
            let scale = min(1, maxDimension / max(image.size.width, image.size.height))
            let targetSize = CGSize(width: max(1, image.size.width * scale), height: max(1, image.size.height * scale))
            let renderer = UIGraphicsImageRenderer(size: targetSize)
            let resized = renderer.image { _ in image.draw(in: CGRect(origin: .zero, size: targetSize)) }
            return resized.jpegData(compressionQuality: 0.82)
        }

        private func jsonLiteral(_ value: String) -> String {
            guard let data = try? JSONSerialization.data(withJSONObject: value),
                  let result = String(data: data, encoding: .utf8) else { return "\"\"" }
            return result
        }

        private func rejectContact(webView: WKWebView) {
            webView.evaluateJavaScript("window.__gcContactPickerReject && window.__gcContactPickerReject();", completionHandler: nil)
        }

        /// 请求一次性前台定位，不启动持续后台跟踪。
        ///
        /// :param body: JavaScript 传入的回调名称对象
        /// :return: 无；结果通过 JavaScript 回调返回
        private func requestOneTimeLocation(_ body: Any) {
            guard let payload = body as? [String: Any],
                  let callback = payload["callbackName"] as? String,
                  callback.range(of: "^[A-Za-z_$][A-Za-z0-9_$]{0,80}$", options: .regularExpression) != nil else {
                return
            }
            if locationCallbackName != nil {
                deliverLocation(nil, error: "LOCATION_REQUEST_IN_PROGRESS")
            }
            locationCallbackName = callback
            locationTimeoutWorkItem?.cancel()
            let timeout = DispatchWorkItem { [weak self] in
                guard let self, self.locationCallbackName == callback else { return }
                self.deliverLocation(nil, error: "LOCATION_TIMEOUT")
            }
            locationTimeoutWorkItem = timeout
            DispatchQueue.main.asyncAfter(deadline: .now() + 30, execute: timeout)
            locationManager.delegate = self
            locationManager.desiredAccuracy = kCLLocationAccuracyHundredMeters
            switch locationManager.authorizationStatus {
            case .authorizedWhenInUse, .authorizedAlways:
                locationManager.requestLocation()
            case .notDetermined:
                locationManager.requestWhenInUseAuthorization()
            default:
                deliverLocation(nil, error: "LOCATION_PERMISSION_DENIED")
            }
        }

        func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
            switch manager.authorizationStatus {
            case .authorizedWhenInUse, .authorizedAlways:
                manager.requestLocation()
            case .denied, .restricted:
                deliverLocation(nil, error: "LOCATION_PERMISSION_DENIED")
            default:
                break
            }
        }

        func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
            guard let location = locations.last else {
                deliverLocation(nil, error: "LOCATION_UNAVAILABLE")
                return
            }
            deliverLocation(location, error: nil)
        }

        func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
            deliverLocation(nil, error: "LOCATION_UNAVAILABLE")
        }

        private func deliverLocation(_ location: CLLocation?, error: String?) {
            guard let callback = locationCallbackName,
                  let webView,
                  callback.range(of: "^[A-Za-z_$][A-Za-z0-9_$]{0,80}$", options: .regularExpression) != nil else {
                return
            }
            locationCallbackName = nil
            locationTimeoutWorkItem?.cancel()
            locationTimeoutWorkItem = nil
            var result: [String: Any] = [:]
            if let location {
                result = [
                    "latitude": location.coordinate.latitude,
                    "longitude": location.coordinate.longitude,
                    "accuracy": max(location.horizontalAccuracy, 0)
                ]
            } else {
                result = ["error": error ?? "LOCATION_UNAVAILABLE"]
            }
            guard let data = try? JSONSerialization.data(withJSONObject: result),
                  let json = String(data: data, encoding: .utf8),
                  let callbackJSON = try? JSONSerialization.data(withJSONObject: callback),
                  let callbackLiteral = String(data: callbackJSON, encoding: .utf8) else {
                return
            }
            let script = "window[\(callbackLiteral)] && window[\(callbackLiteral)](\(json));"
            DispatchQueue.main.async {
                webView.evaluateJavaScript(script, completionHandler: nil)
            }
        }

        private func showOfflineState(in webView: WKWebView) {
            let html = """
            <html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head>
            <body style='font-family:-apple-system;display:flex;min-height:100vh;align-items:center;justify-content:center;background:#f6f8fb;color:#172033'>
            <main style='text-align:center;padding:28px'><h2>Unable to load GalaCredit</h2><p>Check your connection and try again.</p>
            <button style='padding:14px 24px;border:0;border-radius:12px;background:#ea9518;color:white;font-size:16px' onclick='window.webkit.messageHandlers.galacreditRetry.postMessage({})'>Try again</button>
            </main></body></html>
            """
            webView.loadHTMLString(html, baseURL: AppConfig.webBaseURL)
        }

        private func topViewController(from root: UIViewController?) -> UIViewController? {
            if let presented = root?.presentedViewController { return topViewController(from: presented) }
            if let navigation = root as? UINavigationController { return topViewController(from: navigation.visibleViewController) }
            if let tab = root as? UITabBarController { return topViewController(from: tab.selectedViewController) }
            return root
        }
    }
}
