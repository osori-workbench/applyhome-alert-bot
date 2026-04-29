from applyhome_alert.models import Announcement
from applyhome_alert.notifier import build_slack_message


def test_build_slack_message_includes_core_fields() -> None:
    item = Announcement(
        region="경기",
        category="무순위(사후)",
        name="힐스테이트 금오 더퍼스트",
        provider="조합",
        posted_on="2026-04-29",
        subscription_period="2026-05-04 ~ 2026-05-04",
        winner_date="2026-05-08",
        detail_url="https://example.com/a",
    )

    message = build_slack_message([item])

    assert "수도권 무순위 청약 알림" in message
    assert "힐스테이트 금오 더퍼스트" in message
    assert "https://example.com/a" in message
