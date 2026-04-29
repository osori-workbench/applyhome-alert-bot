from applyhome_alert.filters import filter_target_announcements
from applyhome_alert.models import Announcement


def test_filter_keeps_only_capital_area_non_ranked_items() -> None:
    items = [
        Announcement(
            region="경기",
            category="무순위(사후)",
            name="A",
            provider="X",
            posted_on="2026-04-29",
            subscription_period="2026-05-04 ~ 2026-05-04",
            winner_date="2026-05-08",
            detail_url="https://example.com/a",
        ),
        Announcement(
            region="부산",
            category="무순위(사후)",
            name="B",
            provider="Y",
            posted_on="2026-04-29",
            subscription_period="2026-05-04 ~ 2026-05-04",
            winner_date="2026-05-08",
            detail_url="https://example.com/b",
        ),
        Announcement(
            region="서울",
            category="임의공급",
            name="C",
            provider="Z",
            posted_on="2026-04-29",
            subscription_period="2026-05-04 ~ 2026-05-04",
            winner_date="2026-05-08",
            detail_url="https://example.com/c",
        ),
    ]

    result = filter_target_announcements(items)

    assert [item.name for item in result] == ["A"]
