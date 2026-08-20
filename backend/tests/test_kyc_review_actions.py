from app.schemas.admin import KycBatchReviewRequest, KycReviewActionRequest


def test_kyc_review_action_schema_accepts_single_action_and_note():
    payload = KycReviewActionRequest(action="APPROVE", note="资料核验通过")
    assert payload.action == "APPROVE"
    assert payload.note == "资料核验通过"


def test_kyc_batch_review_schema_limits_to_explicit_user_ids():
    payload = KycBatchReviewRequest(user_ids=[1, 2], action="REJECT")
    assert payload.user_ids == [1, 2]
