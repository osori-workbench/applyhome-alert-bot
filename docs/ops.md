# 운영 가이드

## 1. 설치

```bash
cd /Users/osori/workbench/applyhome-alert-bot
uv sync --group dev
uv run playwright install chromium
```

## 2. 환경변수 설정

```bash
cp .env.example .env
```

필수:

- `SLACK_WEBHOOK_URL`
- `INCLUDE_IMMEDIATE_SUPPLY=true`
- `DB_PATH=data/alerts.db`

선택:

- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL_ID`

> `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_ID`까지 있어야 부모 메시지 아래에 thread reply로 상세 공급내역을 붙일 수 있습니다. webhook만 있으면 부모 Block Kit 요약 메시지만 보냅니다.

## 3. 수동 실행

```bash
set -a
source .env
set +a
uv run python -m applyhome_alert.main
```

## 4. 자동 실행

### 로컬 cron 예시

현재 프로젝트에는 cron에서 바로 호출할 수 있도록 `scripts/run_alert.sh`와 등록용 파일 `deploy/applyhome-alert.crontab`를 포함했습니다.

매일 오전 9시에 실행:

```cron
0 9 * * * /Users/osori/workbench/applyhome-alert-bot/scripts/run_alert.sh
```

적용 명령:

```bash
crontab /Users/osori/workbench/applyhome-alert-bot/deploy/applyhome-alert.crontab
```

로그 파일:

```text
/Users/osori/workbench/applyhome-alert-bot/logs/cron.log
```

### GitHub Actions

GitHub Actions용 워크플로는 `.github/workflows/applyhome-alert.yml`에 있습니다.

- 기본 주기: 매시 5분(UTC)
- Secret 필요: `SLACK_WEBHOOK_URL`
- 중복 방지 DB는 `actions/cache`로 복원/저장
- 다만 실운영은 로컬 cron + SQLite 유지가 더 안정적입니다.

자세한 설정 절차는 `docs/github-actions.md`를 참고하세요.

## 5. 데이터 초기화

이미 보낸 공고 이력을 전부 초기화하고 다시 보내고 싶으면:

```bash
rm -f /Users/osori/workbench/applyhome-alert-bot/data/alerts.db
```

그 다음 수동 실행 또는 다음 cron tick에서 현재 공고를 다시 신규로 판단합니다.

## 6. 현재 한계

- 청약홈 페이지 구조가 바뀌면 selector/HTML 파싱 수정이 필요합니다.
- 실제 자격 조건은 반드시 상세 공고문에서 다시 확인해야 합니다.
- 자동화 접근은 사이트 측 봇 감지 정책의 영향을 받을 수 있습니다.
- webhook-only 모드에서는 Slack thread reply를 완전히 구현할 수 없습니다.
