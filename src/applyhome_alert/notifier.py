from __future__ import annotations

from collections.abc import Sequence
from datetime import date

import requests

from .models import Announcement, SupplyItem

APPLYHOME_LIST_URL = "https://www.applyhome.co.kr/ai/aia/selectAPTRemndrLttotPblancListView.do"


def build_parent_payload(
    items: Sequence[Announcement],
    *,
    today_items: Sequence[Announcement],
    today: date | None = None,
) -> dict:
    effective_today = today or date.today()
    sorted_today_items = _sort_announcements(today_items, today=effective_today)
    sorted_items = _sort_announcements(items, today=effective_today)

    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "수도권 무순위 청약 알림"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{APPLYHOME_LIST_URL}|청약홈 바로가기>*",
            },
        },
    ]

    if sorted_today_items:
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*오늘 청약 공고 요약* ({effective_today.isoformat()} 기준)"}}
        )

    return {
        "text": "수도권 무순위 청약 알림",
        "blocks": blocks,
        "attachments": _build_parent_attachments(sorted_items, sorted_today_items),
    }


def build_thread_payloads(items: Sequence[Announcement], *, today: date | None = None) -> list[dict]:
    effective_today = today or date.today()
    payloads: list[dict] = []
    for item in _sort_announcements(items, today=effective_today):
        detail = item.detail
        if detail is None:
            continue
        lines = [_format_supply_item_line(supply_item) for supply_item in detail.supply_items]
        detail_link = detail.notice_url or item.detail_url
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*상세 공급내역 · {item.name}*\n"
                        f"• <{detail_link}|청약홈 입주자모집공고>\n"
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
        if _has_inquiry_price(detail.supply_items):
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "사업주체 문의는 청약홈 상세 페이지 기준 표기입니다. 정확한 분양가는 상단 청약홈 입주자모집공고 링크에서 다시 확인해 주세요.",
                        }
                    ],
                }
            )
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


def _build_parent_attachments(items: Sequence[Announcement], today_items: Sequence[Announcement]) -> list[dict]:
    attachments: list[dict] = []
    if today_items:
        attachments.append({"blocks": [_build_today_table_block(today_items)]})
    if items:
        attachments.append({"blocks": _build_new_item_blocks(items)})
    return attachments


def _build_new_item_blocks(items: Sequence[Announcement]) -> list[dict]:
    blocks: list[dict] = []
    for item in items:
        alert_link = item.detail.notice_url if item.detail and item.detail.notice_url else item.detail_url
        supply_location = item.detail.supply_location if item.detail and item.detail.supply_location else "-"
        blocks.extend(
            [
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*<{alert_link}|{item.name}>*\n"
                            f"• 공급위치: {supply_location}\n"
                            f"• 지역/구분: {item.region} / {item.category}\n"
                            f"• 공고일: {item.posted_on}\n"
                            f"• 청약기간: {item.subscription_period}\n"
                            f"• 당첨자발표: {item.winner_date}\n"
                            f"• *최저 분양가:* *{item.cheapest_price_summary}*"
                        ),
                    },
                },
            ]
        )
    return blocks


def _build_today_table_block(items: Sequence[Announcement]) -> dict:
    return {
        "type": "table",
        "column_settings": [
            {"align": "center"},
            {"align": "center"},
            {"is_wrapped": True},
            {"align": "center", "is_wrapped": True},
        ],
        "rows": [
            [_raw_cell("지역"), _raw_cell("구분"), _raw_cell("주택명"), _raw_cell("청약기간")],
            *[
                [
                    _raw_cell(item.region),
                    _raw_cell(item.category),
                    _raw_cell(item.name),
                    _raw_cell(item.subscription_period),
                ]
                for item in items
            ],
        ],
    }


def _sort_announcements(items: Sequence[Announcement], *, today: date) -> list[Announcement]:
    return sorted(
        items,
        key=lambda item: (
            0 if item.is_open_on(today) else max((item.subscription_start_date - today).days, 0),
            item.subscription_end_date,
            item.subscription_start_date,
            item.name,
        ),
    )


def _raw_cell(text: str) -> dict:
    return {"type": "raw_text", "text": text}


def _format_supply_item_line(item: SupplyItem) -> str:
    note = f" · {item.note}" if item.note else ""
    return f"• 주택형 {item.housing_type} / {item.supply_units}세대 / {item.sale_price}{note}"


def _has_inquiry_price(items: Sequence[SupplyItem]) -> bool:
    return any(item.price_value is None and "사업주체 문의" in item.sale_price for item in items)


def send_slack_webhook(webhook_url: str, payload: dict, *, timeout: int = 15) -> None:
    response = requests.post(webhook_url, json=payload, timeout=timeout)
    response.raise_for_status()


def send_slack_notifications(
    webhook_url: str,
    items: Sequence[Announcement],
    *,
    today_items: Sequence[Announcement],
    today: date | None = None,
    bot_token: str | None = None,
    channel_id: str | None = None,
    timeout: int = 15,
) -> None:
    parent_payload = build_parent_payload(items, today_items=today_items, today=today)
    if bot_token and channel_id:
        parent_ts = _post_chat_message(
            bot_token=bot_token,
            channel_id=channel_id,
            payload=parent_payload,
            timeout=timeout,
        )
        for thread_payload in build_thread_payloads(items, today=today):
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
    if payload.get("attachments"):
        body["attachments"] = payload["attachments"]
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
