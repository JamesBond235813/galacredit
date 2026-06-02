import Foundation

enum AppTab: String, CaseIterable, Hashable {
    case profiles
    case applications
    case cards
    case repayments
    case finance

    var title: String {
        switch self {
        case .profiles:
            return "档案"
        case .applications:
            return "申请"
        case .cards:
            return "发卡"
        case .repayments:
            return "回款"
        case .finance:
            return "平账"
        }
    }

    var iconName: String {
        switch self {
        case .profiles:
            return "person.text.rectangle"
        case .applications:
            return "checklist"
        case .cards:
            return "creditcard"
        case .repayments:
            return "arrow.uturn.backward.circle"
        case .finance:
            return "banknote"
        }
    }
}

enum RepaymentSegment: String, CaseIterable {
    case repayments = "REPAYMENTS"
    case overdue = "OVERDUE"

    var title: String {
        switch self {
        case .repayments:
            return "当日还款"
        case .overdue:
            return "逾期催收"
        }
    }
}

enum OverdueFilter: String, CaseIterable {
    case all = "ALL"
    case overdue = "OVERDUE"
    case notOverdue = "NOT_OVERDUE"

    var title: String {
        switch self {
        case .all:
            return "全部"
        case .overdue:
            return "已逾期"
        case .notOverdue:
            return "未逾期"
        }
    }
}

enum ApplicationStatusFilter: String, CaseIterable {
    case reviewing = "REVIEWING"
    case approved = "APPROVED"
    case rejected = "REJECTED"
    case all = "ALL"

    var title: String {
        switch self {
        case .reviewing:
            return "审核中"
        case .approved:
            return "已通过"
        case .rejected:
            return "未通过"
        case .all:
            return "全部"
        }
    }
}

enum AdminActionKind: String, Hashable, CaseIterable {
    case approve
    case reject
    case disburse
    case rejectCard = "reject-card"
    case saveNote = "save-note"
    case remind
    case collect
    case ack
    case reconcile
    case settle
    case extend
    case adjustCredit = "adjust-credit"
    case setCredit = "set-credit"
    case blacklist
    case removeBlacklist = "remove-blacklist"
    case unlockLocation = "unlock-location"
    case reissueCard = "reissue-card"
    case closeReissue = "close-reissue"
    case refresh

    var title: String {
        switch self {
        case .approve:
            return "审批通过"
        case .reject:
            return "审批拒绝"
        case .disburse:
            return "确认发卡"
        case .rejectCard:
            return "拒绝发卡"
        case .saveNote:
            return "保存备注"
        case .remind:
            return "登记提醒"
        case .collect:
            return "登记催收"
        case .ack:
            return "确认还款申请"
        case .reconcile:
            return "登记平账"
        case .settle:
            return "确认结清"
        case .extend:
            return "账单展期"
        case .adjustCredit:
            return "增加可用额度"
        case .setCredit:
            return "调整授信"
        case .blacklist:
            return "一键拉黑"
        case .removeBlacklist:
            return "移出黑名单"
        case .unlockLocation:
            return "解除位移风控"
        case .reissueCard:
            return "开启二次发卡"
        case .closeReissue:
            return "退回待下单"
        case .refresh:
            return "刷新档案"
        }
    }

    var isDanger: Bool {
        self == .blacklist || self == .reject || self == .rejectCard
    }
}

struct SummaryCardContent: Hashable {
    let title: String
    let value: String
    let subtitle: String
}

extension AdminActionKind: Identifiable {
    var id: String { rawValue }
}

struct IdentifiedJSONItem: Identifiable, Hashable {
    let id = UUID()
    let value: JSONMap
}
