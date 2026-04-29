from datetime import date

import pytest

from applyhome_alert.config import Settings
from applyhome_alert.main import process_announcements, run
from applyhome_alert.models import Announcement


class FakeStore:
    def __init__(self) -> None:
        self.seen: set[str] = set()

    def is_new(self, announcement: Announcement) -> bool:
        return announcement.dedupe_key not in self.seen

    def mark_sent(self, announcement: Announcement) -> None:
        self.seen.add(announcement.dedupe_key)


class SeenStore(FakeStore):
    def __init__(self, items: list[Announcement]) -> None:
        super().__init__()
        self.seen = {item.dedupe_key for item in items}


def make_announcement(
    *,
    name: str,
    region: str = "경기",
    category: str = "무순위(사후)",
    subscription_period: str = "2026-05-04 ~ 2026-05-04",
) -> Announcement:
    return Announcement(
        region=region,
        category=category,
        name=name,
        provider="X",
        posted_on="2026-04-29",
        subscription_period=subscription_period,
        winner_date="2026-05-08",
        detail_url=f"https://example.com/{name}",
        house_manage_no=name,
        pblanc_no=name,
    )


def test_process_announcements_filters_only_new_items_without_marking_them() -> None:
    store = FakeStore()
    items = [
        make_announcement(name="A"),
        make_announcement(name="B", region="부산"),
    ]

    result = process_announcements(items, store=store, include_immediate_supply=False, today=date(2026, 4, 29))

    assert [item.name for item in result] == ["A"]
    assert store.is_new(result[0]) is True


def test_run_sends_today_summary_even_when_no_new_items(monkeypatch: pytest.MonkeyPatch) -> None:
    today_item = make_announcement(
        name="이안 센트럴 제기동역",
        region="서울",
        category="임의공급",
        subscription_period="2026-04-29 ~ 2026-04-29",
    )
    settings = Settings(slack_webhook_url="https://hooks.slack.com/services/test", include_immediate_supply=True)
    sent_calls: list[dict] = []

    monkeypatch.setattr("applyhome_alert.main.fetch_rows", lambda: [
        {
            "region": today_item.region,
            "category": today_item.category,
            "name": today_item.name,
            "provider": today_item.provider,
            "posted_on": today_item.posted_on,
            "subscription_period": today_item.subscription_period,
            "winner_date": today_item.winner_date,
            "detail_url": today_item.detail_url,
            "house_manage_no": today_item.house_manage_no,
            "pblanc_no": today_item.pblanc_no,
        }
    ])
    monkeypatch.setattr("applyhome_alert.main.fetch_announcement_details", lambda items: items)
    monkeypatch.setattr("applyhome_alert.main.AnnouncementStore", lambda _: SeenStore([today_item]))

    def fake_send(webhook_url, items, **kwargs):
        sent_calls.append({"webhook_url": webhook_url, "items": items, **kwargs})

    monkeypatch.setattr("applyhome_alert.main.send_slack_notifications", fake_send)

    result = run(settings, today=date(2026, 4, 29))

    assert result == []
    assert len(sent_calls) == 1
    assert sent_calls[0]["items"] == []
    assert [item.name for item in sent_calls[0]["today_items"]] == ["이안 센트럴 제기동역"]
