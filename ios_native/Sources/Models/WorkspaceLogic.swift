import Foundation

enum WorkspaceLogic {
    /// 根据管理员角色计算可见 tab。
    ///
    /// :param roles: 管理员角色列表
    /// :return: 可见 tab 列表
    static func visibleTabs(for roles: [String]) -> [AppTab] {
        visibleTabs(for: roles, permissions: [])
    }

    /// 根据管理员权限计算可见 tab，权限优先，角色仅作旧数据兜底。
    ///
    /// :param roles: 管理员角色列表
    /// :param permissions: 后端返回的权限列表
    /// :return: 可见 tab 列表
    static func visibleTabs(for roles: [String], permissions: [String]) -> [AppTab] {
        var tabs: [AppTab] = []
        if hasPermission("users", roles: roles, permissions: permissions) {
            tabs.append(.profiles)
        }
        if hasPermission("applications", roles: roles, permissions: permissions) {
            tabs.append(.applications)
        }
        if hasPermission("disbursements", roles: roles, permissions: permissions) {
            tabs.append(.cards)
        }
        if hasPermission("repayments", roles: roles, permissions: permissions) || hasPermission("collections", roles: roles, permissions: permissions) {
            tabs.append(.repayments)
        }
        if hasPermission("financials", roles: roles, permissions: permissions) {
            tabs.append(.finance)
        }
        return tabs.isEmpty ? [.profiles] : tabs
    }

    /// 计算列表查询 scope。
    ///
    /// :param tab: 当前 tab
    /// :param segment: 回款分段
    /// :return: 后端 scope
    static func scope(for tab: AppTab, segment: RepaymentSegment) -> String {
        switch tab {
        case .profiles:
            return ""
        case .applications:
            return "REVIEWING"
        case .cards:
            return "WITHDRAWING"
        case .repayments:
            return "REPAYMENTS"
        case .finance:
            return "FINANCE"
        }
    }

    /// 计算当前 tab 对应操作集合。
    ///
    /// :param tab: 当前 tab
    /// :param item: 当前数据项
    /// :param segment: 回款分段
    /// :return: 操作列表
    static func actions(for tab: AppTab, item: JSONMap, segment: RepaymentSegment) -> [AdminActionKind] {
        actions(for: tab, item: item, segment: segment, roles: [], permissions: [])
    }

    /// 计算当前 tab 对应操作集合，严格按当前登录人员权限展示。
    ///
    /// :param tab: 当前 tab
    /// :param item: 当前数据项
    /// :param segment: 回款分段
    /// :param roles: 当前登录人员角色
    /// :param permissions: 当前登录人员权限
    /// :return: 操作列表
    static func actions(
        for tab: AppTab,
        item: JSONMap,
        segment: RepaymentSegment,
        roles: [String],
        permissions: [String]
    ) -> [AdminActionKind] {
        let status = statusValue(from: item)
        switch tab {
        case .profiles:
            var actions: [AdminActionKind] = []
            if hasPermission("user-location-risk-unlock", roles: roles, permissions: permissions), hasLoginDisplacementRisk(item) {
                actions.append(.unlockLocation)
            }
            if hasPermission("blacklist", roles: roles, permissions: permissions) {
                actions.append(blacklistAction(for: item))
            }
            if hasPermission("disbursements", roles: roles, permissions: permissions), item.int("current_loan_id") > 0, status == "CARD_REJECTED" {
                actions.append(.reissueCard)
            }
            if (hasPermission("users", roles: roles, permissions: permissions) || hasPermission("disbursements", roles: roles, permissions: permissions)),
               item.int("current_loan_id") > 0,
               ["WITHDRAWING", "CARD_REJECTED"].contains(status) {
                actions.append(.closeReissue)
            }
            return actions
        case .applications:
            var actions: [AdminActionKind] = []
            if hasPermission("applications", roles: roles, permissions: permissions), status == "REVIEWING" {
                actions.append(contentsOf: [.approve, .reject, .setCredit, .adjustCredit])
            }
            if hasPermission("applications", roles: roles, permissions: permissions) {
                actions.append(.saveNote)
            }
            if hasPermission("blacklist", roles: roles, permissions: permissions) {
                actions.append(blacklistAction(for: item))
            }
            return actions
        case .cards:
            var actions: [AdminActionKind] = []
            if hasPermission("disbursements", roles: roles, permissions: permissions), status == "WITHDRAWING" {
                actions.append(contentsOf: [.disburse, .rejectCard, .closeReissue])
            }
            if hasPermission("disbursements", roles: roles, permissions: permissions) {
                actions.append(.saveNote)
            }
            if hasPermission("blacklist", roles: roles, permissions: permissions) {
                actions.append(blacklistAction(for: item))
            }
            return actions
        case .repayments:
            var actions: [AdminActionKind] = []
            if hasPermission("collections", roles: roles, permissions: permissions), status == "OVERDUE" {
                actions.append(.collect)
            } else if hasPermission("repayments", roles: roles, permissions: permissions), status == "DISBURSED" {
                actions.append(.remind)
            }
            if hasPermission("repayments", roles: roles, permissions: permissions) || hasPermission("collections", roles: roles, permissions: permissions) {
                if item.int("repay_attempt_count") > 0 {
                    actions.append(.ack)
                }
                if ["DISBURSED", "OVERDUE"].contains(status) {
                    actions.append(.extend)
                }
            }
            let canAdjust = status == "OVERDUE"
                ? hasPermission("collections", roles: roles, permissions: permissions)
                : hasPermission("applications", roles: roles, permissions: permissions)
            if canAdjust, ["DISBURSED", "OVERDUE"].contains(status) {
                actions.append(.adjustCredit)
            }
            if hasPermission("blacklist", roles: roles, permissions: permissions) {
                actions.append(blacklistAction(for: item))
            }
            return actions
        case .finance:
            guard hasPermission("financials", roles: roles, permissions: permissions), ["DISBURSED", "OVERDUE"].contains(status) else {
                return []
            }
            return [.reconcile, .settle]
        }
    }

    /// 生成顶部摘要卡片文案。
    ///
    /// :param tab: 当前 tab
    /// :param stats: 综合统计
    /// :param repaymentStats: 回款统计
    /// :param overdueFilter: 回款/平账逾期筛选
    /// :return: 两张卡片内容
    static func summaryCards(
        for tab: AppTab,
        stats: JSONMap?,
        repaymentStats: JSONMap?,
        overdueFilter: OverdueFilter
    ) -> [SummaryCardContent] {
        let stats = stats ?? [:]
        let repaymentStats = repaymentStats ?? [:]
        switch tab {
        case .profiles:
            return [
                SummaryCardContent(title: "总档案", value: AppFormatter.number(stats.double("total_users")), subtitle: "全部注册客户")
                ,
                SummaryCardContent(title: "今日新增", value: AppFormatter.number(stats.double("today_new_users")), subtitle: "今天进入系统")
            ]
        case .applications:
            return [
                SummaryCardContent(title: "待审批", value: AppFormatter.number(stats.double("reviewing_loans")), subtitle: "需要核验资料")
                ,
                SummaryCardContent(title: "今日申请", value: AppFormatter.number(stats.double("today_applications")), subtitle: "当天提交")
            ]
        case .cards:
            return [
                SummaryCardContent(title: "待发卡", value: AppFormatter.number(stats.double("withdrawing_loans")), subtitle: "等待发卡订单")
                ,
                SummaryCardContent(title: "可用卡池", value: AppFormatter.number(stats.double("ecard_pool_available_count")), subtitle: "可用卡池金额 \(AppFormatter.currency(stats.double("ecard_pool_available_amount")))")
            ]
        case .repayments:
            if overdueFilter == .overdue {
                return [
                    SummaryCardContent(title: "累计逾期人数", value: AppFormatter.number(repaymentStats.double("overdue_user_count")), subtitle: "未转催收逾期客户")
                    ,
                    SummaryCardContent(title: "累计逾期金额", value: AppFormatter.currency(repaymentStats.double("overdue_amount")), subtitle: "未转催收逾期金额")
                ]
            }
            if overdueFilter == .notOverdue {
                return [
                    SummaryCardContent(title: "待回款人数", value: AppFormatter.number(repaymentStats.double("pending_repayment_user_count")), subtitle: "未到期且应回款非零")
                    ,
                    SummaryCardContent(title: "待回总金额", value: AppFormatter.currency(repaymentStats.double("pending_repayment_amount")), subtitle: "未到期待回金额")
                ]
            }
            return [
                SummaryCardContent(title: "今日回款进度", value: "\(AppFormatter.number(repaymentStats.double("due_today_actual_repayment_user_count")))/\(AppFormatter.number(repaymentStats.double("due_today_user_count")))", subtitle: "实际/应回款人数")
                ,
                SummaryCardContent(title: "今日回款金额", value: "\(AppFormatter.currency(repaymentStats.double("due_today_actual_repayment_amount")))/\(AppFormatter.currency(repaymentStats.double("due_today_amount")))", subtitle: "实际/应回款金额")
            ]
        case .finance:
            return [
                SummaryCardContent(title: "累计结清/部分结清订单", value: "\(AppFormatter.number(repaymentStats.double("settled_user_count")))/\(AppFormatter.number(repaymentStats.double("partial_repaid_unsettled_user_count")))", subtitle: "用户数")
                ,
                SummaryCardContent(title: "已收金额", value: AppFormatter.currency(repaymentStats.double("received_amount")), subtitle: "其他费用 \(AppFormatter.currency(repaymentStats.double("other_fee_amount")))")
            ]
        }
    }

    /// 生成列表用户卡片的两项核心信息，保持与安卓生产版一致。
    ///
    /// :param tab: 当前 tab
    /// :param item: 当前列表项
    /// :return: 卡片信息项，格式为标题和值
    static func listCardInfoCells(for tab: AppTab, item: JSONMap) -> [(String, String)] {
        [
            (listCardAmountLabel(for: tab), AppFormatter.currency(listCardAmount(for: item))),
            (listCardDateLabel(for: tab, item: item), listCardDateText(for: tab, item: item))
        ]
    }

    /// 生成列表用户卡片底部备注文案，保持与安卓生产版一致。
    ///
    /// :param item: 当前列表项
    /// :return: 备注文案
    static func listCardNoteText(for item: JSONMap) -> String {
        let note = item.string("product_name", fallback: item.string("review_note", fallback: item.string("collection_note")))
        return note.isEmpty ? "--" : note
    }

    private static func listCardAmountLabel(for tab: AppTab) -> String {
        if tab == .profiles { return "授信额度" }
        if tab == .cards { return "订单支付" }
        return "待处理金额"
    }

    private static func listCardAmount(for item: JSONMap) -> Double {
        let keys = ["remaining_repayment_amount", "product_total_price", "total_repayment_amount", "approved_credit_limit", "credit_limit", "approved_limit"]
        for key in keys {
            let value = item.double(key)
            if value > 0 {
                return value
            }
        }
        return 0
    }

    private static func listCardDateLabel(for tab: AppTab, item: JSONMap) -> String {
        if tab == .profiles { return "注册时间" }
        return item.string("due_date").isEmpty ? "提交时间" : "还款日"
    }

    private static func listCardDateText(for tab: AppTab, item: JSONMap) -> String {
        let raw: String
        if tab == .profiles {
            raw = item.string("created_at")
        } else {
            raw = item.string("due_date", fallback: item.string("application_submitted_at", fallback: item.string("created_at")))
        }
        return AppFormatter.simpleDate(raw)
    }

    /// 构造操作请求体。
    ///
    /// :param action: 操作类型
    /// :param item: 当前数据项
    /// :param inputText: 文本输入
    /// :param actualRepaymentDate: 实际还款日
    /// :return: JSON 请求体
    static func payload(
        for action: AdminActionKind,
        item: JSONMap,
        inputText: String,
        actualRepaymentDate: Date?
    ) -> JSONMap {
        let trimmed = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        switch action {
        case .approve:
            return [
                "approved": .bool(true),
                "credit_limit": .number(numberOr(trimmed, fallback: item.double("approved_credit_limit", fallback: 1000))),
                "approval_discount_amount": .number(0),
                "term_days": .number(Double(item.int("term_days", fallback: max(item.int("product_term_days", fallback: 7), 1)))),
                "review_note": .string("iOS 端审批通过")
            ]
        case .reject:
            return [
                "approved": .bool(false),
                "review_note": .string(trimmed.isEmpty ? "资料不符合要求" : trimmed)
            ]
        case .disburse:
            return [
                "term_days": .number(numberOr(trimmed, fallback: Double(max(item.int("term_days", fallback: item.int("product_term_days", fallback: 7)), 1))))
            ]
        case .rejectCard, .saveNote, .remind, .collect, .ack, .blacklist, .removeBlacklist, .unlockLocation, .reissueCard, .closeReissue, .refresh:
            if action == .saveNote {
                return ["review_note": .string(trimmed)]
            }
            return ["note": .string(trimmed.isEmpty ? action.title : trimmed)]
        case .reconcile:
            var payload: JSONMap = [
                "received_amount": .number(numberOr(trimmed, fallback: item.double("remaining_repayment_amount"))),
                "reduction_amount": .number(0),
                "other_fee_amount": .number(0),
                "note": .string("iOS 端登记平账")
            ]
            if let actualRepaymentDate {
                payload["actual_repayment_date"] = .string(Self.apiDateString(from: actualRepaymentDate))
            }
            return payload
        case .settle:
            return [:]
        case .extend:
            return [
                "extension_type": .string("FREE"),
                "days": .number(numberOr(trimmed, fallback: 3)),
                "reduction_amount": .number(0),
                "note": .string("iOS 端账单展期")
            ]
        case .adjustCredit:
            return [
                "amount": .number(numberOr(trimmed, fallback: 100)),
                "note": .string("iOS 端增加可用额度")
            ]
        case .setCredit:
            return [
                "credit_limit": .number(numberOr(trimmed, fallback: item.double("approved_credit_limit", fallback: 1000))),
                "note": .string("iOS 端调整授信")
            ]
        }
    }

    /// 解析操作接口路径和方法。
    ///
    /// :param action: 操作类型
    /// :param item: 当前数据项
    /// :return: 路径和方法
    static func endpoint(for action: AdminActionKind, item: JSONMap) -> (method: String, path: String)? {
        let loanID = item.int("id") != 0 ? item.int("id") : item.int("current_loan_id")
        let userID = item.int("user_id") != 0 ? item.int("user_id") : (item.int("owner_id") != 0 ? item.int("owner_id") : item.int("id"))
        switch action {
        case .approve, .reject:
            return ("POST", "/admin/loans/\(loanID)/review")
        case .disburse:
            return ("POST", "/admin/loans/\(loanID)/disburse")
        case .rejectCard:
            return ("POST", "/admin/loans/\(loanID)/reject-card")
        case .saveNote:
            return ("PATCH", "/admin/loans/\(loanID)")
        case .remind:
            return ("POST", "/admin/loans/\(loanID)/remind")
        case .collect:
            return ("POST", "/admin/loans/\(loanID)/collect")
        case .ack:
            return ("POST", "/admin/loans/\(loanID)/ack-repay-attempt")
        case .reconcile:
            return ("POST", "/admin/loans/\(loanID)/finance-reconcile")
        case .settle:
            return ("POST", "/admin/loans/\(loanID)/settle")
        case .extend:
            return ("POST", "/admin/loans/\(loanID)/extend")
        case .adjustCredit:
            return ("POST", "/admin/loans/\(loanID)/available-credit/adjust")
        case .setCredit:
            return ("POST", "/admin/loans/\(loanID)/approved-credit/set")
        case .blacklist:
            return ("POST", "/admin/users/\(userID)/blacklist")
        case .removeBlacklist:
            return ("POST", "/admin/users/\(userID)/blacklist/remove")
        case .unlockLocation:
            return ("POST", "/admin/users/\(userID)/location-risk/unlock")
        case .reissueCard:
            return ("POST", "/admin/loans/\(loanID)/reissue-card")
        case .closeReissue:
            return ("POST", "/admin/loans/\(loanID)/close-card-reissue")
        case .refresh:
            return nil
        }
    }

    /// 获取操作输入提示。
    ///
    /// :param action: 操作类型
    /// :return: 输入提示
    static func prompt(for action: AdminActionKind) -> String {
        switch action {
        case .approve:
            return "输入审批额度"
        case .disburse:
            return "输入账期天数"
        case .reconcile:
            return "输入登记收款金额"
        case .extend:
            return "输入展期天数"
        case .adjustCredit:
            return "输入增加额度"
        case .setCredit:
            return "输入授信额度"
        default:
            return "输入备注（可选）"
        }
    }

    private static func hasAny(_ roles: [String], expected: [String]) -> Bool {
        !Set(roles).isDisjoint(with: expected)
    }

    private static func hasPermission(_ permission: String, roles: [String], permissions: [String]) -> Bool {
        if roles.contains("ADMIN") { return true }
        if !permissions.isEmpty { return permissions.contains(permission) }
        if permission == "users" { return hasAny(roles, expected: ["REVIEW", "BUSINESS_CONSULTANT"]) }
        if permission == "applications" { return roles.contains("REVIEW") }
        if permission == "disbursements" || permission == "financials" { return roles.contains("FINANCE") }
        if permission == "repayments" { return roles.contains("REVIEW") }
        if permission == "collections" { return roles.contains("COLLECTION") }
        if permission == "blacklist" { return hasAny(roles, expected: ["REVIEW", "FINANCE", "COLLECTION"]) }
        return false
    }

    private static func statusValue(from item: JSONMap) -> String {
        item.string("status", fallback: item.string("current_loan_status")).uppercased()
    }

    private static func blacklistAction(for item: JSONMap) -> AdminActionKind {
        item.bool("blacklist_hit") || item.bool("user_blacklist_hit") || item.bool("current_blacklist_hit") ? .removeBlacklist : .blacklist
    }

    private static func hasLoginDisplacementRisk(_ item: JSONMap) -> Bool {
        guard item.bool("location_risk_blocked") else { return false }
        let reason = item.string("location_risk_reason")
        return reason.isEmpty || reason.contains("登录位置异常") || reason.contains("小时内") || reason.contains("公里")
    }

    private static func numberOr(_ value: String, fallback: Double) -> Double {
        Double(value) ?? fallback
    }

    /// 组合并清理地址展示文本，避免出现“国家省市 + 完整地址”重复。
    ///
    /// :param parts: 地址片段，通常为国家、省、市、区、详细地址
    /// :return: 去重后的地址文本
    static func normalizedAddress(parts: [String]) -> String {
        let cleaned = parts
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty && $0.lowercased() != "null" && $0 != "--" }
        guard !cleaned.isEmpty else { return "--" }
        guard let last = cleaned.last else { return "--" }
        let prefix = Array(cleaned.dropLast())
        if last.contains("/") {
            return last
        }
        if !prefix.isEmpty {
            let joinedPrefix = prefix.joined()
            if last.hasPrefix(joinedPrefix) {
                return last
            }
        }
        var result: [String] = []
        for part in cleaned {
            let compactPart = part.replacingOccurrences(of: "/", with: "")
            let alreadyCovered = result.contains { existing in
                let compactExisting = existing.replacingOccurrences(of: "/", with: "")
                return compactExisting == compactPart || compactPart.hasPrefix(compactExisting) || compactExisting.hasPrefix(compactPart)
            }
            if !alreadyCovered {
                result.append(part)
            }
        }
        return result.isEmpty ? "--" : result.joined()
    }

    private static func apiDateString(from value: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: value)
    }
}
