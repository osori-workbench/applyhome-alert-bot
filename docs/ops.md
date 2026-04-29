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

`.env`에 Slack webhook URL을 넣어주세요.

## 3. 수동 실행

```bash
export $(grep -v '^#' .env | xargs)
uv run python -m applyhome_alert.main
```

## 4. 자동 실행

### 로컬 cron 예시

매시 5분마다 실행:

```cron
5 * * * * cd /Users/osori/workbench/applyhome-alert-bot && export $(grep -v '^#' .env | xargs) && /Users/osori/.local/bin/uv run python -m applyhome_alert.main >> logs/cron.log 2>&1
```

### GitHub Actions

GitHub Actions용 워크플로는 `.github/workflows/applyhome-alert.yml`에 있습니다.

- 기본 주기: 매시 5분(UTC)
- Secret 필요: `SLACK_WEBHOOK_URL`
- 중복 방지 DB는 `actions/cache`로 복원/저장

자세한 설정 절차는 `docs/github-actions.md`를 참고하세요.

## 5. 현재 한계

- 청약홈 페이지 구조가 바뀌면 selector/HTML 파싱 수정이 필요합니다.
- 실제 자격 조건은 반드시 상세 공고문에서 다시 확인해야 합니다.
- 자동화 접근은 사이트 측 봇 감지 정책의 영향을 받을 수 있습니다.
