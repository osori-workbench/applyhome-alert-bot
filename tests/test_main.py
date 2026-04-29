from applyhome_alert.main import process_announcements
from applyhome_alert.models import Announcement


class FakeStore:
    def __init__(self) -> None:
        self.seen: set[str] = set()

    def is_new(self, announcement: Announcement) -> bool:
        return announcement.dedupe_key not in self.seen

    def mark_sent(self, announcement: Announcement) -> None:
        self.seen.add(announcement.dedupe_key)


def test_process_announcements_filters_only_new_items_without_marking_them() -> None:
    store = FakeStore()
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
            house_manage_no="1",
            pblanc_no="1",
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
            house_manage_no="2",
            pblanc_no="2",
        ),
    ]

    result = process_announcements(items, store=store, include_immediate_supply=False)

    assert [item.name for item in result] == ["A"]
    assert store.is_new(result[0]) is True
