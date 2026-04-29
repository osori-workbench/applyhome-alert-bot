# ApplyHome Alert Bot

청약홈 APT 잔여세대 공고 중 수도권 무순위 공고를 감시해 Slack으로 알려주는 봇입니다.

## 현재 구현 범위

- 수도권(서울/경기/인천) 공고 필터링
- 무순위(사전)/(사후) + 임의공급 필터링
- SQLite 기반 중복 알림 방지
- Slack webhook 메시지 생성/전송
- Playwright 기반 청약홈 페이지 수집
- GitHub Actions 주기 실행 워크플로

## 빠른 시작

```bash
cd /Users/osori/workbench/applyhome-alert-bot
uv sync --group dev
uv run playwright install chromium
cp .env.example .env
export $(grep -v '^#' .env | xargs)
uv run pytest -q
uv run python -m applyhome_alert.main
```

## GitHub Actions 사용

1. 이 프로젝트를 GitHub 저장소에 push
2. 저장소 Secret `SLACK_WEBHOOK_URL` 추가
3. `.github/workflows/applyhome-alert.yml` 활성화
4. 필요하면 cron 스케줄 수정

자세한 운영 방법은 `docs/ops.md`, GitHub Actions 설정은 `docs/github-actions.md`를 참고해주세요.
