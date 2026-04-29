from applyhome_alert.models import Announcement
from applyhome_alert.store import AnnouncementStore


def test_store_marks_only_new_announcement(tmp_path) -> None:
    store = AnnouncementStore(tmp_path / "alerts.db")
    item = Announcement(
        region="경기",
        category="무순위(사후)",
        name="A",
        provider="X",
        posted_on="2026-04-29",
        subscription_period="2026-05-04 ~ 2026-05-04",
        winner_date="2026-05-08",
        detail_url="https://example.com/a",
    )

    assert store.is_new(item) is True
    store.mark_sent(item)
    assert store.is_new(item) is False
