from __future__ import annotations

from dataclasses import dataclass, field, replace
import re
from typing import Self

_PRICE_RE = re.compile(r"(\d[\d,]*)")


@dataclass(frozen=True)
class SupplyItem:
    housing_type: str
    supply_units: str
    sale_price: str
    note: str = ""
    move_in_month: str = ""

    @property
    def price_value(self) -> int | None:
        match = _PRICE_RE.search(self.sale_price)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))


@dataclass(frozen=True)
class AnnouncementDetail:
    supply_location: str
    supply_scale: str
    notice_url: str | None
    contract_date: str
    move_in_month: str
    supply_items: tuple[SupplyItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Announcement:
    region: str
    category: str
    name: str
    provider: str
    posted_on: str
    subscription_period: str
    winner_date: str
    detail_url: str
    house_manage_no: str = ""
    pblanc_no: str = ""
    detail: AnnouncementDetail | None = None

    @property
    def dedupe_key(self) -> str:
        return "|".join(
            [
                self.region,
                self.category,
                self.name,
                self.posted_on,
                self.subscription_period,
            ]
        )

    @property
    def cheapest_supply_item(self) -> SupplyItem | None:
        if not self.detail:
            return None
        priced_items = [item for item in self.detail.supply_items if item.price_value is not None]
        if priced_items:
            return min(priced_items, key=lambda item: item.price_value or 0)
        return self.detail.supply_items[0] if self.detail.supply_items else None

    @property
    def cheapest_price_summary(self) -> str:
        cheapest_item = self.cheapest_supply_item
        if cheapest_item is None:
            return "정보 없음"
        return cheapest_item.sale_price or "정보 없음"

    def with_detail(self, detail: AnnouncementDetail) -> Self:
        return replace(self, detail=detail)
