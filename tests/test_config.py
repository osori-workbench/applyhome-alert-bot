from applyhome_alert.config import Settings


def test_settings_defaults_exclude_immediate_supply() -> None:
    settings = Settings(slack_webhook_url="https://hooks.slack.com/services/test")
    assert settings.include_immediate_supply is False
