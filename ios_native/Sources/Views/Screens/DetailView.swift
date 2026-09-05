import SwiftUI
import ImageIO
import UIKit

struct DetailView: View {
    let item: JSONMap
    let activeTab: AppTab
    let repaymentSegment: RepaymentSegment
    let adminRoles: [String]
    let adminPermissions: [String]
    @ObservedObject var sessionStore: SessionStore
    let onDismiss: () -> Void
    let onCompleted: () -> Void

    @State private var detail: JSONMap?
    @State private var ipAudit: JSONMap?
    @State private var riskReport: JSONMap?
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var selectedAction: AdminActionKind?
    @State private var selectedPhoto: PhotoPreviewItem?
    @State private var showReviewerAssign = false
    @State private var isTakingOverReviewer = false

    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                AppTheme.pageBackground
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    LazyVStack(alignment: .leading, spacing: 16) {
                        header
                        photoSection
                        infoSection(title: "核心信息", rows: coreRows)
                        riskReportSection
                        infoSection(title: "紧急联系人", rows: emergencyRows)
                        infoSection(title: "地理位置", rows: locationRows)
                        infoSection(title: "IP记录", rows: ipRows)
                        infoSection(title: "订单状态及审核批注", rows: orderAuditRows)
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 16)
                    .padding(.bottom, 160)
                }
                .padding(.top, 8)

                actionDock
                    .padding(.horizontal, 16)
                    .padding(.bottom, 18)
                    .padding(.bottom, 8)

                edgeDismissHandle
            }
            .navigationBarHidden(true)
            .task {
                await loadDetail()
            }
            .sheet(item: $selectedAction) { action in
                ActionFormSheet(
                    action: action,
                    item: detailContext,
                    sessionStore: sessionStore
                ) {
                    await loadDetail()
                    onCompleted()
                }
            }
            .sheet(item: $selectedPhoto) { photo in
                PhotoPreviewSheet(photo: photo, token: sessionStore.token)
            }
            .sheet(isPresented: $showReviewerAssign) {
                ReviewerAssignSheet(
                    item: detailContext,
                    sessionStore: sessionStore
                ) {
                    await loadDetail()
                    onCompleted()
                }
            }
            .alert("提示", isPresented: .constant(!errorMessage.isEmpty)) {
                Button("知道了") { errorMessage = "" }
            } message: {
                Text(errorMessage)
            }
        }
    }

    private var edgeDismissHandle: some View {
        HStack {
            Color.clear
                .frame(width: 36)
                .contentShape(Rectangle())
                .gesture(detailDismissGesture)
            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
        .ignoresSafeArea()
    }

    private var detailDismissGesture: some Gesture {
        DragGesture(minimumDistance: 24, coordinateSpace: .local)
            .onEnded { value in
                let horizontalDistance = value.translation.width
                let verticalDistance = abs(value.translation.height)
                if horizontalDistance > 90 && verticalDistance < 80 {
                    onDismiss()
                }
            }
    }

    private var detailContext: JSONMap {
        if activeTab == .profiles {
            return detail ?? item
        }
        var merged = item
        if let detail {
            merged["_user_detail"] = .object(detail)
        }
        if let ipAudit {
            merged["_ip_audit"] = .object(ipAudit)
        }
        if let riskReport {
            merged["_composite_risk_report"] = .object(riskReport)
        }
        return merged
    }

    private var header: some View {
        HStack(alignment: .top, spacing: 12) {
            Button {
                onDismiss()
            } label: {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .semibold))
                    .frame(width: 42, height: 42)
            }
            .buttonStyle(SecondaryButtonStyle())

            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .center, spacing: 8) {
                    Text(displayName)
                        .font(.system(size: 28, weight: .bold, design: .rounded))
                        .foregroundStyle(AppTheme.text)
                        .lineLimit(1)
                    badge(text: detailContext.bool("blacklist_hit") || userDetail.bool("blacklist_hit") ? "黑名单" : "正常", color: (detailContext.bool("blacklist_hit") || userDetail.bool("blacklist_hit")) ? AppTheme.danger : AppTheme.positive)
                    if detailContext.bool("location_risk_blocked") || userDetail.bool("location_risk_blocked") {
                        badge(text: "位置风控", color: AppTheme.warning)
                    }
                }
                Text("\(phoneText) · \(statusText)")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(AppTheme.muted)
            }
            Spacer(minLength: 8)
            reviewerBadge
        }
    }

    @ViewBuilder
    private var reviewerBadge: some View {
        if activeTab == .applications {
            if canAssignReviewer {
                Button {
                    showReviewerAssign = true
                } label: {
                    badge(text: "审核员 \(reviewerName)", color: AppTheme.primary)
                }
                .buttonStyle(.plain)
            } else if canTakeOverReviewer {
                Button {
                    Task { await takeOverReviewer() }
                } label: {
                    if isTakingOverReviewer {
                        ProgressView()
                            .tint(AppTheme.primary)
                            .frame(height: 24)
                    } else {
                        badge(text: "审核员 \(reviewerName) · 转给我", color: AppTheme.primary)
                    }
                }
                .buttonStyle(.plain)
                .disabled(isTakingOverReviewer)
            } else {
                badge(text: "审核员 \(reviewerName)", color: AppTheme.muted)
            }
        }
    }

    private var photoSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("认证照片")
                .font(.system(size: 15, weight: .bold))
                .foregroundStyle(AppTheme.text)
            HStack(spacing: 10) {
                photoBox(title: "身份证正面", url: userDetail.string("id_card_front_image_url"))
                photoBox(title: "身份证反面", url: userDetail.string("id_card_back_image_url"))
                photoBox(title: "人脸照", url: userDetail.string("face_image_url"))
            }
            .frame(maxWidth: .infinity)
        }
    }

    private var riskReportSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("风控报告")
                .font(.system(size: 15, weight: .bold))
                .foregroundStyle(AppTheme.text)
            if isLoading && riskReport == nil {
                ProgressView("风控数据加载中...")
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .glassCard()
            } else if let payload = compositeRiskPayload {
                RiskReportCardView(payload: payload, report: riskReport ?? [:], phoneText: phoneText)
            } else {
                Text("暂无风控报告")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(AppTheme.muted)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .glassCard()
            }
        }
    }

    @ViewBuilder
    private var actionDock: some View {
        let actions = WorkspaceLogic.actions(for: activeTab, item: detailContext, segment: repaymentSegment, roles: adminRoles, permissions: adminPermissions)
        if actions.count <= 2 {
            HStack(spacing: 10) {
                ForEach(actions, id: \.self) { action in
                    actionButton(action)
                }
            }
            .padding(10)
            .background(Color(red: 0.91, green: 0.93, blue: 0.96).opacity(0.92), in: RoundedRectangle(cornerRadius: 30, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .stroke(AppTheme.stroke, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.08), radius: 22, x: 0, y: 12)
            .compositingGroup()
            .frame(maxWidth: .infinity, alignment: .center)
        } else {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(actions, id: \.self) { action in
                        actionButton(action)
                    }
                }
                .padding(10)
            }
            .frame(width: actionDockWidth(for: actions.count))
            .background(Color(red: 0.91, green: 0.93, blue: 0.96).opacity(0.92), in: RoundedRectangle(cornerRadius: 30, style: .continuous))
            .clipShape(RoundedRectangle(cornerRadius: 30, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .stroke(AppTheme.stroke, lineWidth: 1)
            )
            .shadow(color: Color.black.opacity(0.08), radius: 22, x: 0, y: 12)
            .compositingGroup()
            .frame(maxWidth: .infinity, alignment: .center)
        }
    }

    private func actionButton(_ action: AdminActionKind) -> some View {
        Button(action.title) {
            if action == .refresh {
                Task { await loadDetail() }
            } else {
                selectedAction = action
            }
        }
        .buttonStyle(SecondaryButtonStyle(danger: action.isDanger))
    }

    private func actionDockWidth(for actionCount: Int) -> CGFloat {
        min(CGFloat(actionCount) * 106 + 24, 208)
    }

    private var userDetail: JSONMap {
        if activeTab == .profiles {
            return detail ?? item
        }
        return detail ?? item.object("_user_detail") ?? item
    }

    private var phoneText: String {
        userDetail.string("phone", fallback: item.string("user_phone", fallback: item.string("phone", fallback: "--")))
    }

    private var displayName: String {
        userDetail.string("name", fallback: item.string("user_name", fallback: item.string("name", fallback: phoneText)))
    }

    private var statusText: String {
        let status = latestLoan.string("status", fallback: item.string("status", fallback: item.string("current_loan_status")))
        let map: [String: String] = [
            "INIT": "待补资料",
            "REVIEWING": "审核中",
            "APPROVED": "待下单",
            "REJECTED": "未通过",
            "WITHDRAWING": "待发卡",
            "DISBURSED": "待付款",
            "SETTLED": "已结清",
            "OVERDUE": "已逾期",
            "CARD_REJECTED": "拒发卡"
        ]
        return map[status] ?? status
    }

    private var latestLoan: JSONMap {
        if let loan = userDetail.object("latest_loan") {
            return loan
        }
        return item
    }

    private var coreRows: [(String, String)] {
        if activeTab == .profiles {
            return [
                ("手机号", phoneText),
                ("身份证", userDetail.string("id_card_num", fallback: "--")),
                ("渠道", userDetail.string("source_channel_name", fallback: userDetail.string("source_channel_sales_name", fallback: "--"))),
                ("最新状态", statusText),
                ("授信额度", AppFormatter.currency(Double(userDetail.int("approved_limit", fallback: Int(latestLoan.double("approved_credit_limit")))))),
                ("注册时间", AppFormatter.dateTime(userDetail.string("created_at", fallback: item.string("created_at")))),
                ("位置风控", userDetail.bool("location_risk_blocked") ? userDetail.string("location_risk_reason", fallback: "已锁定") : "未锁定"),
                ("风险校验", riskCheckText)
            ]
        }
        return [
            ("状态", statusText),
            ("手机号", phoneText),
            ("身份证", userDetail.string("id_card_num", fallback: item.string("user_id_card_num", fallback: "--"))),
            ("渠道", userDetail.string("source_channel_name", fallback: userDetail.string("source_channel_sales_name", fallback: item.string("user_source_channel_name", fallback: item.string("user_source_channel_sales_name", fallback: "--"))))),
            ("复购", latestLoan.string("relend_label", fallback: item.string("relend_label", fallback: "初借"))),
            (detailPrimaryTimeLabel, detailPrimaryTimeText),
            ("其他费用", AppFormatter.currency(latestLoan.double("other_fee_amount", fallback: item.double("other_fee_amount")))),
            ("风险校验", riskCheckText)
        ]
    }

    private var emergencyRows: [(String, String)] {
        [
            ("联系人1", contactText(prefix: "emergency_contact1")),
            ("联系人2", contactText(prefix: "emergency_contact2"))
        ]
    }

    private func contactText(prefix: String) -> String {
        let name = userDetail.string("\(prefix)_name")
        let relation = userDetail.string("\(prefix)_relation")
        let phone = userDetail.string("\(prefix)_phone")
        if name.isEmpty && relation.isEmpty && phone.isEmpty {
            return "--"
        }
        return [
            name.isEmpty ? "--" : name,
            relation.isEmpty ? "--" : relation,
            phone.isEmpty ? "--" : phone
        ].joined(separator: " / ")
    }

    private var locationRows: [(String, String)] {
        [
            ("定位地址", locationText),
            ("经纬度", coordinateText),
            ("定位精度", userDetail.string("location_accuracy", fallback: "--")),
            ("定位来源", userDetail.string("location_source", fallback: "--")),
            ("更新时间", AppFormatter.dateTime(userDetail.string("location_updated_at"))),
            ("位置风控", userDetail.bool("location_risk_blocked") ? userDetail.string("location_risk_reason", fallback: "已锁定") : "未锁定")
        ]
    }

    private var ipRows: [(String, String)] {
        let items = ipAudit?.array("items") ?? []
        guard !items.isEmpty else {
            return [("最近记录", "--")]
        }
        return Array(items.prefix(3).enumerated()).map { index, value in
            let row = value.objectValue ?? [:]
            let auditAddress = auditAddressText(row)
            let content = [
                row.string("ip", fallback: "--"),
                auditAddress,
                AppFormatter.dateTime(row.string("created_at"))
            ].joined(separator: " / ")
            return ("记录\(index + 1)", content)
        }
    }

    private var orderAuditRows: [(String, String)] {
        [
            ("订单状态", statusText),
            ("复购", latestLoan.string("relend_label", fallback: item.string("relend_label", fallback: "初借"))),
            ("审批备注", latestLoan.string("review_note", fallback: item.string("review_note", fallback: "--"))),
            ("催收备注", latestLoan.string("collection_note", fallback: item.string("collection_note", fallback: "--"))),
            ("提交时间", AppFormatter.dateTime(latestLoan.string("application_submitted_at", fallback: item.string("application_submitted_at", fallback: item.string("created_at"))))),
            ("还款日", AppFormatter.dateTime(latestLoan.string("due_date", fallback: item.string("due_date"))))
        ]
    }

    private var compositeRiskPayload: JSONMap? {
        guard let report = riskReport else { return nil }
        if let payload = report.object("report_json") {
            return payload
        }
        let rawText = report.string("report_json")
        if !rawText.isEmpty,
           let data = rawText.data(using: .utf8),
           let value = try? JSONDecoder().decode(JSONValue.self, from: data) {
            return value.objectValue
        }
        return nil
    }

    private func badge(text: String, color: Color) -> some View {
        Text(text)
            .font(.system(size: 11, weight: .bold))
            .foregroundStyle(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(color.opacity(0.12), in: Capsule())
    }

    private func photoBox(title: String, url: String) -> some View {
        let photoURL = resolvedPhotoURL(from: url)
        return VStack(spacing: 8) {
            Button {
                guard let photoURL else { return }
                selectedPhoto = PhotoPreviewItem(title: title, url: photoURL)
            } label: {
                ZStack {
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .fill(Color.white.opacity(0.92))
                    AuthenticatedRemoteImage(url: photoURL, token: sessionStore.token, contentMode: .fill, maxPixelSize: 420)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                        .clipped()
                }
                .frame(height: 112)
                .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .stroke(AppTheme.stroke, lineWidth: 1)
                )
            }
            .frame(maxWidth: .infinity)
            .frame(height: 112)
            .buttonStyle(.plain)
            Text(title)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(AppTheme.muted)
                .lineLimit(1)
                .minimumScaleFactor(0.82)
        }
        .frame(maxWidth: .infinity)
    }

    private func resolvedPhotoURL(from rawValue: String) -> URL? {
        let trimmed = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        if let absoluteURL = URL(string: trimmed), absoluteURL.scheme != nil {
            return absoluteURL
        }
        let rootURL = AppConfig.apiBaseURL.deletingLastPathComponent()
        return URL(string: trimmed, relativeTo: rootURL)?.absoluteURL
    }

    private func infoSection(title: String, rows: [(String, String)]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 15, weight: .bold))
                .foregroundStyle(AppTheme.text)
            VStack(spacing: 10) {
                ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                    HStack(alignment: .top, spacing: 12) {
                        Text(row.0)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundStyle(AppTheme.muted)
                            .frame(width: 88, alignment: .leading)
                        Text(row.1.isEmpty ? "--" : row.1)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundStyle(AppTheme.text)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .glassCard()
        }
    }

    private var detailPrimaryTimeLabel: String {
        switch activeTab {
        case .applications:
            return "申请时间"
        case .cards:
            return "下单时间"
        case .repayments, .finance:
            return "应还款时间"
        case .profiles:
            return "注册时间"
        }
    }

    private var detailPrimaryTimeText: String {
        switch activeTab {
        case .applications:
            return AppFormatter.dateTime(userDetail.string("application_submitted_at", fallback: latestLoan.string("application_submitted_at", fallback: latestLoan.string("created_at"))))
        case .profiles:
            return AppFormatter.dateTime(userDetail.string("created_at", fallback: item.string("created_at")))
        case .cards:
            return AppFormatter.dateTime(latestLoan.string("ordered_at", fallback: latestLoan.string("application_submitted_at", fallback: latestLoan.string("created_at"))))
        case .repayments, .finance:
            return AppFormatter.dateTime(latestLoan.string("due_date", fallback: item.string("due_date")))
        }
    }

    private var riskCheckText: String {
        var tags: [String] = []
        if detailContext.bool("blacklist_hit") || detailContext.bool("user_blacklist_hit") || userDetail.bool("blacklist_hit") || latestLoan.bool("current_blacklist_hit") {
            tags.append("黑名单")
        }
        if detailContext.bool("risk_list_hit") || detailContext.bool("user_risk_list_hit") || userDetail.bool("risk_list_hit") || latestLoan.bool("current_risk_list_hit") {
            tags.append("风险名单")
        }
        if detailContext.bool("user_location_risk_hit") || detailContext.bool("location_risk_hit") || userDetail.bool("location_risk_hit") {
            tags.append("风险地区")
        }
        if userDetail.bool("location_risk_blocked") || detailContext.bool("location_risk_blocked") {
            tags.append("位置风控")
        }
        return tags.isEmpty ? "未命中" : tags.joined(separator: " / ")
    }

    private var locationText: String {
        WorkspaceLogic.normalizedAddress(parts: [
            userDetail.string("location_province"),
            userDetail.string("location_city"),
            userDetail.string("location_district"),
            userDetail.string("location_street"),
            userDetail.string("location_address")
        ])
    }

    private var coordinateText: String {
        let latitude = userDetail.string("location_latitude")
        let longitude = userDetail.string("location_longitude")
        if latitude.isEmpty && longitude.isEmpty {
            return "--"
        }
        return "\(latitude.isEmpty ? "--" : latitude), \(longitude.isEmpty ? "--" : longitude)"
    }

    private func auditAddressText(_ row: JSONMap) -> String {
        WorkspaceLogic.normalizedAddress(parts: [
            row.string("country"),
            row.string("province"),
            row.string("city"),
            row.string("district"),
            row.string("address")
        ])
    }

    private var reviewerName: String {
        latestLoan.string("review_admin_name", fallback: item.string("review_admin_name", fallback: "未分配"))
    }

    private var canAssignReviewer: Bool {
        activeTab == .applications && adminRoles.contains("ADMIN")
    }

    private var currentAdminID: Int {
        sessionStore.admin?.int("id") ?? 0
    }

    private var canTakeOverReviewer: Bool {
        activeTab == .applications
            && !adminRoles.contains("ADMIN")
            && hasPermission("loan-review-takeover")
            && currentAdminID > 0
            && latestLoan.string("status", fallback: item.string("status")) == "REVIEWING"
            && latestLoan.int("review_admin_id", fallback: item.int("review_admin_id")) != currentAdminID
    }

    private func hasPermission(_ permission: String) -> Bool {
        if adminRoles.contains("ADMIN") { return true }
        if !adminPermissions.isEmpty { return adminPermissions.contains(permission) }
        if permission == "applications" { return adminRoles.contains("REVIEW") }
        if permission == "loan-review-takeover" { return adminRoles.contains("REVIEW") }
        return false
    }

    /// 将审核中的申请转入当前审核员名下。
    ///
    /// :param none: 无
    /// :return: 无
    private func takeOverReviewer() async {
        let loanID = latestLoan.int("id", fallback: item.int("id", fallback: item.int("current_loan_id")))
        guard loanID > 0, currentAdminID > 0 else {
            errorMessage = "订单或审核员信息缺失，无法转单"
            return
        }
        isTakingOverReviewer = true
        defer { isTakingOverReviewer = false }
        do {
            _ = try await sessionStore.apiClient.post(
                path: "/admin/loans/\(loanID)/assign",
                body: [
                    "stage": .string("review"),
                    "admin_id": .number(Double(currentAdminID))
                ],
                token: sessionStore.token
            )
            await loadDetail()
            onCompleted()
        } catch APIError.unauthorized {
            sessionStore.logout()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 拉取详情、IP 审计与风控报告。
    ///
    /// :param none: 无
    /// :return: 无
    private func loadDetail() async {
        let userID = resolveUserID()
        guard userID > 0 else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            let detailResponse = try await sessionStore.apiClient.get(path: "/admin/users/\(userID)", token: sessionStore.token)
            async let ipAuditResponse = sessionStore.apiClient.get(path: "/admin/users/\(userID)/ip-audit", token: sessionStore.token)
            async let riskResponse = sessionStore.apiClient.post(path: "/admin/risk/composite-report", body: ["user_id": .number(Double(userID))], token: sessionStore.token)
            detail = detailResponse
            ipAudit = try await ipAuditResponse
            riskReport = try? await riskResponse
            errorMessage = ""
        } catch APIError.unauthorized {
            sessionStore.logout()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func resolveUserID() -> Int {
        if activeTab == .profiles {
            return item.int("id")
        }
        return item.int("user_id", fallback: item.int("owner_id", fallback: 0))
    }
}

private struct PhotoPreviewItem: Identifiable {
    let title: String
    let url: URL

    var id: String {
        "\(title)-\(url.absoluteString)"
    }
}

private struct AuthenticatedRemoteImage: View {
    let url: URL?
    let token: String
    var contentMode: ContentMode = .fill
    var maxPixelSize: CGFloat = 900
    @State private var image: UIImage?
    @State private var didFail = false

    var body: some View {
        ZStack {
            if let image {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: contentMode)
            } else {
                Image(systemName: didFail ? "exclamationmark.triangle" : "photo")
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundStyle(AppTheme.muted)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .clipped()
        .task(id: url) {
            await load()
        }
    }

    private func load() async {
        guard let url else {
            await MainActor.run {
                image = nil
                didFail = false
            }
            return
        }
        let cacheKey = "\(url.absoluteString)#\(Int(maxPixelSize))" as NSString
        if let cachedImage = RemoteImageMemoryCache.shared.image(forKey: cacheKey) {
            await MainActor.run {
                image = cachedImage
                didFail = false
            }
            return
        }
        var request = URLRequest(url: url)
        request.timeoutInterval = 18
        if !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode),
                  let loadedImage = Self.downsample(data: data, maxPixelSize: maxPixelSize) else {
                await MainActor.run { didFail = true }
                return
            }
            RemoteImageMemoryCache.shared.setImage(loadedImage, forKey: cacheKey)
            await MainActor.run {
                image = loadedImage
                didFail = false
            }
        } catch {
            await MainActor.run { didFail = true }
        }
    }

    private static func downsample(data: Data, maxPixelSize: CGFloat) -> UIImage? {
        let options = [kCGImageSourceShouldCache: false] as CFDictionary
        guard let source = CGImageSourceCreateWithData(data as CFData, options) else { return nil }
        let thumbnailOptions = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceShouldCacheImmediately: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceThumbnailMaxPixelSize: Int(maxPixelSize)
        ] as CFDictionary
        guard let image = CGImageSourceCreateThumbnailAtIndex(source, 0, thumbnailOptions) else { return nil }
        return UIImage(cgImage: image)
    }
}

private final class RemoteImageMemoryCache {
    static let shared = RemoteImageMemoryCache()
    private let cache = NSCache<NSString, UIImage>()

    private init() {
        cache.countLimit = 80
        cache.totalCostLimit = 28 * 1024 * 1024
    }

    func image(forKey key: NSString) -> UIImage? {
        cache.object(forKey: key)
    }

    func setImage(_ image: UIImage, forKey key: NSString) {
        cache.setObject(image, forKey: key)
    }
}

private struct PhotoPreviewSheet: View {
    let photo: PhotoPreviewItem
    let token: String
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.pageBackground
                    .ignoresSafeArea()
                AuthenticatedRemoteImage(url: photo.url, token: token, contentMode: .fit, maxPixelSize: 1800)
                    .padding(18)
            }
            .navigationTitle(photo.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("关闭") {
                        dismiss()
                    }
                    .font(.system(size: 14, weight: .semibold))
                }
            }
        }
    }
}

private struct RiskReportCardView: View {
    let payload: JSONMap
    let report: JSONMap
    let phoneText: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                riskMiniMetric(title: "报告时间", value: AppFormatter.dateTime(report.string("query_time", fallback: payload.string("query_time"))))
                riskMiniMetric(title: "报告评估结论", value: summaryBadge, color: summaryColor)
            }

            HStack(spacing: 10) {
                riskScoreMetric(title: "申请准入分", value: metric(from: applyDetail, key: "A22160001"))
                riskScoreMetric(title: "信用行为分", value: metric(from: behaviorDetail, key: "B22170001"))
            }

            HStack(spacing: 8) {
                riskMiniMetric(title: "最近放款", value: latestDisbursementText)
                riskMiniMetric(title: "探查结果", value: probeLabel)
                riskMiniMetric(title: "正常还款比例", value: metric(from: behaviorDetail, key: "B22170034"))
            }

            Text("风险维度")
                .font(.system(size: 14, weight: .bold))
                .foregroundStyle(AppTheme.text)
                .padding(.top, 2)

            riskDimensionGrid

            Text("命中原因")
                .font(.system(size: 14, weight: .bold))
                .foregroundStyle(AppTheme.text)
            VStack(alignment: .leading, spacing: 8) {
                ForEach(riskReasons, id: \.self) { reason in
                    Text("• \(reason)")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundStyle(AppTheme.muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .glassCard()
    }

    private var riskDimensionGrid: some View {
        VStack(spacing: 0) {
            HStack(spacing: 0) {
                dimensionBox(title: "系统核查", status: systemStatus, note: systemDescription)
                riskVerticalDivider
                dimensionBox(title: "位置 / IP", status: locationStatus, note: locationDescription)
            }
            riskHorizontalDivider
            HStack(spacing: 0) {
                dimensionBox(title: "履约行为", status: behaviorStatus, note: behaviorDescription)
                riskVerticalDivider
                dimensionBox(title: "探针C", status: probeStatus, note: probeDescription)
            }
        }
        .background(Color(red: 0.965, green: 0.972, blue: 0.985), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(AppTheme.stroke, lineWidth: 1)
        )
    }

    private var riskHorizontalDivider: some View {
        Rectangle()
            .fill(AppTheme.stroke)
            .frame(height: 1)
            .padding(.horizontal, 12)
    }

    private var riskVerticalDivider: some View {
        Rectangle()
            .fill(AppTheme.stroke)
            .frame(width: 1)
            .padding(.vertical, 10)
    }

    private var systemRisk: JSONMap {
        payload.object("system_risk") ?? [:]
    }

    private var panorama: JSONMap {
        payload.object("panorama") ?? [:]
    }

    private var panoramaPayload: JSONMap {
        panorama.object("payload") ?? [:]
    }

    private var panoramaData: JSONMap {
        panoramaPayload.object("data") ?? [:]
    }

    private var applyDetail: JSONMap {
        panoramaData.object("apply_report_detail") ?? panoramaPayload.object("apply_report_detail") ?? [:]
    }

    private var behaviorDetail: JSONMap {
        panoramaData.object("behavior_report_detail") ?? panoramaPayload.object("behavior_report_detail") ?? [:]
    }

    private var probe: JSONMap {
        payload.object("probe_c") ?? [:]
    }

    private var probeData: JSONMap {
        probe.object("payload")?.object("data") ?? [:]
    }

    private var probeLabel: String {
        probe.string("result_label")
    }

    private var latestOrder: JSONMap {
        payload.object("latest_order") ?? [:]
    }

    private var latestDisbursementText: String {
        let orderTime = latestOrder.string("disbursed_at")
        if !orderTime.isEmpty {
            return AppFormatter.dateTime(orderTime)
        }
        return metric(from: behaviorDetail, key: "B22170054")
    }

    private var summaryBadge: String {
        if systemRisk.bool("blacklist_hit") || systemRisk.bool("login_location_blocked") {
            return "评分偏高"
        }
        if systemRisk.bool("location_risk_hit") || metric(from: behaviorDetail, key: "B22170026") != "0" {
            return "建议复核"
        }
        if probeLabel == "逾期未还款" {
            return "评分偏高"
        }
        return "风险可控"
    }

    private var summaryColor: Color {
        switch summaryBadge {
        case "评分偏高":
            return AppTheme.danger
        case "建议复核":
            return AppTheme.warning
        default:
            return AppTheme.positive
        }
    }

    private func metric(from source: JSONMap, key: String) -> String {
        let text = source.string(key, fallback: "--")
        return text.isEmpty ? "--" : text
    }

    private func riskMiniMetric(title: String, value: String, color: Color = AppTheme.text) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 10, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
                .lineLimit(1)
                .minimumScaleFactor(0.86)
            Text(value.isEmpty ? "--" : value)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(color)
                .lineLimit(2)
                .minimumScaleFactor(0.76)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .frame(minHeight: 52, alignment: .leading)
        .padding(9)
        .background(Color(red: 0.965, green: 0.972, blue: 0.985), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(AppTheme.stroke, lineWidth: 1)
        )
    }

    private func riskScoreMetric(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            Text(value.isEmpty ? "--" : value)
                .font(.system(size: 28, weight: .bold, design: .rounded))
                .foregroundStyle(AppTheme.primary)
                .lineLimit(1)
                .minimumScaleFactor(0.72)
            Text("手机号 \(phoneText)")
                .font(.system(size: 10, weight: .medium))
                .foregroundStyle(AppTheme.muted)
                .lineLimit(1)
                .minimumScaleFactor(0.82)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .frame(minHeight: 92, alignment: .leading)
        .padding(12)
        .background(Color(red: 0.965, green: 0.972, blue: 0.985), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(AppTheme.stroke, lineWidth: 1)
        )
    }

    private func dimensionBox(title: String, status: String, note: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            Text(status)
                .font(.system(size: 13, weight: .bold))
                .foregroundStyle(AppTheme.text)
            Text(note)
                .font(.system(size: 10, weight: .medium))
                .foregroundStyle(AppTheme.muted)
                .lineLimit(3)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .frame(minHeight: 74, alignment: .leading)
        .padding(12)
    }

    private var systemStatus: String {
        if systemRisk.bool("blacklist_hit") { return "高风险" }
        if systemRisk.bool("risk_list_hit") { return "建议复核" }
        return "正常"
    }

    private var systemDescription: String {
        if systemRisk.bool("blacklist_hit") {
            return valueOr(systemRisk.string("blacklist_reason", fallback: "命中系统黑名单"))
        }
        if systemRisk.bool("risk_list_hit") {
            return valueOr(systemRisk.string("risk_list_reason", fallback: "命中风险名单，建议人工复核"))
        }
        let bindingCount = systemRisk.int("same_phone_binding_count")
        return bindingCount > 1 ? "同手机号曾绑定 \(bindingCount) 个账号" : "黑名单与风险名单均未命中"
    }

    private var locationStatus: String {
        if systemRisk.bool("login_location_blocked") { return "高风险" }
        if systemRisk.bool("location_risk_hit") { return "偏高" }
        return "正常"
    }

    private var locationDescription: String {
        if systemRisk.bool("login_location_blocked") {
            return valueOr(systemRisk.string("login_location_reason", fallback: "登录位置已被系统拦截"))
        }
        if systemRisk.bool("location_risk_hit") {
            return valueOr(systemRisk.string("location_risk_detail", fallback: "命中风险地址关键词"))
        }
        return "定位与 IP 暂未发现明显异常"
    }

    private var behaviorStatus: String {
        let overdueCount = metric(from: behaviorDetail, key: "B22170026")
        if overdueCount != "--" && overdueCount != "0" { return "偏高" }
        let score = metric(from: behaviorDetail, key: "B22170001")
        if let intScore = Int(score), intScore >= 700 {
            return "正常"
        }
        return score == "--" ? "待补充" : "建议关注"
    }

    private var behaviorDescription: String {
        let score = metric(from: behaviorDetail, key: "B22170001")
        let overdueCount = metric(from: behaviorDetail, key: "B22170026")
        let overdueAmount = metric(from: behaviorDetail, key: "B22170032")
        if overdueCount != "--" && overdueCount != "0" {
            return "近12个月 M0+ 逾期 \(overdueCount) 笔，累计 \(overdueAmount)"
        }
        return "信用行为分 \(score)，正常付款占比 \(metric(from: behaviorDetail, key: "B22170034"))"
    }

    private var probeStatus: String {
        switch probeLabel {
        case "逾期未还款":
            return "高风险"
        case "逾期后已还款", "无法确认":
            return "建议复核"
        case "正常履约":
            return "正常"
        default:
            return "待补充"
        }
    }

    private var probeDescription: String {
        "探针结果 \(valueOr(probeLabel))，当前逾期机构 \(metric(from: probeData, key: "currently_overdue"))，履约机构 \(metric(from: probeData, key: "currently_performance"))"
    }

    private var riskReasons: [String] {
        var reasons: [String] = []
        if systemRisk.bool("blacklist_hit") {
            reasons.append("系统黑名单命中：\(valueOr(systemRisk.string("blacklist_reason", fallback: "存在历史风险记录")))")
        }
        if systemRisk.bool("risk_list_hit") {
            reasons.append("风险名单命中：\(valueOr(systemRisk.string("risk_list_reason", fallback: "外部风险名单命中")))")
        }
        if systemRisk.bool("location_risk_hit") {
            reasons.append(valueOr(systemRisk.string("location_risk_detail", fallback: "申请定位或访问 IP 命中风险地址关键词")))
        }
        if systemRisk.bool("login_location_blocked") {
            reasons.append("登录位置拦截：\(valueOr(systemRisk.string("login_location_reason", fallback: "当前登录环境存在异常")))")
        }
        let overdueCount = metric(from: behaviorDetail, key: "B22170026")
        if overdueCount != "--" && overdueCount != "0" {
            reasons.append("履约行为显示近12个月 M0+ 逾期 \(overdueCount) 笔，累计金额 \(metric(from: behaviorDetail, key: "B22170032"))")
        }
        if !probeLabel.isEmpty && probeLabel != "正常履约" {
            reasons.append("探针C结果为“\(probeLabel)”，最长逾期天数 \(metric(from: probeData, key: "max_overdue_days"))")
        }
        if reasons.isEmpty {
            return [
                "系统核查、位置/IP 与外部履约探查暂未发现明显强风险信号。",
                "建议结合认证照片、联系人与订单信息继续人工审核。"
            ]
        }
        return reasons
    }

    private func valueOr(_ value: String, fallback: String = "--") -> String {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty || trimmed.lowercased() == "null" ? fallback : trimmed
    }
}

private struct ReviewerAssignSheet: View {
    let item: JSONMap
    @ObservedObject var sessionStore: SessionStore
    let onCompleted: () async -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var assignees: [JSONMap] = []
    @State private var selectedID = 0
    @State private var isLoading = false
    @State private var isSubmitting = false
    @State private var errorMessage = ""

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.pageBackground
                    .ignoresSafeArea()

                VStack(alignment: .leading, spacing: 16) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("选择审核员")
                            .font(.system(size: 28, weight: .bold, design: .rounded))
                            .foregroundStyle(AppTheme.text)
                        Text("先选择审核员，再点击确定完成转单。")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundStyle(AppTheme.muted)
                    }

                    if isLoading {
                        ProgressView("审核员加载中...")
                            .frame(maxWidth: .infinity, minHeight: 120)
                            .glassCard()
                    } else if assignees.isEmpty {
                        Text("暂无可分配审核员")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundStyle(AppTheme.muted)
                            .frame(maxWidth: .infinity, minHeight: 120)
                            .glassCard()
                    } else {
                        ScrollView(showsIndicators: false) {
                            VStack(spacing: 10) {
                                ForEach(assignees, id: \.self) { assignee in
                                    assigneeButton(assignee)
                                }
                            }
                        }
                        .glassCard()
                    }

                    if !errorMessage.isEmpty {
                        Text(errorMessage)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundStyle(AppTheme.danger)
                    }

                    HStack(spacing: 12) {
                        Button("取消") {
                            dismiss()
                        }
                        .buttonStyle(SecondaryButtonStyle())

                        Button {
                            Task { await submit() }
                        } label: {
                            if isSubmitting {
                                ProgressView().tint(.white)
                            } else {
                                Text("确定")
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle())
                    }
                }
                .padding(20)
            }
            .task {
                await loadAssignees()
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("关闭") { dismiss() }
                }
            }
        }
    }

    private func assigneeButton(_ assignee: JSONMap) -> some View {
        let adminID = assignee.int("id")
        let selected = adminID == selectedID
        return Button {
            selectedID = adminID
        } label: {
            HStack {
                Text(assignee.string("username", fallback: "--"))
                    .font(.system(size: 15, weight: .semibold))
                Spacer()
                if selected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(AppTheme.primary)
                }
            }
            .foregroundStyle(selected ? AppTheme.primary : AppTheme.text)
            .padding(.horizontal, 14)
            .frame(height: 48)
            .background(selected ? AppTheme.primary.opacity(0.12) : Color.white.opacity(0.64), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    /// 加载可转单审核员。
    ///
    /// :param none: 无
    /// :return: 无
    private func loadAssignees() async {
        guard assignees.isEmpty else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            selectedID = item.int("review_admin_id")
            assignees = try await sessionStore.apiClient.getArray(
                path: "/admin/loan-assignees",
                query: [URLQueryItem(name: "stage", value: "review")],
                token: sessionStore.token
            )
            if selectedID == 0 {
                selectedID = assignees.first?.int("id") ?? 0
            }
            errorMessage = ""
        } catch APIError.unauthorized {
            sessionStore.logout()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 提交审核员转单。
    ///
    /// :param none: 无
    /// :return: 无
    private func submit() async {
        guard selectedID > 0 else {
            errorMessage = "请选择审核员"
            return
        }
        let loanID = item.int("id", fallback: item.int("current_loan_id"))
        guard loanID > 0 else {
            errorMessage = "订单信息缺失，无法转单"
            return
        }
        isSubmitting = true
        defer { isSubmitting = false }
        do {
            _ = try await sessionStore.apiClient.post(
                path: "/admin/loans/\(loanID)/assign",
                body: [
                    "stage": .string("review"),
                    "admin_id": .number(Double(selectedID))
                ],
                token: sessionStore.token
            )
            await onCompleted()
            dismiss()
        } catch APIError.unauthorized {
            sessionStore.logout()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

private struct ActionFormSheet: View {
    let action: AdminActionKind
    let item: JSONMap
    @ObservedObject var sessionStore: SessionStore
    let onCompleted: () async -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var noteValue = ""
    @State private var creditValue = ""
    @State private var discountValue = "0"
    @State private var termValue = ""
    @State private var extensionTypeValue = "FREE"
    @State private var daysValue = "3"
    @State private var reductionValue = "0"
    @State private var receivedValue = ""
    @State private var otherFeeValue = "0"
    @State private var amountValue = ""
    @State private var actualRepaymentDate = Date()
    @State private var includeActualRepaymentDate = false
    @State private var isSubmitting = false
    @State private var errorMessage = ""
    @State private var didInitialize = false

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.pageBackground
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(alignment: .leading, spacing: 16) {
                        VStack(alignment: .leading, spacing: 10) {
                            Text(action.title)
                                .font(.system(size: 28, weight: .bold, design: .rounded))
                            Text("按当前云端与本地一致的接口规则提交这次操作。")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundStyle(AppTheme.muted)
                        }

                        contextCard
                        formCard

                        if action == .reconcile {
                            reconcilePreviewCard
                        }

                        if !errorMessage.isEmpty {
                            Text(errorMessage)
                                .font(.system(size: 13, weight: .medium))
                                .foregroundStyle(AppTheme.danger)
                                .padding(.horizontal, 6)
                        }

                        Button {
                            Task { await submit() }
                        } label: {
                            if isSubmitting {
                                ProgressView()
                                    .tint(.white)
                            } else {
                                Text("确认提交")
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle())
                    }
                    .padding(20)
                }
            }
            .task {
                initializeIfNeeded()
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("关闭") {
                        dismiss()
                    }
                }
            }
        }
    }

    private var contextCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("当前对象")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            VStack(spacing: 10) {
                summaryRow("客户", displayName)
                summaryRow("手机号", phoneText)
                summaryRow("订单状态", statusText)
                if !productName.isEmpty && productName != "--" {
                    summaryRow("商品", productName)
                }
                if item.int("id") > 0 {
                    summaryRow("订单 ID", "\(item.int("id"))")
                }
            }
        }
        .glassCard()
    }

    private var formCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(WorkspaceLogic.prompt(for: action))
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            actionFields
        }
        .glassCard()
    }

    @ViewBuilder
    private var actionFields: some View {
        switch action {
        case .approve:
            numericField(label: "授信额度", text: $creditValue)
            numericField(label: "减免额度", text: $discountValue)
            integerField(label: "期限天数", text: $termValue)
        case .reject:
            noteField(label: "审批备注", text: $noteValue)
        case .disburse:
            summaryBlock(rows: [
                ("下单商品", productName),
                ("E卡面值", AppFormatter.currency(item.double("ecard_face_value", fallback: item.double("credit_limit")))),
                ("信用支付金额", AppFormatter.currency(orderAmount))
            ])
            integerField(label: "账期天数", text: $termValue)
        case .rejectCard:
            noteField(label: "拒绝原因", text: $noteValue)
        case .saveNote:
            noteField(label: "审批意见", text: $noteValue)
        case .remind:
            noteField(label: "提醒备注", text: $noteValue)
        case .collect:
            noteField(label: "催收备注", text: $noteValue)
        case .ack, .settle, .reissueCard, .closeReissue, .refresh:
            summaryBlock(rows: [
                ("确认事项", "本次操作将直接提交到当前业务系统"),
                ("处理动作", action.title)
            ])
        case .reconcile:
            numericField(label: "登记收款", text: $receivedValue)
            numericField(label: "减免金额", text: $reductionValue)
            numericField(label: "其他费用", text: $otherFeeValue)
            noteField(label: "平账说明", text: $noteValue)
            Toggle("填写实际还款日", isOn: $includeActualRepaymentDate)
                .toggleStyle(SwitchToggleStyle(tint: AppTheme.primary))
            if includeActualRepaymentDate {
                DatePicker("实际还款日", selection: $actualRepaymentDate, displayedComponents: .date)
                    .datePickerStyle(.compact)
            }
        case .extend:
            extensionTypeSelector
            integerField(label: "展期天数", text: $daysValue)
            numericField(label: "减免金额", text: $reductionValue)
            noteField(label: "展期备注", text: $noteValue)
        case .adjustCredit:
            numericField(label: "增加可用额度", text: $amountValue)
            noteField(label: "额度调整备注", text: $noteValue)
        case .setCredit:
            numericField(label: "授信额度", text: $creditValue)
            noteField(label: "授信调整备注", text: $noteValue)
        case .blacklist:
            noteField(label: "拉黑原因", text: $noteValue)
        case .removeBlacklist:
            noteField(label: "移出说明", text: $noteValue)
        case .unlockLocation:
            noteField(label: "解除说明", text: $noteValue)
        }
    }

    private var extensionTypeSelector: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("展期类型")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            HStack(spacing: 8) {
                extensionTypeButton(title: "免费展期", value: "FREE")
                extensionTypeButton(title: "付费展期", value: "FEE")
            }
        }
    }

    private func extensionTypeButton(title: String, value: String) -> some View {
        Button(title) {
            extensionTypeValue = value
            noteValue = value == "FREE" ? "iOS 端免费展期" : "iOS 端付费展期"
        }
        .buttonStyle(ExtensionTypeButtonStyle(active: extensionTypeValue == value))
    }

    private var reconcilePreviewCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("平账预览")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            VStack(spacing: 10) {
                summaryRow("平账后已还款额", AppFormatter.currency(nextReceivedAmount))
                summaryRow("平账后减免金额", AppFormatter.currency(nextReductionAmount))
                summaryRow("平账后其他费用", AppFormatter.currency(nextOtherFeeAmount))
                summaryRow("本次实际到账合计", AppFormatter.currency(currentReceivedAmount + currentOtherFeeAmount))
                summaryRow("平账后剩余还款额", AppFormatter.currency(remainingRepaymentAmount))
            }
        }
        .glassCard()
    }

    private var phoneText: String {
        item.string("user_phone", fallback: item.string("phone", fallback: "--"))
    }

    private var displayName: String {
        item.string("user_name", fallback: item.string("name", fallback: phoneText))
    }

    private var productName: String {
        item.string("product_name", fallback: "--")
    }

    private var statusText: String {
        let status = item.string("status", fallback: item.string("current_loan_status"))
        let map: [String: String] = [
            "INIT": "待补资料",
            "REVIEWING": "审核中",
            "APPROVED": "待下单",
            "REJECTED": "未通过",
            "WITHDRAWING": "待发卡",
            "DISBURSED": "待付款",
            "SETTLED": "已结清",
            "OVERDUE": "已逾期",
            "CARD_REJECTED": "拒发卡"
        ]
        return map[status] ?? (status.isEmpty ? "--" : status)
    }

    private var orderAmount: Double {
        item.double("credit_limit", fallback: item.double("approved_credit_limit", fallback: item.double("remaining_repayment_amount")))
    }

    private var currentReceivedAmount: Double {
        doubleValue(receivedValue, fallback: item.double("remaining_repayment_amount"))
    }

    private var currentReductionAmount: Double {
        doubleValue(reductionValue, fallback: 0)
    }

    private var currentOtherFeeAmount: Double {
        doubleValue(otherFeeValue, fallback: 0)
    }

    private var nextReceivedAmount: Double {
        item.double("repaid_amount") + currentReceivedAmount
    }

    private var nextReductionAmount: Double {
        item.double("reduction_amount") + currentReductionAmount
    }

    private var nextOtherFeeAmount: Double {
        item.double("other_fee_amount") + currentOtherFeeAmount
    }

    private var remainingRepaymentAmount: Double {
        max(item.double("total_repayment_amount") - nextReceivedAmount - nextReductionAmount, 0)
    }

    private func summaryRow(_ title: String, _ value: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(AppTheme.muted)
                .frame(width: 92, alignment: .leading)
            Text(value.isEmpty ? "--" : value)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(AppTheme.text)
                .frame(maxWidth: .infinity, alignment: .leading)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private func summaryBlock(rows: [(String, String)]) -> some View {
        VStack(spacing: 10) {
            ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                summaryRow(row.0, row.1)
            }
        }
        .padding(14)
        .background(Color.white.opacity(0.58), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }

    private func numericField(label: String, text: Binding<String>) -> some View {
        fieldContainer(label: label) {
            TextField(label, text: text)
                .keyboardType(.decimalPad)
        }
    }

    private func integerField(label: String, text: Binding<String>) -> some View {
        fieldContainer(label: label) {
            TextField(label, text: text)
                .keyboardType(.numberPad)
        }
    }

    private func shortTextField(label: String, text: Binding<String>) -> some View {
        fieldContainer(label: label) {
            TextField(label, text: text)
                .textInputAutocapitalization(.characters)
        }
    }

    private func noteField(label: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            TextField(label, text: text, axis: .vertical)
                .lineLimit(4, reservesSpace: true)
                .padding(.horizontal, 16)
                .padding(.vertical, 14)
                .background(Color.white.opacity(0.8), in: RoundedRectangle(cornerRadius: 24, style: .continuous))
        }
    }

    private func fieldContainer<Content: View>(label: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(label)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.muted)
            content()
                .padding(.horizontal, 16)
                .frame(height: 50)
                .background(Color.white.opacity(0.8), in: RoundedRectangle(cornerRadius: 24, style: .continuous))
        }
    }

    /// 初始化表单默认值，保持与安卓端常用录入口径一致。
    ///
    /// :param none: 无
    /// :return: 无
    private func initializeIfNeeded() {
        guard !didInitialize else { return }
        didInitialize = true
        switch action {
        case .approve:
            creditValue = displayNumber(item.double("approved_credit_limit", fallback: 1000))
            discountValue = displayNumber(item.double("approval_discount_amount"))
            termValue = "\(max(item.int("term_days", fallback: item.int("product_term_days", fallback: 7)), 1))"
        case .reject:
            noteValue = "资料不符合要求"
        case .disburse:
            termValue = "\(max(item.int("term_days", fallback: item.int("product_term_days", fallback: 7)), 1))"
        case .rejectCard:
            noteValue = "卡池或订单信息不符合发卡要求"
        case .saveNote:
            noteValue = item.string("review_note")
        case .remind:
            noteValue = "已完成还款提醒"
        case .collect:
            noteValue = item.string("collection_note", fallback: "已执行逾期催收")
        case .reconcile:
            receivedValue = displayNumber(item.double("remaining_repayment_amount"))
            reductionValue = "0"
            otherFeeValue = "0"
            includeActualRepaymentDate = true
            actualRepaymentDate = defaultActualRepaymentDate
            noteValue = "iOS 端登记平账"
        case .extend:
            extensionTypeValue = "FREE"
            daysValue = "3"
            reductionValue = "0"
            noteValue = "iOS 端免费展期"
        case .adjustCredit:
            amountValue = "100"
            noteValue = "iOS 端增加可用额度"
        case .setCredit:
            creditValue = displayNumber(item.double("approved_credit_limit", fallback: 1000))
            noteValue = "iOS 端调整授信"
        case .blacklist:
            noteValue = "后台一键拉黑"
        case .removeBlacklist:
            noteValue = "后台移出黑名单"
        case .unlockLocation:
            noteValue = "管理员确认解除4小时位移风控"
        case .ack, .settle, .reissueCard, .closeReissue, .refresh:
            break
        }
    }

    /// 提交操作请求。
    ///
    /// :param none: 无
    /// :return: 无
    private func submit() async {
        if action == .refresh {
            await onCompleted()
            dismiss()
            return
        }
        guard let endpoint = WorkspaceLogic.endpoint(for: action, item: item) else {
            errorMessage = "当前操作未配置接口"
            return
        }
        isSubmitting = true
        defer { isSubmitting = false }
        do {
            guard let payload = buildPayload() else { return }
            if endpoint.method == "PATCH" {
                _ = try await sessionStore.apiClient.patch(path: endpoint.path, body: payload, token: sessionStore.token)
            } else {
                _ = try await sessionStore.apiClient.post(path: endpoint.path, body: payload, token: sessionStore.token)
            }
            await onCompleted()
            dismiss()
        } catch APIError.unauthorized {
            sessionStore.logout()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// 根据当前动作和表单内容构造请求体。
    ///
    /// :param none: 无
    /// :return: 请求体；校验失败时返回 nil
    private func buildPayload() -> JSONMap? {
        errorMessage = ""
        switch action {
        case .approve:
            let credit = doubleValue(creditValue, fallback: item.double("approved_credit_limit", fallback: 1000))
            let discount = doubleValue(discountValue, fallback: 0)
            let term = intValue(termValue, fallback: max(item.int("term_days", fallback: item.int("product_term_days", fallback: 7)), 1))
            guard credit > 0, term > 0 else {
                errorMessage = "请填写有效的授信额度和期限天数"
                return nil
            }
            return [
                "approved": .bool(true),
                "credit_limit": .number(credit),
                "approval_discount_amount": .number(discount),
                "term_days": .number(Double(term)),
                "review_note": .string("iOS 端审批通过")
            ]
        case .reject:
            return [
                "approved": .bool(false),
                "review_note": .string(noteValue.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "资料不符合要求" : noteValue.trimmingCharacters(in: .whitespacesAndNewlines))
            ]
        case .disburse:
            let term = intValue(termValue, fallback: max(item.int("term_days", fallback: item.int("product_term_days", fallback: 7)), 1))
            guard term > 0 else {
                errorMessage = "请填写有效的账期天数"
                return nil
            }
            return ["term_days": .number(Double(term))]
        case .rejectCard:
            return ["note": .string(normalizedNote(defaultValue: "卡池或订单信息不符合发卡要求"))]
        case .saveNote:
            return ["review_note": .string(noteValue.trimmingCharacters(in: .whitespacesAndNewlines))]
        case .remind:
            return ["note": .string(normalizedNote(defaultValue: "已完成还款提醒"))]
        case .collect:
            return ["note": .string(normalizedNote(defaultValue: item.string("collection_note", fallback: "已执行逾期催收")))]
        case .ack, .settle, .reissueCard, .closeReissue, .refresh:
            return [:]
        case .reconcile:
            var payload: JSONMap = [
                "received_amount": .number(currentReceivedAmount),
                "reduction_amount": .number(currentReductionAmount),
                "other_fee_amount": .number(currentOtherFeeAmount),
                "note": .string(normalizedNote(defaultValue: "iOS 端登记平账"))
            ]
            if includeActualRepaymentDate {
                payload["actual_repayment_date"] = .string(apiDateString(actualRepaymentDate))
            }
            return payload
        case .extend:
            let type = extensionTypeValue.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
            let days = intValue(daysValue, fallback: 3)
            let reduction = doubleValue(reductionValue, fallback: 0)
            guard type == "FREE" || type == "FEE" else {
                errorMessage = "请选择免费展期或付费展期"
                return nil
            }
            guard days > 0 else {
                errorMessage = "展期天数必须大于 0"
                return nil
            }
            return [
                "extension_type": .string(type),
                "days": .number(Double(days)),
                "reduction_amount": .number(reduction),
                "note": .string(normalizedNote(defaultValue: type == "FREE" ? "iOS 端免费展期" : "iOS 端付费展期"))
            ]
        case .adjustCredit:
            let amount = doubleValue(amountValue, fallback: 0)
            guard amount > 0 else {
                errorMessage = "请填写大于 0 的额度"
                return nil
            }
            return [
                "amount": .number(amount),
                "note": .string(normalizedNote(defaultValue: "iOS 端增加可用额度"))
            ]
        case .setCredit:
            let credit = doubleValue(creditValue, fallback: item.double("approved_credit_limit", fallback: 1000))
            guard credit > 0 else {
                errorMessage = "请填写有效的授信额度"
                return nil
            }
            return [
                "credit_limit": .number(credit),
                "note": .string(normalizedNote(defaultValue: "iOS 端调整授信"))
            ]
        case .blacklist:
            return ["note": .string(normalizedNote(defaultValue: "后台一键拉黑"))]
        case .removeBlacklist:
            return ["note": .string(normalizedNote(defaultValue: "后台移出黑名单"))]
        case .unlockLocation:
            return ["note": .string(normalizedNote(defaultValue: "管理员确认解除4小时位移风控"))]
        }
    }

    private func normalizedNote(defaultValue: String) -> String {
        let trimmed = noteValue.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? defaultValue : trimmed
    }

    private func doubleValue(_ value: String, fallback: Double) -> Double {
        Double(value.trimmingCharacters(in: .whitespacesAndNewlines)) ?? fallback
    }

    private func intValue(_ value: String, fallback: Int) -> Int {
        Int(value.trimmingCharacters(in: .whitespacesAndNewlines)) ?? fallback
    }

    private func displayNumber(_ value: Double) -> String {
        let integer = floor(value)
        return integer == value ? String(Int(value)) : String(value)
    }

    private func apiDateString(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    private var defaultActualRepaymentDate: Date {
        let raw = item.string("actual_repayment_date")
        guard raw.count >= 10 else { return Date() }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.date(from: String(raw.prefix(10))) ?? Date()
    }
}

private struct ExtensionTypeButtonStyle: ButtonStyle {
    let active: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(active ? Color.white : AppTheme.text)
            .frame(maxWidth: .infinity)
            .frame(height: 42)
            .background(
                Capsule(style: .continuous)
                    .fill(active ? AppTheme.primary : Color.white.opacity(configuration.isPressed ? 0.9 : 0.72))
            )
            .overlay(
                Capsule(style: .continuous)
                    .stroke(active ? AppTheme.primary.opacity(0.25) : Color.white.opacity(0.82), lineWidth: 1)
            )
    }
}
