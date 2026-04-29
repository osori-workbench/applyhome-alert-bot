from __future__ import annotations

from collections.abc import Iterable

from .models import Announcement


def parse_row(row: dict[str, str]) -> Announcement:
    return Announcement(
        region=row["region"].strip(),
        category=row["category"].strip(),
        name=row["name"].strip(),
        provider=row["provider"].strip(),
        posted_on=row["posted_on"].strip(),
        subscription_period=row["subscription_period"].strip(),
        winner_date=row["winner_date"].strip(),
        detail_url=row["detail_url"].strip(),
    )


def parse_rows(rows: Iterable[dict[str, str]]) -> list[Announcement]:
    return [parse_row(row) for row in rows]
