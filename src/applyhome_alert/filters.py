from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date

from .models import Announcement

CAPITAL_REGIONS = {"서울", "경기", "인천"}
DEFAULT_TARGET_CATEGORIES = {"무순위(사전)", "무순위(사후)"}


def filter_target_announcements(
    items: Iterable[Announcement],
    *,
    include_immediate_supply: bool = False,
    today: date | None = None,
) -> list[Announcement]:
    target_categories = set(DEFAULT_TARGET_CATEGORIES)
    if include_immediate_supply:
        target_categories.add("임의공급")

    effective_today = today or date.today()

    return [
        item
        for item in items
        if item.region in CAPITAL_REGIONS
        and item.category in target_categories
        and item.subscription_end_date >= effective_today
    ]


def select_today_open_announcements(items: Sequence[Announcement], *, today: date | None = None) -> list[Announcement]:
    effective_today = today or date.today()
    return [item for item in items if item.is_open_on(effective_today)]
