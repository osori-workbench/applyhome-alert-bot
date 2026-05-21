from applyhome_alert.models import Announcement, AnnouncementDetail, SupplyItem


def test_announcement_compatibility_aliases_expose_title_and_detail_data() -> None:
    detail = AnnouncementDetail(
        supply_location="경기 의정부시",
        supply_scale="아파트 1세대",
        notice_url="https://www.applyhome.co.kr/notice/1",
        contract_date="2026-05-15 ~ 2026-05-15",
        move_in_month="2026.06",
        supply_items=(SupplyItem(housing_type="084.7576A", supply_units="1", sale_price="48,660만원"),),
    )
    announcement = Announcement(
        region="경기",
        category="무순위(사후)",
        name="힐스테이트 금오 더퍼스트",
        provider="금오생활권1구역주택재개발정비사업조합",
        posted_on="2026-04-29",
        subscription_period="2026-05-04 ~ 2026-05-04",
        winner_date="2026-05-08",
        detail_url="https://www.applyhome.co.kr/detail/1",
        house_manage_no="2026910103",
        pblanc_no="2026910103",
        detail=detail,
    )

    assert announcement.title == announcement.name
    assert announcement.detail_data == detail
    assert announcement.supply_items == detail.supply_items
