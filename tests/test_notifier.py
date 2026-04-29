from applyhome_alert.models import Announcement, AnnouncementDetail, SupplyItem
from applyhome_alert.notifier import build_parent_payload, build_thread_payloads


def make_announcement() -> Announcement:
    return Announcement(
        region="경기",
        category="무순위(사후)",
        name="동탄신도시 금강펜테리움 6차 센트럴파크(A59BL)",
        provider="주식회사 펜테리움건설",
        posted_on="2026-04-29",
        subscription_period="2026-05-06",
        winner_date="2026-05-11",
        detail_url="https://example.com/a",
        house_manage_no="2026930013",
        pblanc_no="2026930013",
        detail=AnnouncementDetail(
            supply_location="경기도 화성시 동탄구 신동 822",
            supply_scale="1세대",
            notice_url="https://example.com/notice.pdf",
            contract_date="2026-05-15 ~ 2026-05-15",
            move_in_month="2026.06",
            supply_items=(
                SupplyItem(housing_type="084.7576A", supply_units="1", sale_price="48,660만원", note="", move_in_month="2026.06"),
            ),
        ),
    )


def test_build_parent_payload_includes_summary_and_blocks() -> None:
    payload = build_parent_payload([make_announcement()])

    assert payload["text"].startswith("수도권 무순위 청약 알림")
    blocks = payload["blocks"]
    block_text = "\n".join(block.get("text", {}).get("text", "") for block in blocks if isinstance(block, dict))
    assert "동탄신도시 금강펜테리움 6차 센트럴파크(A59BL)" in block_text
    assert "최저 분양가" in block_text
    assert "48,660만원" in block_text


def test_build_thread_payloads_include_supply_rows() -> None:
    payloads = build_thread_payloads([make_announcement()])

    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["text"].startswith("상세 공급내역")
    text = "\n".join(block.get("text", {}).get("text", "") for block in payload["blocks"] if isinstance(block, dict))
    assert "주택형" in text
    assert "084.7576A" in text
    assert "48,660만원" in text
