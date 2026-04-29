# GitHub Actions 설정 가이드

## 1. 필수 GitHub Secret

레포지토리의 **Settings → Secrets and variables → Actions** 에서 아래 secret을 추가하세요.

- `SLACK_WEBHOOK_URL`: Slack incoming webhook URL
- `SLACK_BOT_TOKEN` *(optional)*: thread reply를 위한 Slack Bot token
- `SLACK_CHANNEL_ID` *(optional)*: thread reply를 달 대상 channel ID

## 2. 워크플로 파일

- 경로: `.github/workflows/applyhome-alert.yml`
- 기본 실행 주기: **매시 5분(UTC)**
- 수동 실행도 가능: `workflow_dispatch`

## 3. 기본 동작

워크플로는 아래 순서로 실행됩니다.

1. 코드 checkout
2. Python 3.11 설정
3. `uv sync --group dev`
4. `uv run playwright install chromium`
5. `uv run python -m applyhome_alert.main`

## 4. 현재 설정값

- `INCLUDE_IMMEDIATE_SUPPLY=true`
- `DB_PATH=data/alerts.db`

## 5. 중복 방지 저장

워크플로는 `actions/cache`로 `data/alerts.db`를 복원/저장합니다. 따라서 이전 실행에서 이미 보낸 공고는 다음 실행에서 다시 거를 수 있습니다.

다만 GitHub Actions 캐시는 영구 DB가 아니므로, 아래 상황에서는 중복 이력이 사라질 수 있습니다.

- 캐시가 만료되거나 제거된 경우
- 브랜치 이름이 바뀐 경우
- 워크플로 키 전략을 변경한 경우

## 6. 주의사항

- 청약홈 페이지 구조가 바뀌면 selector/HTML 파싱 수정이 필요합니다.
- 실제 자격 조건은 반드시 상세 공고문에서 다시 확인해야 합니다.
- 자동화 접근은 사이트 측 봇 감지 정책의 영향을 받을 수 있습니다.
