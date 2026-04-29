# 수도권 무순위 청약 알림 봇 MVP Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** 청약홈 APT 잔여세대 공고를 주기적으로 확인해 수도권(서울/경기/인천) 무순위 공고만 골라 중복 없이 Slack으로 알림 보내는 MVP를 만든다.

**Architecture:** Playwright 기반 수집기로 청약홈 APT 잔여세대 화면의 표 데이터를 읽고, 순수 함수 계층에서 파싱/필터링/중복 판정을 수행한다. 중복 이력은 SQLite에 저장하고, Slack Webhook 알림 계층을 분리해 로컬 cron이나 GitHub Actions에서 반복 실행 가능하게 구성한다.

**Tech Stack:** Python 3.11+, uv, pytest, Playwright, SQLite, requests

---

### Task 1: 프로젝트 스캐폴드 만들기

**Objective:** 패키지 구조, 의존성 정의, 테스트 폴더를 만든다.

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/applyhome_alert/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`

**Step 1: Write failing test**

```python
from pathlib import Path


def test_project_package_exists() -> None:
    assert Path("src/applyhome_alert/__init__.py").exists()
```

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_smoke.py::test_project_package_exists -v`
Expected: FAIL — package file does not exist

**Step 3: Write minimal implementation**

Create the package file and basic project metadata.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_smoke.py::test_project_package_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add pyproject.toml README.md src tests .gitignore
git commit -m "chore: initialize project scaffold"
```

### Task 2: 공고 데이터 모델과 필터 규칙 구현

**Objective:** 공고를 표현하는 데이터 구조와 수도권/무순위 필터를 순수 함수로 만든다.

**Files:**
- Create: `src/applyhome_alert/models.py`
- Create: `src/applyhome_alert/filters.py`
- Test: `tests/test_filters.py`

**Step 1: Write failing test**

```python
from applyhome_alert.filters import filter_target_announcements
from applyhome_alert.models import Announcement


def test_filter_keeps_only_capital_area_non_ranked_items() -> None:
    items = [
        Announcement(region="경기", category="무순위(사후)", name="A", provider="X", posted_on="2026-04-29", subscription_period="2026-05-04 ~ 2026-05-04", winner_date="2026-05-08", detail_url="https://example.com/a"),
        Announcement(region="부산", category="무순위(사후)", name="B", provider="Y", posted_on="2026-04-29", subscription_period="2026-05-04 ~ 2026-05-04", winner_date="2026-05-08", detail_url="https://example.com/b"),
        Announcement(region="서울", category="임의공급", name="C", provider="Z", posted_on="2026-04-29", subscription_period="2026-05-04 ~ 2026-05-04", winner_date="2026-05-08", detail_url="https://example.com/c"),
    ]

    result = filter_target_announcements(items)

    assert [item.name for item in result] == ["A"]
```

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_filters.py::test_filter_keeps_only_capital_area_non_ranked_items -v`
Expected: FAIL — module/function missing

**Step 3: Write minimal implementation**

Define `Announcement` dataclass and `filter_target_announcements()`.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_filters.py::test_filter_keeps_only_capital_area_non_ranked_items -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/applyhome_alert/models.py src/applyhome_alert/filters.py tests/test_filters.py
git commit -m "feat: add announcement model and target filters"
```

### Task 3: HTML/DOM 행 파싱 구현

**Objective:** 수집된 표 행 데이터를 구조화 공고 객체로 변환한다.

**Files:**
- Create: `src/applyhome_alert/parser.py`
- Test: `tests/test_parser.py`

**Step 1: Write failing test**

```python
from applyhome_alert.parser import parse_row


def test_parse_row_builds_announcement() -> None:
    row = {
        "region": "경기",
        "category": "무순위(사후)",
        "name": "힐스테이트 금오 더퍼스트",
        "provider": "금오생활권1구역주택재개발정비사업조합",
        "posted_on": "2026-04-29",
        "subscription_period": "2026-05-04 ~ 2026-05-04",
        "winner_date": "2026-05-08",
        "detail_url": "https://www.applyhome.co.kr/detail/1",
    }

    announcement = parse_row(row)

    assert announcement.region == "경기"
    assert announcement.name == "힐스테이트 금오 더퍼스트"
```

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_parser.py::test_parse_row_builds_announcement -v`
Expected: FAIL — parser missing

**Step 3: Write minimal implementation**

Implement `parse_row()` and a helper to parse multiple rows.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_parser.py::test_parse_row_builds_announcement -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/applyhome_alert/parser.py tests/test_parser.py
git commit -m "feat: parse announcement rows"
```

### Task 4: 중복 방지 저장소 구현

**Objective:** SQLite에 발송 이력을 저장하고 신규 공고만 판별한다.

**Files:**
- Create: `src/applyhome_alert/store.py`
- Test: `tests/test_store.py`

**Step 1: Write failing test**

```python
from applyhome_alert.models import Announcement
from applyhome_alert.store import AnnouncementStore


def test_store_marks_only_new_announcement(tmp_path) -> None:
    store = AnnouncementStore(tmp_path / "alerts.db")
    item = Announcement(region="경기", category="무순위(사후)", name="A", provider="X", posted_on="2026-04-29", subscription_period="2026-05-04 ~ 2026-05-04", winner_date="2026-05-08", detail_url="https://example.com/a")

    assert store.is_new(item) is True
    store.mark_sent(item)
    assert store.is_new(item) is False
```

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_store.py::test_store_marks_only_new_announcement -v`
Expected: FAIL — store missing

**Step 3: Write minimal implementation**

Create table and implement `is_new()` / `mark_sent()`.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_store.py::test_store_marks_only_new_announcement -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/applyhome_alert/store.py tests/test_store.py
git commit -m "feat: add sqlite announcement store"
```

### Task 5: Slack 메시지 포맷터와 Webhook 알림 구현

**Objective:** 신규 공고 목록을 사람이 읽기 쉬운 Slack 메시지로 만들고 webhook 발송을 분리한다.

**Files:**
- Create: `src/applyhome_alert/notifier.py`
- Test: `tests/test_notifier.py`

**Step 1: Write failing test**

```python
from applyhome_alert.models import Announcement
from applyhome_alert.notifier import build_slack_message


def test_build_slack_message_includes_core_fields() -> None:
    item = Announcement(region="경기", category="무순위(사후)", name="힐스테이트 금오 더퍼스트", provider="조합", posted_on="2026-04-29", subscription_period="2026-05-04 ~ 2026-05-04", winner_date="2026-05-08", detail_url="https://example.com/a")

    message = build_slack_message([item])

    assert "수도권 무순위 청약 알림" in message
    assert "힐스테이트 금오 더퍼스트" in message
    assert "https://example.com/a" in message
```

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_notifier.py::test_build_slack_message_includes_core_fields -v`
Expected: FAIL — notifier missing

**Step 3: Write minimal implementation**

Implement message builder and webhook sender.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_notifier.py::test_build_slack_message_includes_core_fields -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/applyhome_alert/notifier.py tests/test_notifier.py
git commit -m "feat: add slack notifier"
```

### Task 6: 실행 진입점과 설정 로더 구현

**Objective:** 환경변수로 설정을 받아 전체 파이프라인을 실행하는 CLI 엔트리포인트를 만든다.

**Files:**
- Create: `src/applyhome_alert/config.py`
- Create: `src/applyhome_alert/main.py`
- Create: `.env.example`
- Test: `tests/test_config.py`

**Step 1: Write failing test**

```python
from applyhome_alert.config import Settings


def test_settings_defaults_exclude_immediate_supply() -> None:
    settings = Settings(slack_webhook_url="https://hooks.slack.com/services/test")
    assert settings.include_immediate_supply is False
```

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_config.py::test_settings_defaults_exclude_immediate_supply -v`
Expected: FAIL — config missing

**Step 3: Write minimal implementation**

Create settings model and CLI main.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_config.py::test_settings_defaults_exclude_immediate_supply -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/applyhome_alert/config.py src/applyhome_alert/main.py .env.example tests/test_config.py
git commit -m "feat: add runtime settings and cli entrypoint"
```

### Task 7: Playwright 수집기 통합 및 E2E 스모크 테스트

**Objective:** 실제 청약홈 페이지에서 표 데이터를 읽는 수집기를 만들고, HTML fixture 기반 스모크 테스트를 추가한다.

**Files:**
- Create: `src/applyhome_alert/fetcher.py`
- Create: `tests/fixtures/applyhome_table.html`
- Test: `tests/test_fetcher.py`

**Step 1: Write failing test**

```python
from pathlib import Path
from applyhome_alert.fetcher import extract_rows_from_html


def test_extract_rows_from_fixture() -> None:
    html = Path("tests/fixtures/applyhome_table.html").read_text(encoding="utf-8")
    rows = extract_rows_from_html(html, base_url="https://www.applyhome.co.kr")
    assert rows[0]["region"] == "경기"
```

**Step 2: Run test to verify failure**

Run: `uv run pytest tests/test_fetcher.py::test_extract_rows_from_fixture -v`
Expected: FAIL — fetcher missing

**Step 3: Write minimal implementation**

Implement HTML extraction helper first, then Playwright fetch routine.

**Step 4: Run test to verify pass**

Run: `uv run pytest tests/test_fetcher.py::test_extract_rows_from_fixture -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/applyhome_alert/fetcher.py tests/fixtures/applyhome_table.html tests/test_fetcher.py
git commit -m "feat: add applyhome fetcher"
```

### Task 8: 문서화 및 운영 가이드 정리

**Objective:** 설치/실행/cron 설정/제약사항을 문서화한다.

**Files:**
- Modify: `README.md`
- Create: `docs/ops.md`

**Step 1: Write failing test**

Documentation task — no production test required.

**Step 2: Write minimal implementation**

Document:
- `uv sync`
- `playwright install chromium`
- `.env` 작성
- `uv run python -m applyhome_alert.main`
- cron 예시
- 한계: 사이트 구조 변경, 봇 감지 가능성, 공고문 상세 조건은 링크 확인 필요

**Step 3: Verify**

Run: `uv run pytest -q`
Expected: PASS

**Step 4: Commit**

```bash
git add README.md docs/ops.md
git commit -m "docs: add setup and operations guide"
```
