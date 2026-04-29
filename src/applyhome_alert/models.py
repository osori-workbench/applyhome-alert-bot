from __future__ import annotations

from dataclasses import dataclass


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
