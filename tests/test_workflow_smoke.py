from pathlib import Path


PROJECT_DIR = "/Users/osori/workbench/applyhome-alert-bot"


def test_local_cron_runner_assets_exist() -> None:
    runner = Path("scripts/run_alert.sh")
    assert runner.exists()
    runner_text = runner.read_text(encoding="utf-8")
    assert f'PROJECT_DIR="{PROJECT_DIR}"' in runner_text
    assert 'uv run python -m applyhome_alert.main' in runner_text
    assert 'source "$ENV_FILE"' in runner_text

    crontab = Path("deploy/applyhome-alert.crontab")
    assert crontab.exists()
    crontab_text = crontab.read_text(encoding="utf-8")
    assert "0 9 * * *" in crontab_text
    assert f"{PROJECT_DIR}/scripts/run_alert.sh" in crontab_text
