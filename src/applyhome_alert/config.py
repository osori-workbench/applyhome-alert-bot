from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    slack_webhook_url: str
    include_immediate_supply: bool = False
    db_path: Path = Path("data/alerts.db")
    slack_bot_token: str | None = None
    slack_channel_id: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        webhook_url = os.environ["SLACK_WEBHOOK_URL"]
        include_immediate_supply = os.environ.get("INCLUDE_IMMEDIATE_SUPPLY", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        db_path = Path(os.environ.get("DB_PATH", "data/alerts.db"))
        slack_bot_token = os.environ.get("SLACK_BOT_TOKEN") or None
        slack_channel_id = os.environ.get("SLACK_CHANNEL_ID") or None
        return cls(
            slack_webhook_url=webhook_url,
            include_immediate_supply=include_immediate_supply,
            db_path=db_path,
            slack_bot_token=slack_bot_token,
            slack_channel_id=slack_channel_id,
        )
