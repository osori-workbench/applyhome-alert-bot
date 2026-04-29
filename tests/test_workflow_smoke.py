from pathlib import Path


def test_github_actions_workflow_exists() -> None:
    workflow = Path('.github/workflows/applyhome-alert.yml')
    assert workflow.exists()
    text = workflow.read_text(encoding='utf-8')
    assert 'schedule:' in text
    assert 'workflow_dispatch:' in text
    assert 'SLACK_WEBHOOK_URL' in text
    assert 'INCLUDE_IMMEDIATE_SUPPLY: "true"' in text
