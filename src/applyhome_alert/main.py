from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from .config import Settings
from .fetcher import fetch_announcement_details, fetch_rows
from .filters import filter_target_announcements, select_today_open_announcements
from .models import Announcement
from .notifier import send_slack_notifications
from .parser import parse_rows
from .store import AnnouncementStore


def process_announcements(
    items: Iterable[Announcement],
    *,
    store: AnnouncementStore,
    include_immediate_supply: bool,
    today: date | None = None,
) -> list[Announcement]:
    filtered = filter_target_announcements(
        items,
        include_immediate_supply=include_immediate_supply,
        today=today,
    )
    return [item for item in filtered if store.is_new(item)]


def run(settings: Settings, *, today: date | None = None) -> list[Announcement]:
    effective_today = today or date.today()
    store = AnnouncementStore(settings.db_path)
    announcements = parse_rows(fetch_rows())
    filtered = filter_target_announcements(
        announcements,
        include_immediate_supply=settings.include_immediate_supply,
        today=effective_today,
    )
    today_items = select_today_open_announcements(filtered, today=effective_today)
    new_items = [item for item in filtered if store.is_new(item)]

    if not new_items and not today_items:
        return []

    enriched_items = fetch_announcement_details(new_items)
    send_slack_notifications(
        settings.slack_webhook_url,
        enriched_items,
        today_items=today_items,
        today=effective_today,
        bot_token=settings.slack_bot_token,
        channel_id=settings.slack_channel_id,
    )
    for item in enriched_items:
        store.mark_sent(item)
    return enriched_items


def main() -> int:
    settings = Settings.from_env()
    run(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
