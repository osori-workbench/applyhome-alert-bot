from __future__ import annotations

from collections.abc import Iterable

from .config import Settings
from .fetcher import fetch_announcement_details, fetch_rows
from .filters import filter_target_announcements
from .models import Announcement
from .notifier import send_slack_notifications
from .parser import parse_rows
from .store import AnnouncementStore


def process_announcements(
    items: Iterable[Announcement],
    *,
    store: AnnouncementStore,
    include_immediate_supply: bool,
) -> list[Announcement]:
    filtered = filter_target_announcements(
        items,
        include_immediate_supply=include_immediate_supply,
    )
    return [item for item in filtered if store.is_new(item)]


def run(settings: Settings) -> list[Announcement]:
    store = AnnouncementStore(settings.db_path)
    announcements = parse_rows(fetch_rows())
    new_items = process_announcements(
        announcements,
        store=store,
        include_immediate_supply=settings.include_immediate_supply,
    )
    if not new_items:
        return []

    enriched_items = fetch_announcement_details(new_items)
    send_slack_notifications(
        settings.slack_webhook_url,
        enriched_items,
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
