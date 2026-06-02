import XCTest
@testable import XiaoHeBaoIOS

final class WorkspaceLogicTests: XCTestCase {
    func testVisibleTabsShouldRespectRoles() {
        let reviewTabs = WorkspaceLogic.visibleTabs(for: ["REVIEW"])
        XCTAssertEqual(reviewTabs, [.profiles, .applications, .repayments])

        let financeTabs = WorkspaceLogic.visibleTabs(for: ["FINANCE"])
        XCTAssertEqual(financeTabs, [.cards, .finance])
    }

    func testVisibleTabsShouldPreferExplicitPermissions() {
        let tabs = WorkspaceLogic.visibleTabs(for: ["REVIEW"], permissions: ["users", "financials"])
        XCTAssertEqual(tabs, [.profiles, .finance])
    }

    func testRepaymentScopeShouldStayInRepaymentWorkQueue() {
        XCTAssertEqual(WorkspaceLogic.scope(for: .repayments, segment: .repayments), "REPAYMENTS")
        XCTAssertEqual(WorkspaceLogic.scope(for: .repayments, segment: .overdue), "REPAYMENTS")
    }

    func testReconcilePayloadShouldKeepCurrentContract() {
        let item: JSONMap = [
            "remaining_repayment_amount": .number(1600)
        ]
        let payload = WorkspaceLogic.payload(for: .reconcile, item: item, inputText: "1600", actualRepaymentDate: nil)
        XCTAssertEqual(payload["received_amount"]?.doubleValue, 1600)
        XCTAssertEqual(payload["reduction_amount"]?.doubleValue, 0)
        XCTAssertEqual(payload["other_fee_amount"]?.doubleValue, 0)
    }

    func testEndpointShouldResolveLoanAndUserActions() {
        let item: JSONMap = [
            "id": .number(9),
            "user_id": .number(8)
        ]
        XCTAssertEqual(WorkspaceLogic.endpoint(for: .settle, item: item)?.path, "/admin/loans/9/settle")
        XCTAssertEqual(WorkspaceLogic.endpoint(for: .blacklist, item: item)?.path, "/admin/users/8/blacklist")
    }

    func testSummaryCardsShouldRespectNotOverdueRepaymentMetrics() {
        let repaymentStats: JSONMap = [
            "pending_repayment_user_count": .number(6),
            "pending_repayment_amount": .number(3200)
        ]

        let cards = WorkspaceLogic.summaryCards(
            for: .repayments,
            stats: nil,
            repaymentStats: repaymentStats,
            overdueFilter: .notOverdue
        )

        XCTAssertEqual(cards.first?.title, "待回款人数")
        XCTAssertEqual(cards.first?.value, "6")
        XCTAssertEqual(cards.first?.subtitle, "未到期且应回款非零")
        XCTAssertEqual(cards.last?.title, "待回总金额")
        XCTAssertEqual(cards.last?.value, "¥3,200")
        XCTAssertEqual(cards.last?.subtitle, "未到期待回金额")
    }

    func testSummaryCardsShouldMatchAndroidWorkspaceMetrics() {
        let stats: JSONMap = [
            "total_users": .number(18),
            "today_new_users": .number(2),
            "reviewing_loans": .number(5),
            "today_applications": .number(3)
        ]

        let profileCards = WorkspaceLogic.summaryCards(
            for: .profiles,
            stats: stats,
            repaymentStats: nil,
            overdueFilter: .all
        )
        XCTAssertEqual(profileCards.map(\.title), ["总档案", "今日新增"])
        XCTAssertEqual(profileCards.map(\.value), ["18", "2"])
        XCTAssertEqual(profileCards.map(\.subtitle), ["全部注册客户", "今天进入系统"])

        let applicationCards = WorkspaceLogic.summaryCards(
            for: .applications,
            stats: stats,
            repaymentStats: nil,
            overdueFilter: .all
        )
        XCTAssertEqual(applicationCards.map(\.title), ["待审批", "今日申请"])
        XCTAssertEqual(applicationCards.map(\.value), ["5", "3"])
        XCTAssertEqual(applicationCards.map(\.subtitle), ["需要核验资料", "当天提交"])
    }

    func testSummaryCardsShouldRespectRepaymentOverdueAndAllMetrics() {
        let repaymentStats: JSONMap = [
            "overdue_user_count": .number(7),
            "overdue_amount": .number(8600),
            "due_today_actual_repayment_user_count": .number(2),
            "due_today_user_count": .number(3),
            "due_today_actual_repayment_amount": .number(1200),
            "due_today_amount": .number(1800)
        ]

        let overdueCards = WorkspaceLogic.summaryCards(
            for: .repayments,
            stats: nil,
            repaymentStats: repaymentStats,
            overdueFilter: .overdue
        )
        XCTAssertEqual(overdueCards.map(\.title), ["累计逾期人数", "累计逾期金额"])
        XCTAssertEqual(overdueCards.map(\.value), ["7", "¥8,600"])

        let allCards = WorkspaceLogic.summaryCards(
            for: .repayments,
            stats: nil,
            repaymentStats: repaymentStats,
            overdueFilter: .all
        )
        XCTAssertEqual(allCards.map(\.title), ["今日回款进度", "今日回款金额"])
        XCTAssertEqual(allCards.map(\.value), ["2/3", "¥1,200/¥1,800"])
    }

    func testApplicationFilterTitlesShouldUseFullAndroidLabels() {
        XCTAssertEqual(ApplicationStatusFilter.reviewing.title, "审核中")
        XCTAssertEqual(ApplicationStatusFilter.approved.title, "已通过")
        XCTAssertEqual(ApplicationStatusFilter.rejected.title, "未通过")
    }

    func testListCardInfoCellsShouldMatchAndroidProductionCard() {
        let repaymentItem: JSONMap = [
            "remaining_repayment_amount": .number(1680),
            "due_date": .string("2026-06-01T10:00:00"),
            "actual_repayment_date": .string("2026-06-02")
        ]
        let repaymentCells = WorkspaceLogic.listCardInfoCells(for: .repayments, item: repaymentItem)
        XCTAssertEqual(repaymentCells.map { $0.0 }, ["待处理金额", "还款日"])
        XCTAssertEqual(repaymentCells.map { $0.1 }, ["¥1,680", "2026-06-01"])

        let cardItem: JSONMap = [
            "product_total_price": .number(1200),
            "application_submitted_at": .string("2026-05-31 09:15:00")
        ]
        let cardCells = WorkspaceLogic.listCardInfoCells(for: .cards, item: cardItem)
        XCTAssertEqual(cardCells.map { $0.0 }, ["订单支付", "提交时间"])
        XCTAssertEqual(cardCells.map { $0.1 }, ["¥1,200", "2026-05-31"])
    }

    func testActionsShouldRespectLocationRiskPermission() {
        let item: JSONMap = [
            "id": .number(8),
            "location_risk_blocked": .bool(true),
            "location_risk_reason": .string("4小时内位移超过阈值")
        ]

        let withoutPermission = WorkspaceLogic.actions(
            for: .profiles,
            item: item,
            segment: .repayments,
            roles: ["REVIEW"],
            permissions: ["users"]
        )
        XCTAssertFalse(withoutPermission.contains(.unlockLocation))

        let withPermission = WorkspaceLogic.actions(
            for: .profiles,
            item: item,
            segment: .repayments,
            roles: ["REVIEW"],
            permissions: ["users", "user-location-risk-unlock"]
        )
        XCTAssertTrue(withPermission.contains(.unlockLocation))
    }

    func testActionsShouldMatchFinanceTab() {
        let item: JSONMap = ["status": .string("DISBURSED")]
        let actions = WorkspaceLogic.actions(
            for: .finance,
            item: item,
            segment: .repayments,
            roles: ["FINANCE"],
            permissions: ["financials"]
        )
        XCTAssertEqual(actions, [.reconcile, .settle])
    }

    func testNormalizedAddressShouldRemoveRepeatedAdministrativePrefix() {
        let value = WorkspaceLogic.normalizedAddress(parts: [
            "中国",
            "广东",
            "深圳",
            "中国/广东/深圳"
        ])

        XCTAssertEqual(value, "中国/广东/深圳")
    }

    func testNormalizedAddressShouldKeepDetailedGpsAddressOnce() {
        let value = WorkspaceLogic.normalizedAddress(parts: [
            "广东省",
            "深圳市",
            "南山区",
            "广东省深圳市南山区科技园"
        ])

        XCTAssertEqual(value, "广东省深圳市南山区科技园")
    }
}
