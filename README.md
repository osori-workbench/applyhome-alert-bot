# ApplyHome Alert Bot

청약홈 `APT 잔여세대` 목록을 주기적으로 확인해서, **수도권(서울/경기/인천)** 의 **무순위(사전)/(사후) + 임의공급** 공고만 Slack으로 알려주는 로컬 알림 봇입니다.

이 프로젝트는 **로컬 cron + SQLite** 조합을 기본 운영 방식으로 가정합니다. 이유는 중복 방지용 DB(`data/alerts.db`)를 같은 머신에 계속 유지해야 같은 공고를 반복 발송하지 않기 때문입니다.

---

## 주요 기능

- 청약홈 `APT 잔여세대` 목록 수집
- 수도권(서울/경기/인천) 필터링
- 무순위(사전)/(사후) + 임의공급 필터링
- SQLite 기반 중복 알림 방지
- Playwright 기반 상세 공고 파싱
- Slack **Block Kit** 부모 메시지 전송
- 상세 공고문에서 아래 정보 추출
  - 주택형
  - 공급세대수
  - 분양가(또는 `사업주체 문의`)
  - 계약일
  - 입주예정월
  - 모집공고문 링크
- 부모 메시지에 공고별 **최저 분양가 요약** 표시
- 선택적으로 Slack thread reply 지원
  - `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`가 있으면 부모 메시지 아래 thread reply로 상세 공급내역 전송
  - webhook만 있으면 부모 Block Kit 메시지만 전송

---

## 알림 예시

### 부모 메시지
- 단지명
- 지역/구분
- 청약기간
- 당첨자발표
- 최저 분양가

### 쓰레드 상세 메시지 (선택 기능)
- 공급위치
- 공급규모
- 계약일
- 입주예정월
- 주택형 / 공급세대수 / 분양가
- 모집공고문 버튼

> Slack incoming webhook만으로는 부모 메시지의 `ts`를 직접 회수할 수 없어서 thread reply를 안정적으로 달기 어렵습니다. 그래서 **진짜 쓰레드 답글**이 필요하면 `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`를 함께 설정해야 합니다.

---

## 프로젝트 구조

```text
applyhome-alert-bot/
├── data/                        # SQLite DB 위치 (git ignored)
├── deploy/
│   └── applyhome-alert.crontab  # cron 등록 파일
├── docs/
│   ├── github-actions.md
│   ├── ops.md
│   └── plans/
├── logs/                        # cron 로그 위치 (git ignored)
├── scripts/
│   └── run_alert.sh             # cron 실행 스크립트
├── src/applyhome_alert/
│   ├── config.py
│   ├── fetcher.py
│   ├── filters.py
│   ├── main.py
│   ├── models.py
│   ├── notifier.py
│   ├── parser.py
│   └── store.py
├── tests/
└── pyproject.toml
```

---

## 빠른 시작

### 1) 설치

```bash
cd /Users/osori/workbench/applyhome-alert-bot
uv sync --group dev
uv run playwright install chromium
```

### 2) 환경 변수 파일 준비

```bash
cp .env.example .env
```

최소 설정:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
INCLUDE_IMMEDIATE_SUPPLY=true
DB_PATH=data/alerts.db
```

쓰레드 상세 메시지까지 원하면 추가:

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C1234567890
```

### 3) 테스트

```bash
uv run pytest -q
```

### 4) 수동 실행

```bash
set -a
source .env
set +a
uv run python -m applyhome_alert.main
```

---

## 운영 방식

### 권장: 로컬 cron

이 프로젝트는 로컬 cron 운용을 기본값으로 둡니다.

등록 파일 적용:

```bash
crontab /Users/osori/workbench/applyhome-alert-bot/deploy/applyhome-alert.crontab
```

현재 기본 스케줄:

```cron
5 * * * * /Users/osori/workbench/applyhome-alert-bot/scripts/run_alert.sh
```

로그 파일:

```text
/Users/osori/workbench/applyhome-alert-bot/logs/cron.log
```

### 선택: GitHub Actions

GitHub Actions 워크플로도 남겨두었지만, DB 지속성 측면에서 로컬 cron보다 덜 안정적입니다.
자세한 내용은 `docs/github-actions.md`를 참고해주세요.

---

## 중복 방지 방식

발송이 성공하면 `data/alerts.db`에 공고 키를 저장합니다.

기본 dedupe key 구성:
- 지역
- 구분
- 주택명
- 공고일
- 청약기간

즉, 같은 공고가 다음 실행에서 다시 보여도 DB에 이미 있으면 재발송하지 않습니다.

데이터를 초기화하고 전체를 다시 보내고 싶으면:

```bash
rm -f /Users/osori/workbench/applyhome-alert-bot/data/alerts.db
```

그 다음 다시 실행하면 현재 조회되는 공고를 신규로 간주하고 다시 발송합니다.

---

## 구현 메모

### 1) 목록 수집
- `fetch_rows()`가 APT 잔여세대 목록 HTML을 가져옵니다.
- 각 행에서 `data-hmno`, `data-pbno`를 함께 저장합니다.

### 2) 상세 공고 수집
- 신규 공고만 골라서 상세 endpoint를 Playwright request context로 POST 호출합니다.
- 상세 HTML에서 공급내역/분양가/입주예정월/모집공고문 링크를 추출합니다.

### 3) Slack 전송
- webhook만 있으면 부모 Block Kit 메시지 전송
- bot token + channel ID가 있으면
  1. 부모 메시지 전송
  2. 부모 `ts` 확보
  3. 공고별 상세 thread reply 전송

---

## 한계와 주의사항

- 청약홈 UI/HTML 구조가 바뀌면 파서 수정이 필요합니다.
- 일부 공고는 분양가가 `사업주체 문의`로만 제공됩니다.
- 상세 조건(잔여세대 동호수, 자격, 특별공급 세부 조건 등)은 반드시 모집공고문 원문을 다시 확인해야 합니다.
- Slack thread reply는 webhook-only 모드에서 완전 지원되지 않습니다. 진짜 thread reply가 필요하면 Web API 자격증명도 넣어야 합니다.

---

## 문서

- 운영 가이드: `docs/ops.md`
- GitHub Actions 메모: `docs/github-actions.md`
- 초기 구현 계획: `docs/plans/2026-04-29-applyhome-alert-bot-mvp.md`
