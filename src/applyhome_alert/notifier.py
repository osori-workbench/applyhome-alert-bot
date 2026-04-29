from __future__ import annotations

from collections.abc import Sequence

import requests

from .models import Announcement


def build_slack_message(items: Sequence[Announcement]) -> str:
    lines = ["[수도권 무순위 청약 알림]", ""]
    for item in items:
        lines.extend(
            [
                f"- 지역: {item.region}",
                f"- 구분: {item.category}",
                f"- 단지명: {item.name}",
                f"- 시행사: {item.provider}",
                f"- 공고일: {item.posted_on}",
                f"- 청약기간: {item.subscription_period}",
                f"- 당첨자발표: {item.winner_date}",
                f"- 링크: {item.detail_url}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def send_slack_webhook(webhook_url: str, message: str, *, timeout: int = 15) -> None:
    response = requests.post(webhook_url, json={"text": message}, timeout=timeout)
    response.raise_for_status()
