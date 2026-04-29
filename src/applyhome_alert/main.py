from __future__ import annotations

from collections.abc import Iterable

from .config import Settings
from .fetcher import fetch_rows
from .filters import filter_target_announcements
from .models import Announcement
from .notifier import build_slack_message, send_slack_webhook
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
    new_items = [item for item in filtered if store.is_new(item)]
    for item in new_items:
        store.mark_sent(item)
    return new_items


def run(settings: Settings) -> list[Announcement]:
    store = AnnouncementStore(settings.db_path)
    announcements = parse_rows(fetch_rows())
    new_items = process_announcements(
        announcements,
        store=store,
        include_immediate_supply=settings.include_immediate_supply,
    )
    if new_items:
        send_slack_webhook(
            settings.slack_webhook_url,
            build_slack_message(new_items),
        )
    return new_items


def main() -> int:
    settings = Settings.from_env()
    run(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
