from __future__ import annotations

from collections.abc import Iterable

from .models import Announcement

CAPITAL_REGIONS = {"서울", "경기", "인천"}
DEFAULT_TARGET_CATEGORIES = {"무순위(사전)", "무순위(사후)"}


def filter_target_announcements(
    items: Iterable[Announcement],
    *,
    include_immediate_supply: bool = False,
) -> list[Announcement]:
    target_categories = set(DEFAULT_TARGET_CATEGORIES)
    if include_immediate_supply:
        target_categories.add("임의공급")

    return [
        item
        for item in items
        if item.region in CAPITAL_REGIONS and item.category in target_categories
    ]
