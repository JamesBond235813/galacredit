import Foundation
import SwiftUI

@MainActor
final class WorkspaceViewModel: ObservableObject {
    @Published var activeTab: AppTab = .profiles
    @Published var repaymentSegment: RepaymentSegment = .repayments
    @Published var applicationFilter: ApplicationStatusFilter = .reviewing
    @Published var repaymentOverdueFilter: OverdueFilter = .all
    @Published var financeOverdueFilter: OverdueFilter = .all
    @Published var keyword = ""
    @Published var repaymentStartDate = ""
    @Published var repaymentEndDate = ""
    @Published var items: [JSONMap] = []
    @Published var stats: JSONMap?
    @Published var repaymentStats: JSONMap?
    @Published var isLoading = false
    @Published var errorMessage = ""

    private let sessionStore: SessionStore

    init(sessionStore: SessionStore) {
        self.sessionStore = sessionStore
    }

    var visibleTabs: [AppTab] {
        WorkspaceLogic.visibleTabs(for: adminRoles, permissions: adminPermissions)
    }

    var adminRoles: [String] {
        sessionStore.admin?.array("roles").compactMap(\.stringValue) ?? []
    }

    var adminPermissions: [String] {
        sessionStore.admin?.array("permissions").compactMap(\.stringValue) ?? []
    }

    var currentOverdueFilter: OverdueFilter {
        activeTab == .finance ? financeOverdueFilter : repaymentOverdueFilter
    }

    var summaryCards: [SummaryCardContent] {
        WorkspaceLogic.summaryCards(
            for: activeTab,
            stats: stats,
            repaymentStats: repaymentStats,
            overdueFilter: currentOverdueFilter
        )
    }

    /// 首次加载工作台数据。
    ///
    /// :param none: 无
    /// :return: 无
    func bootstrapIfNeeded() async {
        if !visibleTabs.contains(activeTab) {
            activeTab = visibleTabs.first ?? .profiles
        }
        await reloadAll()
    }

    /// 切换 tab 后刷新数据。
    ///
    /// :param tab: 新 tab
    /// :return: 无
    func switchTab(_ tab: AppTab) async {
        activeTab = tab
        keyword = ""
        await reloadAll()
    }

    /// 刷新统计与列表。
    ///
    /// :param none: 无
    /// :return: 无
    func reloadAll() async {
        guard let token = sessionStore.admin != nil ? sessionStore.token : nil else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            async let statsRequest = sessionStore.apiClient.get(path: "/admin/stats", token: token)
            async let repaymentRequest: JSONMap = needsRepaymentStats
                ? sessionStore.apiClient.get(path: "/admin/repayment-stats", query: repaymentStatsQueryItems(), token: token)
                : [:]
            async let listRequest = loadList(token: token)
            self.stats = try await statsRequest
            self.repaymentStats = try await repaymentRequest
            self.items = try await listRequest
            self.errorMessage = ""
        } catch APIError.unauthorized {
            sessionStore.logout()
        } catch {
            self.errorMessage = error.localizedDescription
        }
    }

    private var needsRepaymentStats: Bool {
        activeTab == .repayments || activeTab == .finance
    }

    /// 根据当前筛选加载列表。
    ///
    /// :param token: Bearer token
    /// :return: 列表项数组
    private func loadList(token: String) async throws -> [JSONMap] {
        if activeTab == .profiles {
            var query = baseQueryItems()
            if !keyword.isEmpty {
                query.append(URLQueryItem(name: "keyword", value: keyword))
            }
            let response = try await sessionStore.apiClient.get(path: "/admin/users", query: query, token: token)
            return response.array("items").compactMap(\.objectValue)
        }

        var query = baseQueryItems()
        let scope = WorkspaceLogic.scope(for: activeTab, segment: repaymentSegment)
        if !scope.isEmpty {
            query.append(URLQueryItem(name: "scope", value: scope))
        }
        if activeTab == .applications, applicationFilter != .all {
            query.append(URLQueryItem(name: "status", value: applicationFilter.rawValue))
        }
        if activeTab == .repayments || activeTab == .finance {
            switch currentOverdueFilter {
            case .overdue:
                query.append(URLQueryItem(name: "status", value: "OVERDUE"))
            case .notOverdue:
                query.append(URLQueryItem(name: "status", value: "DISBURSED"))
            case .all:
                break
            }
        }
        if activeTab == .repayments {
            appendRepaymentDateRange(to: &query)
        }
        if !keyword.isEmpty {
            query.append(URLQueryItem(name: "phone", value: keyword))
        }
        let response = try await sessionStore.apiClient.get(path: "/admin/loans", query: query, token: token)
        var rows = response.array("items").compactMap(\.objectValue)
        if activeTab == .applications {
            rows = try await enrichApplicationItems(rows, token: token)
        }
        return rows
    }

    private func baseQueryItems() -> [URLQueryItem] {
        [
            URLQueryItem(name: "skip", value: "0"),
            URLQueryItem(name: "limit", value: "20")
        ]
    }

    private func repaymentStatsQueryItems() -> [URLQueryItem] {
        guard activeTab == .repayments else { return [] }
        var query: [URLQueryItem] = []
        appendRepaymentDateRange(to: &query)
        return query
    }

    private func appendRepaymentDateRange(to query: inout [URLQueryItem]) {
        let start = repaymentStartDate.trimmingCharacters(in: .whitespacesAndNewlines)
        let end = repaymentEndDate.trimmingCharacters(in: .whitespacesAndNewlines)
        if !start.isEmpty {
            query.append(URLQueryItem(name: "due_date_start", value: start))
        }
        if !end.isEmpty {
            query.append(URLQueryItem(name: "due_date_end", value: end))
        }
    }

    /// 补全申请列表中的用户详情。
    ///
    /// :param rows: 原始订单行
    /// :param token: Bearer token
    /// :return: 补齐后的订单行
    private func enrichApplicationItems(_ rows: [JSONMap], token: String) async throws -> [JSONMap] {
        var enriched: [JSONMap] = []
        for row in rows {
            let userID = row.int("user_id", fallback: row.int("owner_id", fallback: 0))
            guard userID > 0 else {
                enriched.append(row)
                continue
            }
            var next = row
            let detail = try await sessionStore.apiClient.get(path: "/admin/users/\(userID)", token: token)
            let ipAudit = try await sessionStore.apiClient.get(path: "/admin/users/\(userID)/ip-audit", token: token)
            var detailWithAudit = detail
            detailWithAudit["_ip_audit"] = .object(ipAudit)
            next["_user_detail"] = .object(detailWithAudit)
            enriched.append(next)
        }
        return enriched
    }
}
