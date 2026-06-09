import json
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.services import admin_service
from app.schemas.risk import CompositeRiskReportResponse
from app.services.composite_risk_report import (
    build_composite_risk_payload_async,
    get_cached_composite_report_async,
    serialize_composite_risk_report,
    _json_default,
    _probe_result_label,
)
from app.services.risk_report import _build_empty_risk_result_payload, _is_empty_risk_result_message


class _FakeScalarResult:
    """模拟SQLAlchemy结果集。

    :param value: first返回值
    :param items: all返回值
    :return: 无返回值
    """

    def __init__(self, value=None, items=None):
        self.value = value
        self.items = items or []

    def unique(self):
        return self

    def scalars(self):
        return self

    def first(self):
        return self.value

    def all(self):
        return self.items


class _FakeDb:
    """按调用顺序返回综合报告构建所需数据。

    :param results: 预设结果列表
    :return: 无返回值
    """

    def __init__(self, results):
        self.results = list(results)

    async def execute(self, _stmt):
        return self.results.pop(0)


def _has_recommendation_key(value):
    """递归检查报告中是否存在建议动作字段。

    :param value: 待检查对象
    :return: 是否存在建议动作字段
    """
    if isinstance(value, dict):
        for key, item in value.items():
            if "建议动作" in str(key) or "recommend" in str(key).lower():
                return True
            if _has_recommendation_key(item):
                return True
    if isinstance(value, list):
        return any(_has_recommendation_key(item) for item in value)
    return False


def test_probe_result_label():
    """探针结果编码应转换为业务可读文案。

    :return: 无返回值
    """
    assert _probe_result_label("1") == "逾期未还款"
    assert _probe_result_label("2") == "正常履约"
    assert _probe_result_label("3") == "逾期后已还款"
    assert _probe_result_label("4") == "无法确认"
    assert _probe_result_label(None) == "未知"


def test_empty_risk_result_should_be_saved_as_report_payload():
    """风控接口无记录时不应阻断综合报告生成。

    :return: 无返回值
    """
    assert _is_empty_risk_result_message("查询数据为空") is True
    payload = _build_empty_risk_result_payload(
        {"code": 500, "msg": "查询数据为空", "requestId": "r1"},
        product_no="JX1000021",
        message="查询数据为空",
    )

    assert payload["code"] == 200
    assert payload["empty_result"] is True
    assert payload["data"] == {}
    assert payload["productNo"] == "JX1000021"


def test_composite_response_should_accept_legacy_null_fields():
    """历史综合报告存在空三要素或空时间时不应触发响应校验500。

    :return: 无返回值
    """
    report = SimpleNamespace(
        id=1,
        user_id=164,
        panorama_report_id=None,
        probe_a_report_id=None,
        probe_c_report_id=None,
        name=None,
        id_card=None,
        phone=None,
        report_json=None,
        query_time=None,
        created_at=None,
        updated_at=None,
    )

    payload = serialize_composite_risk_report(report)
    response = CompositeRiskReportResponse.model_validate(payload)

    assert response.user_id == 164
    assert response.name is None
    assert response.query_time is None


def test_composite_report_json_default_should_accept_date():
    """综合报告包含日期字段时应能正常写入JSON。

    :return: 无返回值
    """
    payload = {
        "due_date": date(2026, 6, 4),
        "created_at": datetime(2026, 6, 4, 14, 29, 25),
    }

    result = json.dumps(payload, ensure_ascii=False, default=_json_default)

    assert '"due_date": "2026-06-04"' in result
    assert '"created_at": "2026-06-04T14:29:25"' in result


@pytest.mark.asyncio
async def test_reviewing_cache_requires_probe_c_report():
    """审核中的当前用户只应复用探针C综合报告缓存。

    :return: 无返回值
    """
    old_probe_a_report = SimpleNamespace(id=1, report_json=json.dumps({"probe_a": {"source": "PROBE_A"}}))
    new_probe_c_report = SimpleNamespace(id=2, report_json=json.dumps({"probe_c": {"source": "PROBE_C"}}))
    db = _FakeDb([_FakeScalarResult(items=[old_probe_a_report, new_probe_c_report])])

    cached_report = await get_cached_composite_report_async(
        db,
        name="测试用户",
        id_card="440100199001010011",
        require_probe_c=True,
    )

    assert cached_report.id == new_probe_c_report.id


@pytest.mark.asyncio
async def test_non_reviewing_cache_keeps_existing_report():
    """非审核中的当前用户不主动刷新旧综合报告缓存。

    :return: 无返回值
    """
    old_probe_a_report = SimpleNamespace(id=1, report_json=json.dumps({"probe_a": {"source": "PROBE_A"}}))
    new_probe_c_report = SimpleNamespace(id=2, report_json=json.dumps({"probe_c": {"source": "PROBE_C"}}))
    db = _FakeDb([_FakeScalarResult(items=[old_probe_a_report, new_probe_c_report])])

    cached_report = await get_cached_composite_report_async(
        db,
        name="测试用户",
        id_card="440100199001010011",
        require_probe_c=False,
    )

    assert cached_report.id == old_probe_a_report.id


@pytest.mark.asyncio
async def test_composite_risk_payload_has_sources_without_recommendation_action():
    """综合风险报告应合并多来源数据且不输出建议动作。

    :return: 无返回值
    """
    now = datetime.now()
    user = SimpleNamespace(
        id=9,
        name="测试用户",
        phone="13900000000",
        id_card_num="440100199001010011",
        id_address="广东省广州市天河区",
        created_at=now,
        real_name_status="AUTHED",
        face_auth_status="PASSED",
        ocr_submitted_at=now,
        application_submitted_at=now,
        last_login_at=now,
        blacklist_hit=False,
        blacklist_reason=None,
        blacklist_checked_at=None,
        location_province="广东省",
        location_city="广州市",
        location_district="天河区",
        location_street="",
        location_address="广东省广州市天河区",
        location_risk_blocked=False,
        location_risk_reason=None,
        location_risk_at=None,
        available_credit_limit=1200,
        overdue_credit_locked=False,
    )
    loan = SimpleNamespace(
        id=21,
        user_id=user.id,
        owner=user,
        status="DISBURSED",
        credit_limit=1600,
        approved_credit_limit=1600,
        fee_rate=0,
        term_days=7,
        due_date=now,
        penalty_amount=0,
        repaid_amount=0,
        reduction_amount=0,
        product_name="京东E卡1000元 + 权益包",
        product_total_price=1600,
        rights_price=600,
        ecard_face_value=1000,
        created_at=now,
        disbursed_at=now,
    )
    event = SimpleNamespace(
        id=1,
        loan_id=loan.id,
        actor_type="USER",
        event_type="LOGIN",
        title="用户登录",
        detail="登录成功",
        ip="127.0.0.1",
        ip_country="中国",
        ip_province="广东省",
        ip_city="广州市",
        ip_district="天河区",
        ip_detail="广东省广州市天河区",
        lon_lat="23.1,113.3",
        lon_lat_country="中国",
        lon_lat_province="广东省",
        lon_lat_city="广州市",
        lon_lat_district="天河区",
        lon_lat_detail="广东省广州市天河区",
        created_at=now,
    )
    db = _FakeDb(
        [
            _FakeScalarResult(value=loan),
            _FakeScalarResult(items=[]),
            _FakeScalarResult(items=[]),
            _FakeScalarResult(items=[event]),
        ]
    )
    panorama_report = SimpleNamespace(
        id=1,
        source="PANORAMA",
        query_time=now,
        report_json=json.dumps(
            {
                "data": {
                    "apply_report_detail": {"A22160001": "80"},
                    "current_report_detail": {"C22180001": "2000"},
                }
            }
        ),
    )
    probe_c_report = SimpleNamespace(
        id=2,
        source="PROBE_C",
        query_time=now,
        report_json=json.dumps({"data": {"result_code": "2", "currently_performance": "3"}}),
    )

    payload = await build_composite_risk_payload_async(
        db,
        user=user,
        panorama_report=panorama_report,
        probe_c_report=probe_c_report,
    )

    assert payload["report_type"] == "XIAOHEBAO_RISK"
    assert payload["title"] == "小荷包风险报告"
    assert payload["panorama"]["source"] == "PANORAMA"
    assert "current_report_detail" not in payload["panorama"]["payload"]["data"]
    assert payload["probe_c"]["result_label"] == "正常履约"
    assert payload["latest_order"]["id"] == loan.id
    assert _has_recommendation_key(payload) is False


@pytest.mark.asyncio
async def test_composite_risk_report_should_mark_latest_loan_checked(monkeypatch):
    """查询小荷包风险报告后应记录当前审核员已查看报告。

    :return: 无返回值
    """
    now = datetime.now()
    user = SimpleNamespace(id=9, name="测试用户", id_card_num="440100199001010011")
    loan = SimpleNamespace(id=21, risk_report_checked_at=None, risk_report_checked_by=None)
    events = []

    async def _fake_get_user(_db, user_id):
        assert user_id == user.id
        return user

    async def _fake_get_report(_db, *, user):
        return SimpleNamespace(
            id=3,
            user_id=user.id,
            panorama_report_id=1,
            probe_c_report_id=2,
            name=user.name,
            id_card=user.id_card_num,
            phone="13900000000",
            report_json='{"title":"小荷包风险报告"}',
            query_time=now,
            created_at=now,
            updated_at=now,
        )

    async def _fake_get_latest_loan(_db, user_id):
        assert user_id == user.id
        return loan

    async def _fake_log_event(_db, **kwargs):
        events.append(kwargs)

    class _FakeDb:
        async def commit(self):
            return None

        async def refresh(self, _item):
            return None

    monkeypatch.setattr(admin_service, "ensure_any_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin_service, "get_user_for_risk_report_async", _fake_get_user)
    monkeypatch.setattr(admin_service, "get_or_create_composite_risk_report_async", _fake_get_report)
    monkeypatch.setattr(admin_service, "get_latest_loan_async", _fake_get_latest_loan)
    monkeypatch.setattr(admin_service, "log_user_event_async", _fake_log_event)

    result = await admin_service._get_composite_risk_report(
        _FakeDb(),
        SimpleNamespace(user_id=user.id),
        SimpleNamespace(username="review01"),
    )

    result_payload = json.loads(result["report_json"])
    assert result_payload["title"] == "小荷包风险报告"
    assert result_payload["report_type"] == "XIAOHEBAO_RISK"
    assert loan.risk_report_checked_at is not None
    assert loan.risk_report_checked_by == "review01"
    assert events[0]["title"] == "查询小荷包风险报告"
