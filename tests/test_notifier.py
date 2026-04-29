from datetime import date

from applyhome_alert.models import Announcement, AnnouncementDetail, SupplyItem
from applyhome_alert.notifier import build_parent_payload, build_thread_payloads


def make_announcement(
    *,
    name: str = "동탄신도시 금강펜테리움 6차 센트럴파크(A59BL)",
    posted_on: str = "2026-04-29",
    subscription_period: str = "2026-05-06",
    winner_date: str = "2026-05-11",
    sale_price: str = "48,660만원",
) -> Announcement:
    return Announcement(
        region="경기",
        category="무순위(사후)",
        name=name,
        provider="주식회사 펜테리움건설",
        posted_on=posted_on,
        subscription_period=subscription_period,
        winner_date=winner_date,
        detail_url=f"https://example.com/{name}",
        house_manage_no="2026930013",
        pblanc_no="2026930013",
        detail=AnnouncementDetail(
            supply_location="경기도 화성시 동탄구 신동 822",
            supply_scale="1세대",
            notice_url="https://example.com/notice.pdf",
            contract_date="2026-05-15 ~ 2026-05-15",
            move_in_month="2026.06",
            supply_items=(
                SupplyItem(housing_type="084.7576A", supply_units="1", sale_price=sale_price, note="", move_in_month="2026.06"),
            ),
        ),
    )


def make_inquiry_announcement() -> Announcement:
    return Announcement(
        region="경기",
        category="무순위(사후)",
        name="힐스테이트 금오 더퍼스트",
        provider="금오생활권1구역주택재개발정비사업조합",
        posted_on="2026-04-29",
        subscription_period="2026-05-04 ~ 2026-05-04",
        winner_date="2026-05-08",
        detail_url="https://example.com/detail",
        house_manage_no="2026910103",
        pblanc_no="2026910103",
        detail=AnnouncementDetail(
            supply_location="경기도 의정부시 금오동 65-3번지 일원",
            supply_scale="1세대",
            notice_url="https://example.com/notice-inquiry.pdf",
            contract_date="2026-05-12 ~ 2026-05-12",
            move_in_month="2026.06",
            supply_items=(
                SupplyItem(
                    housing_type="036.1818",
                    supply_units="1",
                    sale_price="사업주체 문의",
                    note="공급금액 : 사업주체 문의",
                    move_in_month="2026.06",
                ),
            ),
        ),
    )


def make_today_announcement(
    *,
    name: str = "이안 센트럴 제기동역",
    subscription_period: str = "2026-04-29 ~ 2026-04-29",
) -> Announcement:
    return Announcement(
        region="서울",
        category="임의공급",
        name=name,
        provider="공성아파트 소규모재건축사업조합",
        posted_on="2026-04-27",
        subscription_period=subscription_period,
        winner_date="2026-05-06",
        detail_url="https://example.com/today",
    )


def test_build_parent_payload_includes_today_summary_directly_in_top_level_blocks() -> None:
    payload = build_parent_payload(
        [make_announcement()],
        today_items=[make_today_announcement()],
        today=date(2026, 4, 29),
    )

    text_blocks = [block.get("text", {}).get("text", "") for block in payload["blocks"] if isinstance(block, dict)]
    merged_text = "\n".join(text_blocks)
    assert "오늘 청약 공고 요약" in merged_text
    assert "2026-04-29 기준" in merged_text
    assert "*지역* | *구분* | *주택명* | *청약기간*" in merged_text
    assert "서울 | 임의공급 | <https://example.com/today|이안 센트럴 제기동역> | 2026-04-29 ~ 2026-04-29" in merged_text
    assert "attachments" not in payload


def test_build_parent_payload_keeps_new_items_below_today_summary_in_top_level_blocks() -> None:
    payload = build_parent_payload(
        [make_announcement(name="내일 청약")],
        today_items=[make_today_announcement(name="오늘 청약")],
        today=date(2026, 4, 29),
    )

    top_level_text = "\n".join(
        block.get("text", {}).get("text", "")
        for block in payload["blocks"]
        if isinstance(block, dict)
    )

    assert top_level_text.index("오늘 청약 공고 요약") < top_level_text.index("*지역* | *구분* | *주택명* | *청약기간*")
    assert top_level_text.index("오늘 청약") < top_level_text.index("내일 청약")


def test_build_parent_payload_removes_new_summary_and_bolds_cheapest_price() -> None:
    payload = build_parent_payload([make_announcement()], today_items=[], today=date(2026, 4, 29))

    merged = "\n".join(
        block.get("text", {}).get("text", "")
        for block in payload["blocks"]
        if isinstance(block, dict)
    )

    assert "새로운 수도권 무순위/임의공급 공고를 감지했습니다." not in merged
    assert "동탄신도시 금강펜테리움 6차 센트럴파크(A59BL)" in merged
    assert "청약홈 바로가기" in merged
    assert "공급위치" in merged
    assert "경기도 화성시 동탄구 신동 822" in merged
    assert "공고일: 2026-04-29" in merged
    assert "*최저 분양가:* *48,660만원*" in merged


def test_build_parent_payload_sorts_new_items_by_nearest_subscription_date() -> None:
    soon = make_announcement(name="오늘 청약", subscription_period="2026-04-29 ~ 2026-04-29")
    later = make_announcement(name="다음 주 청약", subscription_period="2026-05-06 ~ 2026-05-06")
    middle = make_announcement(name="내일 청약", subscription_period="2026-04-30 ~ 2026-04-30")

    payload = build_parent_payload([later, middle, soon], today_items=[], today=date(2026, 4, 29))
    top_level_text = "\n".join(
        block.get("text", {}).get("text", "")
        for block in payload["blocks"]
        if isinstance(block, dict)
    )

    assert top_level_text.index("오늘 청약") < top_level_text.index("내일 청약") < top_level_text.index("다음 주 청약")


def test_build_thread_payloads_include_supply_rows() -> None:
    payloads = build_thread_payloads([make_announcement()])

    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["text"].startswith("상세 공급내역")
    text = "\n".join(block.get("text", {}).get("text", "") for block in payload["blocks"] if isinstance(block, dict))
    assert "청약홈 입주자모집공고" in text
    assert "주택형" in text
    assert "084.7576A" in text
    assert "48,660만원" in text


def test_build_thread_payloads_explain_inquiry_prices() -> None:
    payloads = build_thread_payloads([make_inquiry_announcement()])

    assert len(payloads) == 1
    payload_text = str(payloads[0])
    assert "사업주체 문의" in payload_text
    assert "청약홈 상세 페이지 기준" in payload_text
