import SwiftUI

struct WorkspaceView: View {
    @EnvironmentObject private var sessionStore: SessionStore
    @StateObject private var viewModel: WorkspaceViewModel
    @State private var selectedItem: IdentifiedJSONItem?
    @State private var showLogoutPrompt = false
    @State private var activeDatePicker: RepaymentDatePickerTarget?
    @State private var selectedDate = Date()

    init(viewModel: WorkspaceViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                AppTheme.pageBackground
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 16) {
                        header
                        SummaryCardsView(cards: viewModel.summaryCards)
                        filterControls
                        listSection
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 12)
                    .padding(.bottom, 120)
                }

                tabBar
                    .ignoresSafeArea(.container, edges: .bottom)
            }
            .navigationBarHidden(true)
            .task {
                await viewModel.bootstrapIfNeeded()
            }
            .overlay(alignment: .center) {
                if let selectedItem {
                    DetailView(
                        item: selectedItem.value,
                        activeTab: viewModel.activeTab,
                        repaymentSegment: viewModel.repaymentSegment,
                        adminRoles: viewModel.adminRoles,
                        adminPermissions: viewModel.adminPermissions,
                        sessionStore: sessionStore,
                        onDismiss: closeDetail,
                        onCompleted: {
                            Task { await viewModel.reloadAll() }
                        }
                    )
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .transition(.move(edge: .trailing))
                    .zIndex(20)
                }
            }
            .animation(.easeInOut(duration: 0.28), value: selectedItem)
            .alert("退出当前账号？", isPresented: $showLogoutPrompt) {
                Button("取消", role: .cancel) {}
                Button("登出", role: .destructive) {
                    sessionStore.logout()
                }
            }
            .alert("提示", isPresented: .constant(!viewModel.errorMessage.isEmpty)) {
                Button("知道了") {
                    viewModel.errorMessage = ""
                }
            } message: {
                Text(viewModel.errorMessage)
            }
            .sheet(item: $activeDatePicker) { target in
                repaymentDatePickerSheet(target: target)
            }
        }
    }

    private var header: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 6) {
                Text("GalaCredit")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(AppTheme.muted)
                Text(viewModel.activeTab.title)
                    .font(.system(size: 34, weight: .bold, design: .rounded))
                    .foregroundStyle(AppTheme.text)
            }
            Spacer()
            Button {
                Task { await viewModel.reloadAll() }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .font(.system(size: 18, weight: .semibold))
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(SecondaryButtonStyle())

            Button {
                showLogoutPrompt = true
            } label: {
                Text(String((sessionStore.admin?.string("username", fallback: "我") ?? "我").prefix(1)).uppercased())
                    .font(.system(size: 16, weight: .bold))
                    .foregroundStyle(AppTheme.primary)
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(SecondaryButtonStyle())
        }
    }

    @ViewBuilder
    private var filterControls: some View {
        VStack(spacing: 12) {
            if viewModel.activeTab == .profiles {
                HStack(spacing: 8) {
                    SearchField(text: $viewModel.keyword, prompt: "搜索手机号、姓名、身份证")
                        .frame(maxWidth: .infinity)
                    Button("查询") {
                        Task { await viewModel.reloadAll() }
                    }
                    .buttonStyle(CompactQueryButtonStyle())
                    Button("清空") {
                        viewModel.keyword = ""
                        Task { await viewModel.reloadAll() }
                    }
                    .buttonStyle(CompactSecondaryButtonStyle())
                }
            }
            if viewModel.activeTab == .finance {
                financeFilterControls
            }
            if viewModel.activeTab == .applications {
                fullWidthChipRow(values: viewModel.applicationFilterOptions.map { ($0.rawValue, $0.title) }, current: viewModel.applicationFilter.rawValue) { selected in
                    guard let next = ApplicationStatusFilter(rawValue: selected) else { return }
                    Task { await viewModel.selectApplicationFilter(next) }
                }
            }
            if viewModel.activeTab == .repayments {
                repaymentDateRangeControls
                fullWidthChipRow(values: OverdueFilter.allCases.map { ($0.rawValue, $0.title) }, current: viewModel.repaymentOverdueFilter.rawValue) { selected in
                    guard let next = OverdueFilter(rawValue: selected) else { return }
                    Task { await viewModel.selectRepaymentOverdueFilter(next) }
                }
            }
            if viewModel.activeTab == .finance {
                fullWidthChipRow(values: OverdueFilter.allCases.map { ($0.rawValue, $0.title) }, current: viewModel.financeOverdueFilter.rawValue) { selected in
                    guard let next = OverdueFilter(rawValue: selected) else { return }
                    viewModel.financeOverdueFilter = next
                    Task { await viewModel.reloadAll() }
                }
            }
        }
    }

    private var financeFilterControls: some View {
        HStack(spacing: 8) {
            SearchField(text: $viewModel.keyword, prompt: "搜索手机号、姓名、身份证")
                .frame(maxWidth: .infinity)
            Button("查询") {
                Task { await viewModel.reloadAll() }
            }
            .buttonStyle(CompactQueryButtonStyle())
            Button("清空") {
                viewModel.keyword = ""
                Task { await viewModel.reloadAll() }
            }
            .buttonStyle(CompactSecondaryButtonStyle())
        }
    }

    private var repaymentDateRangeControls: some View {
        HStack(spacing: 8) {
            DatePickerField(text: viewModel.repaymentStartDate, prompt: "开始日期") {
                showDatePicker(.start)
            }
            DatePickerField(text: viewModel.repaymentEndDate, prompt: "结束日期") {
                showDatePicker(.end)
            }
            Button("查询") {
                Task { await viewModel.reloadAll() }
            }
            .buttonStyle(SecondaryButtonStyle())
        }
    }

    private func showDatePicker(_ target: RepaymentDatePickerTarget) {
        let currentText = target == .start ? viewModel.repaymentStartDate : viewModel.repaymentEndDate
        selectedDate = Self.dateOnlyFormatter.date(from: currentText) ?? Date()
        activeDatePicker = target
    }

    private func repaymentDatePickerSheet(target: RepaymentDatePickerTarget) -> some View {
        NavigationStack {
            VStack(spacing: 18) {
                DatePicker(
                    target.title,
                    selection: $selectedDate,
                    displayedComponents: .date
                )
                .datePickerStyle(.graphical)
                .tint(AppTheme.primary)
                Spacer(minLength: 0)
            }
            .padding(18)
            .navigationTitle(target.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("取消") {
                        activeDatePicker = nil
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("确定") {
                        let text = Self.dateOnlyFormatter.string(from: selectedDate)
                        if target == .start {
                            viewModel.repaymentStartDate = text
                        } else {
                            viewModel.repaymentEndDate = text
                        }
                        activeDatePicker = nil
                        Task { await viewModel.reloadAll() }
                    }
                    .font(.system(size: 15, weight: .semibold))
                }
            }
        }
        .presentationDetents([.medium])
    }

    private var listSection: some View {
        LazyVStack(spacing: 12) {
            if viewModel.isLoading && viewModel.items.isEmpty {
                ProgressView("加载中...")
                    .frame(maxWidth: .infinity, minHeight: 120)
            } else if viewModel.items.isEmpty {
                Text("暂无数据")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(AppTheme.muted)
                    .frame(maxWidth: .infinity, minHeight: 120)
            } else {
                ForEach(Array(viewModel.items.enumerated()), id: \.offset) { _, item in
                    ItemCardView(item: item, activeTab: viewModel.activeTab)
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: 0.28)) {
                                selectedItem = IdentifiedJSONItem(value: item)
                            }
                        }
                }
            }
        }
    }

    private func closeDetail() {
        withAnimation(.easeInOut(duration: 0.28)) {
            selectedItem = nil
        }
    }

    private var tabBar: some View {
        HStack(spacing: 4) {
            ForEach(viewModel.visibleTabs, id: \.self) { tab in
                let isActive = viewModel.activeTab == tab
                Button {
                    Task { await viewModel.switchTab(tab) }
                } label: {
                    VStack(spacing: 6) {
                        Image(systemName: tab.iconName)
                            .font(.system(size: 18, weight: .bold))
                        Text(tab.title)
                            .font(.system(size: 11, weight: .bold))
                    }
                    .foregroundStyle(isActive ? AppTheme.primary : AppTheme.muted)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(
                        Capsule(style: .continuous)
                            .fill(isActive ? Color.white.opacity(0.92) : Color.clear)
                            .shadow(color: isActive ? Color.white.opacity(0.85) : Color.clear, radius: 8, x: -4, y: -4)
                            .shadow(color: isActive ? AppTheme.primary.opacity(0.16) : Color.clear, radius: 14, x: 5, y: 7)
                    )
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 6)
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 10)
        .padding(.top, 8)
        .padding(.bottom, 10)
        .background(Color.clear)
        .background(
            RoundedRectangle(cornerRadius: 34, style: .continuous)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 34, style: .continuous)
                        .stroke(Color.white.opacity(0.78), lineWidth: 1)
                )
                .shadow(color: Color.white.opacity(0.75), radius: 14, x: -8, y: -8)
                .shadow(color: Color.black.opacity(0.12), radius: 22, x: 0, y: 10)
                .padding(.horizontal, 10)
                .padding(.top, 8)
                .padding(.bottom, 10)
        )
        .compositingGroup()
    }

    private func fullWidthChipRow(values: [(String, String)], current: String, onSelect: @escaping (String) -> Void) -> some View {
        HStack(spacing: 8) {
            ForEach(values, id: \.0) { value, title in
                Button(title) {
                    guard value != current else { return }
                    onSelect(value)
                }
                .buttonStyle(WideChipButtonStyle(active: value == current))
            }
        }
    }

    private static let dateOnlyFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
}

private enum RepaymentDatePickerTarget: String, Identifiable {
    case start
    case end

    var id: String {
        rawValue
    }

    var title: String {
        switch self {
        case .start:
            return "选择开始日期"
        case .end:
            return "选择结束日期"
        }
    }
}

private struct WideChipButtonStyle: ButtonStyle {
    let active: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(active ? Color.white : AppTheme.text)
            .frame(maxWidth: .infinity)
            .frame(height: 40)
            .background(
                Capsule(style: .continuous)
                    .fill(active ? AppTheme.primary : Color.white.opacity(0.74))
            )
            .overlay(
                Capsule(style: .continuous)
                    .stroke(active ? AppTheme.primary.opacity(0.25) : AppTheme.stroke, lineWidth: 1)
            )
    }
}

private struct CompactQueryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .bold))
            .foregroundStyle(Color.white)
            .frame(width: 58, height: 44)
            .background(AppTheme.primary.opacity(configuration.isPressed ? 0.82 : 0.95), in: Capsule(style: .continuous))
            .overlay(
                Capsule(style: .continuous)
                    .stroke(Color.white.opacity(0.3), lineWidth: 1)
            )
    }
}

private struct CompactSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(AppTheme.text)
            .frame(width: 54, height: 44)
            .background(Color.white.opacity(configuration.isPressed ? 0.86 : 0.74), in: Capsule(style: .continuous))
            .overlay(
                Capsule(style: .continuous)
                    .stroke(AppTheme.stroke, lineWidth: 1)
            )
    }
}

private struct ItemCardView: View {
    let item: JSONMap
    let activeTab: AppTab

    var body: some View {
        if activeTab == .applications {
            applicationCard
        } else {
            defaultCard
        }
    }

    private var defaultCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            cardHeader
            HStack(spacing: 12) {
                ForEach(Array(infoCells.enumerated()), id: \.offset) { _, info in
                    cell(title: info.0, value: info.1)
                }
            }
            if noteText != "--" {
                Text(noteText)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundStyle(AppTheme.muted)
                    .lineLimit(2)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassCard()
    }

    private var applicationCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            cardHeader
            infoLine("申请时间", AppFormatter.dateTime(item.string("application_submitted_at", fallback: item.string("created_at"))))
            infoLine("最新IP", latestIPText)
            infoLine("IP位置", latestIPLocationText)
            infoLine("最新GPS", latestGPSText)
            infoLine("GPS位置", latestGPSLocationText)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassCard()
    }

    private var cardHeader: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 6) {
                Text(displayName)
                    .font(.system(size: 19, weight: .bold))
                    .foregroundStyle(AppTheme.text)
                Text(subtitle)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundStyle(AppTheme.muted)
                    .lineLimit(2)
            }
            Spacer()
            if !riskLabels.isEmpty {
                HStack(spacing: 5) {
                    ForEach(riskLabels, id: \.self) { label in
                        riskPill(label)
                    }
                }
            }
            Text(statusText)
                .font(.system(size: 11, weight: .bold))
                .foregroundStyle(statusColor)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(statusColor.opacity(0.14), in: Capsule())
        }
    }

    private var displayName: String {
        item.string("user_name", fallback: item.string("name", fallback: item.string("phone", fallback: "--")))
    }

    private var subtitle: String {
        switch activeTab {
        case .applications:
            return "\(item.string("user_phone", fallback: item.string("phone"))) · \(item.string("user_source_channel_name", fallback: item.string("source_channel_name", fallback: "未知渠道")))"
        case .profiles:
            return "\(item.string("phone")) · \(item.string("source_channel_name", fallback: item.string("source_channel_sales_name", fallback: "自然流量")))"
        default:
            return item.string("user_phone", fallback: item.string("phone"))
        }
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
        return map[status] ?? status
    }

    private var riskLabels: [String] {
        var labels: [String] = []
        if item.bool("blacklist_hit") || item.bool("user_blacklist_hit") || item.bool("current_blacklist_hit") {
            labels.append("黑名单")
        }
        if item.bool("risk_list_hit") || item.bool("user_risk_list_hit") || item.bool("current_risk_list_hit") {
            labels.append("风险名单")
        }
        if item.bool("user_location_risk_hit") || item.bool("location_risk_hit") {
            labels.append("风险地区")
        }
        if item.bool("location_risk_blocked") {
            labels.append("位置风控")
        }
        return labels
    }

    private var statusColor: Color {
        switch item.string("status", fallback: item.string("current_loan_status")) {
        case "SETTLED":
            return AppTheme.positive
        case "OVERDUE", "REJECTED", "CARD_REJECTED":
            return AppTheme.danger
        case "WITHDRAWING":
            return AppTheme.warning
        default:
            return AppTheme.primary
        }
    }

    private var infoCells: [(String, String)] {
        WorkspaceLogic.listCardInfoCells(for: activeTab, item: item)
    }

    private var noteText: String {
        WorkspaceLogic.listCardNoteText(for: item)
    }

    private func cell(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(value)
                .font(.system(size: value.count > 8 ? 14 : 18, weight: .bold, design: .rounded))
                .foregroundStyle(AppTheme.text)
                .lineLimit(2)
                .minimumScaleFactor(0.75)
            Text(title)
                .font(.system(size: 11, weight: .medium))
                .foregroundStyle(AppTheme.muted)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(Color.white.opacity(0.58), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }

    private func riskPill(_ label: String) -> some View {
        let isLocation = label == "风险地区" || label == "位置风控"
        let color = isLocation ? AppTheme.warning : AppTheme.danger
        return Text(label)
            .font(.system(size: 10, weight: .bold))
            .foregroundStyle(color)
            .padding(.horizontal, 7)
            .padding(.vertical, 4)
            .background(color.opacity(0.13), in: Capsule())
    }

    private func infoLine(_ label: String, _ value: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Text(label)
                .font(.system(size: 12, weight: .medium))
                .foregroundStyle(AppTheme.muted)
                .frame(width: 62, alignment: .leading)
            Text(value.isEmpty ? "--" : value)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(AppTheme.text)
                .frame(maxWidth: .infinity, alignment: .leading)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private var userDetail: JSONMap {
        item.object("_user_detail") ?? item
    }

    private var latestIPText: String {
        latestIPEvent?.string("ip", fallback: "--") ?? "--"
    }

    private var latestIPLocationText: String {
        guard let row = latestIPEvent else { return "" }
        return WorkspaceLogic.normalizedAddress(parts: [
            row.string("country"),
            row.string("province"),
            row.string("city"),
            row.string("district"),
            row.string("address")
        ])
    }

    private var latestGPSText: String {
        if let event = latestGPSEvent {
            let lonLat = event.string("lon_lat")
            if !lonLat.isEmpty { return lonLat }
        }
        let latitude = userDetail.string("location_latitude")
        let longitude = userDetail.string("location_longitude")
        if latitude.isEmpty && longitude.isEmpty { return "--" }
        return "\(latitude.isEmpty ? "--" : latitude), \(longitude.isEmpty ? "--" : longitude)"
    }

    private var latestGPSLocationText: String {
        if let event = latestGPSEvent {
            return WorkspaceLogic.normalizedAddress(parts: [
                event.string("lon_lat_province"),
                event.string("lon_lat_city"),
                event.string("lon_lat_district"),
                event.string("lon_lat_detail")
            ])
        }
        return WorkspaceLogic.normalizedAddress(parts: [
            userDetail.string("location_province"),
            userDetail.string("location_city"),
            userDetail.string("location_district"),
            userDetail.string("location_street"),
            userDetail.string("location_address")
        ])
    }

    private var latestIPEvent: JSONMap? {
        let items = userDetail.object("_ip_audit")?.array("items") ?? []
        return items.first?.objectValue
    }

    private var latestGPSEvent: JSONMap? {
        for value in userDetail.array("events") {
            guard let event = value.objectValue else { continue }
            if !event.string("lon_lat").isEmpty {
                return event
            }
        }
        return nil
    }
}

private struct DatePickerField: View {
    let text: String
    let prompt: String
    let onTap: () -> Void

    var body: some View {
        Button {
            onTap()
        } label: {
            HStack(spacing: 6) {
                Text(text.isEmpty ? prompt : text)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(text.isEmpty ? AppTheme.muted : AppTheme.text)
                    .lineLimit(1)
                Spacer(minLength: 0)
                Image(systemName: "calendar")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(AppTheme.muted)
            }
            .padding(.horizontal, 12)
            .frame(height: 44)
            .background(Color.white.opacity(0.78), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .stroke(AppTheme.stroke, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}
