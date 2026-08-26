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
    @FocusState private var focus: Field?
    private enum Field { case phone, code }
    private let orange = Color(red: 234 / 255, green: 149 / 255, blue: 24 / 255)

    var body: some View {
        GeometryReader { proxy in
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    HStack(spacing: 12) {
                        CreditCardLogo(color: orange).frame(width: 62, height: 62)
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
    }

    private var phoneField: some View {
        HStack(spacing: 10) {
            Text("🇬🇭  +233").font(.system(size: 15, weight: .semibold)); Divider().frame(height: 24)
            TextField("Enter mobile number", text: $phone).keyboardType(.numberPad).focused($focus, equals: .phone)
                .onChange(of: phone) { _, v in phone = String(v.filter(\.isNumber).prefix(9)) }
            Text("\(phone.count)/9").font(.caption).foregroundStyle(.secondary)
        }.padding(.horizontal, 16).frame(height: 54).background(.white, in: RoundedRectangle(cornerRadius: 14))
    }

    private var codeField: some View {
        HStack(spacing: 8) {
            TextField("Enter the 6-digit code", text: $code).keyboardType(.numberPad).focused($focus, equals: .code)
                .onChange(of: code) { _, v in code = String(v.filter(\.isNumber).prefix(6)) }
            Button("Send code", action: loadCaptcha).font(.system(size: 13, weight: .semibold)).foregroundStyle(orange).disabled(phone.count != 9)
        }.padding(.horizontal, 16).frame(height: 54).background(.white, in: RoundedRectangle(cornerRadius: 14))
    }

    private var agreement: some View {
        HStack(alignment: .top, spacing: 8) {
            Button { consent.toggle() } label: { Image(systemName: consent ? "checkmark.square.fill" : "square").foregroundStyle(consent ? orange : .secondary) }.buttonStyle(.plain)
            Text("I agree to GalaCredit's ") + Text("User Agreement").foregroundStyle(orange).underline() + Text(", ") + Text("Privacy Policy").foregroundStyle(orange).underline() + Text(" and ") + Text("Personal Data Authorization").foregroundStyle(orange).underline() + Text(".")
        }.font(.system(size: 12)).foregroundStyle(.secondary)
    }

    private func loadCaptcha() { guard phone.count == 9 else { return }; Task { do { captcha = try await sessionStore.createCaptcha(phone: phone); showCaptcha = true } catch { message = error.localizedDescription } } }
    private func sendCode(offset: Double, elapsed: Int) { guard let id = captcha?.string("captcha_id") else { return }; Task { do { _ = try await sessionStore.verifyAndSendCode(phone: phone, captchaID: id, offsetX: offset, elapsedMs: elapsed); showCaptcha = false } catch { message = error.localizedDescription } } }
    private func login() { Task { await sessionStore.login(phone: phone, smsCode: code) } }
}

private struct CreditCardLogo: View {
    let color: Color
    var body: some View {
        Canvas { context, size in
            let rect = CGRect(x: 3, y: size.height * 0.18, width: size.width - 6, height: size.height * 0.64)
            context.fill(Path(roundedRect: rect, cornerRadius: 7), with: .color(color))
            context.fill(Path(CGRect(x: 3, y: size.height * 0.42, width: size.width - 6, height: size.height * 0.08)), with: .color(.white.opacity(0.96)))
            context.fill(Path(CGRect(x: size.width * 0.54, y: size.height * 0.62, width: size.width * 0.23, height: size.height * 0.10)), with: .color(.white))
        }
    }
}

private struct LegalView: View {
    let path: String
    var body: some View {
        NavigationStack { ScrollView { Text(path == "agreement" ? "GalaCredit User Agreement\n\nPlease review the terms governing your use of GalaCredit services." : "GalaCredit Personal Data Authorization\n\nWe explain what data is collected, why it is needed, and how it is protected.").padding(24) }.navigationTitle(path == "agreement" ? "User Agreement" : "Privacy Policy").navigationBarTitleDisplayMode(.inline) }
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
