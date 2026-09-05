import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @State private var phone = ""
    @State private var code = ""
    @State private var consent = false
    @State private var captcha: JSONMap?
    @State private var showCaptcha = false
    @State private var legalPage: String?
    @State private var message = ""
    @State private var cooldown = 0
    @State private var cooldownTask: Task<Void, Never>?
    @FocusState private var focus: Field?
    private enum Field { case phone, code }
    private let orange = Color(red: 234 / 255, green: 149 / 255, blue: 24 / 255)

    var body: some View {
        GeometryReader { proxy in
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    HStack(spacing: 12) {
                        GalaCreditMark().frame(width: 62, height: 62)
                        VStack(alignment: .leading, spacing: 0) {
                            Text("GalaCredit").font(.system(size: 31, weight: .bold, design: .rounded))
                            Text("Credit when it matters").font(.system(size: 13, weight: .medium)).foregroundStyle(.secondary)
                        }
                    }
                    .padding(.top, max(48, proxy.size.height * 0.14))
                    VStack(spacing: 14) { phoneField; codeField }.padding(.top, 58)
                    agreement.padding(.top, 18)
                    Button(action: login) {
                        Group { if sessionStore.isLoading { ProgressView().tint(.white) } else { Text("Sign In") } }
                            .font(.system(size: 16, weight: .semibold)).foregroundStyle(.white)
                            .frame(maxWidth: .infinity).frame(height: 50).background(orange, in: Capsule())
                    }
                    .disabled(phone.count != 9 || code.count != 6 || !consent || sessionStore.isLoading)
                    .opacity((phone.count != 9 || code.count != 6 || !consent) ? 0.45 : 1)
                    if !message.isEmpty || !sessionStore.errorMessage.isEmpty { Text(message.isEmpty ? sessionStore.errorMessage : message).font(.caption).foregroundStyle(.red).padding(.top, 12) }
                }
                .padding(.horizontal, 24).padding(.bottom, 28).frame(maxWidth: 440).frame(maxWidth: .infinity)
            }
            .scrollDismissesKeyboard(.interactively)
            .background(Color(red: 0.985, green: 0.98, blue: 0.965).ignoresSafeArea())
        }
        .sheet(isPresented: Binding(get: { legalPage != nil }, set: { if !$0 { legalPage = nil } })) { LegalView(path: legalPage ?? "agreement") }
        .sheet(isPresented: $showCaptcha) { CaptchaSheet(onVerified: sendCode, onRefresh: loadCaptcha).presentationDetents([.height(250)]) }
        .onDisappear { cooldownTask?.cancel() }
    }

    private var phoneField: some View {
        HStack(spacing: 10) {
            Text("🇬🇭  +233").font(.system(size: 15, weight: .semibold)); Divider().frame(height: 24)
            TextField("Enter mobile number", text: $phone).keyboardType(.numberPad).focused($focus, equals: .phone)
                .onChange(of: phone) { v in phone = String(v.filter(\.isNumber).prefix(9)) }
            Text("\(phone.count)/9").font(.caption).foregroundStyle(.secondary)
        }.padding(.horizontal, 16).frame(height: 54).background(.white, in: RoundedRectangle(cornerRadius: 14))
    }

    private var codeField: some View {
        HStack(spacing: 8) {
            TextField("Enter the 6-digit code", text: $code).keyboardType(.numberPad).focused($focus, equals: .code)
                .onChange(of: code) { v in code = String(v.filter(\.isNumber).prefix(6)) }
            Button(cooldown > 0 ? "\(cooldown)s" : "Send code", action: loadCaptcha).font(.system(size: 13, weight: .semibold)).foregroundStyle(orange).disabled(phone.count != 9 || cooldown > 0 || sessionStore.isLoading)
        }.padding(.horizontal, 16).frame(height: 54).background(.white, in: RoundedRectangle(cornerRadius: 14))
    }

    private var agreement: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top, spacing: 8) {
                Button { consent.toggle() } label: {
                    Image(systemName: consent ? "checkmark.square.fill" : "square")
                        .foregroundStyle(consent ? orange : .secondary)
                }
                .buttonStyle(.plain)
                .accessibilityLabel(consent ? "Consent selected" : "Consent not selected")
                Text("I agree to GalaCredit's User Agreement, Privacy Policy and Personal Data Authorization.")
            }
            Button("Read agreements and privacy notice") { legalPage = "agreement" }
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(orange)
                .buttonStyle(.plain)
                .accessibilityHint("Opens the GalaCredit agreement and privacy notice")
        }
        .font(.system(size: 12))
        .foregroundStyle(.secondary)
    }

    private func loadCaptcha() {
        guard phone.count == 9, cooldown == 0 else { return }
        Task {
            do {
                captcha = try await sessionStore.createCaptcha(phone: phone)
                showCaptcha = true
            } catch {
                message = error.localizedDescription
            }
        }
    }

    private func sendCode(offset: Double, elapsed: Int) {
        guard let id = captcha?.string("captcha_id"), cooldown == 0 else { return }
        Task {
            do {
                let response = try await sessionStore.verifyAndSendCode(phone: phone, captchaID: id, offsetX: offset, elapsedMs: elapsed)
                showCaptcha = false
                startCooldown(response.int("cooldown_seconds", fallback: 60))
            } catch {
                message = error.localizedDescription
            }
        }
    }

    /// 启动验证码冷却，避免弱网或重复点击造成短信接口重复请求。
    ///
    /// :param seconds: 服务端返回的冷却秒数
    /// :return: 无
    private func startCooldown(_ seconds: Int) {
        cooldownTask?.cancel()
        cooldown = max(seconds, 1)
        cooldownTask = Task { @MainActor in
            while cooldown > 0 && !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 1_000_000_000)
                if !Task.isCancelled { cooldown -= 1 }
            }
        }
    }
    private func login() { Task { await sessionStore.login(phone: phone, smsCode: code) } }
}

private struct LegalView: View {
    let path: String
    private var document: String {
        if path == "agreement" {
            return """
            GALACREDIT USER AGREEMENT

            Last updated: 5 September 2026

            GalaCredit provides an online application service for short-term credit in Ghana. Eligibility, fees, limits, disbursement and repayment dates are shown before you confirm a product. Applying does not guarantee approval. You must provide accurate information belonging to you and protect your registered phone, SIM and verification codes.

            You authorise GalaCredit and approved providers to verify identity, application, device, location and risk information as described in the Personal Data Authorization. iOS does not read SMS content. An authorised internal Android build may offer optional SMS review only after separate consent and Android permission; the device filters to the latest 90 days and published keyword matches before upload. The current builds do not read or upload a complete installed-app list.

            Before confirming a loan, the app displays the nominal amount, fees, estimated cash received, repayment amount, due dates, instalments and overdue charges. Repay only through methods displayed or confirmed by GalaCredit. Questions and complaints can be submitted through Customer Support.

            This operational draft must be reviewed by qualified Ghanaian legal and compliance advisers before production release.
            """
        }
        return """
        GALACREDIT PERSONAL DATA AUTHORIZATION

        Last updated: 5 September 2026

        GalaCredit may process your name, Ghana Card and face-verification images, registered mobile number, application and loan records, emergency contacts you choose, one-time location checks, device/browser signals, support records and lawful fraud or risk results for account security, identity verification, responsible lending, servicing and legal obligations.

        iOS builds do not read SMS content. SMS review is limited to an authorised internal Android build, after separate consent and Android SMS permission. The device keeps only messages from the most recent 90 days that match the published sms_keys20260602.csv regular-expression keywords; older, future-dated and unmatched messages are not uploaded, and the server filters again. The current builds do not read or upload a complete installed-app list.

        The app receives only the emergency contact you choose, requests location only after a user action and permission, and uses selected Ghana Card and face images for identity verification. You may decline optional collection and ask Customer Support about access, correction, retention, deletion and complaints.

        This operational notice must be reviewed by qualified Ghanaian legal and compliance advisers before production release.
        """
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                Text(document)
                    .font(.system(size: 15))
                    .foregroundStyle(.primary)
                    .multilineTextAlignment(.leading)
                    .textSelection(.enabled)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(24)
            }
            .navigationTitle(path == "agreement" ? "User Agreement" : "Privacy Policy")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

private struct CaptchaSheet: View {
    let onVerified: (Double, Int) -> Void
    let onRefresh: () -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var offset: CGFloat = 0
    @State private var started = Date()
    var body: some View {
        VStack(spacing: 16) {
            Text("Complete the security check").font(.headline)
            GeometryReader { proxy in
                let maxOffset = max(proxy.size.width - 54, 1)
                ZStack(alignment: .leading) {
                    Capsule().fill(Color.gray.opacity(0.15)); Text("Slide right to send the code").font(.caption).foregroundStyle(.secondary).frame(maxWidth: .infinity)
                    Circle().fill(Color(red: 234/255, green: 149/255, blue: 24/255)).frame(width: 46, height: 46).offset(x: offset).overlay(Image(systemName: "chevron.right").foregroundStyle(.white).offset(x: offset))
                        .gesture(DragGesture().onChanged { value in offset = min(max(0, value.translation.width), maxOffset) }.onEnded { _ in if offset > maxOffset * 0.9 { onVerified(Double(offset), Int(Date().timeIntervalSince(started) * 1000)); dismiss() } else { offset = 0 } })
                }
            }.frame(height: 46)
            Button("Refresh", action: onRefresh).font(.subheadline)
        }.padding(24)
    }
}
