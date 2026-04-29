from __future__ import annotations

from collections.abc import Sequence

import requests

from .models import Announcement, SupplyItem


def build_parent_payload(items: Sequence[Announcement]) -> dict:
    summary_lines = [f"• {item.name} — 최저 분양가 {item.cheapest_price_summary}" for item in items]
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "수도권 무순위 청약 알림"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "새로운 수도권 무순위/임의공급 공고를 감지했습니다.\n" + "\n".join(summary_lines),
            },
        },
    ]

    for item in items:
        alert_link = item.detail.notice_url if item.detail and item.detail.notice_url else item.detail_url
        blocks.extend(
            [
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*<{alert_link}|{item.name}>*\n"
                            f"• 지역/구분: {item.region} / {item.category}\n"
                            f"• 청약기간: {item.subscription_period}\n"
                            f"• 당첨자발표: {item.winner_date}\n"
                            f"• 최저 분양가: {item.cheapest_price_summary}"
                        ),
                    },
                    "fields": [
                        {"type": "mrkdwn", "text": f"*시행사*\n{item.provider}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*공고일*\n{item.posted_on}",
                        },
                    ],
                },
            ]
        )

    return {
        "text": "수도권 무순위 청약 알림",
        "blocks": blocks,
    }


def build_thread_payloads(items: Sequence[Announcement]) -> list[dict]:
    payloads: list[dict] = []
    for item in items:
        detail = item.detail
        if detail is None:
            continue
        lines = [_format_supply_item_line(supply_item) for supply_item in detail.supply_items]
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*상세 공급내역 · {item.name}*\n"
                        f"• 공급위치: {detail.supply_location or '-'}\n"
                        f"• 공급규모: {detail.supply_scale or '-'}\n"
                        f"• 계약일: {detail.contract_date or '-'}\n"
                        f"• 입주예정월: {detail.move_in_month or '-'}"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*주택형 / 공급세대수 / 분양가*\n" + "\n".join(lines),
                },
            },
        ]
        if detail.notice_url:
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "모집공고문 보기"},
                            "url": detail.notice_url,
                        }
                    ],
                }
            )
        payloads.append(
            {
                "text": f"상세 공급내역 · {item.name}",
                "blocks": blocks,
            }
        )
    return payloads


def _format_supply_item_line(item: SupplyItem) -> str:
    note = f" · {item.note}" if item.note else ""
    return f"• 주택형 {item.housing_type} / {item.supply_units}세대 / {item.sale_price}{note}"


def send_slack_webhook(webhook_url: str, payload: dict, *, timeout: int = 15) -> None:
    response = requests.post(webhook_url, json=payload, timeout=timeout)
    response.raise_for_status()


def send_slack_notifications(
    webhook_url: str,
    items: Sequence[Announcement],
    *,
    bot_token: str | None = None,
    channel_id: str | None = None,
    timeout: int = 15,
) -> None:
    parent_payload = build_parent_payload(items)
    if bot_token and channel_id:
        parent_ts = _post_chat_message(
            bot_token=bot_token,
            channel_id=channel_id,
            payload=parent_payload,
            timeout=timeout,
        )
        for thread_payload in build_thread_payloads(items):
            _post_chat_message(
                bot_token=bot_token,
                channel_id=channel_id,
                payload=thread_payload,
                thread_ts=parent_ts,
                timeout=timeout,
            )
        return

    send_slack_webhook(webhook_url, parent_payload, timeout=timeout)


def _post_chat_message(
    *,
    bot_token: str,
    channel_id: str,
    payload: dict,
    thread_ts: str | None = None,
    timeout: int = 15,
) -> str:
    body = {
        "channel": channel_id,
        "text": payload["text"],
        "blocks": payload["blocks"],
    }
    if thread_ts is not None:
        body["thread_ts"] = thread_ts
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json=body,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data}")
    return str(data["ts"])
