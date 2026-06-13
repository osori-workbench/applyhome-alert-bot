from pathlib import Path

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from applyhome_alert.fetcher import (
    _ensure_success_status,
    _fetch_list_page_html,
    extract_rows_from_html,
    extract_total_pages_from_html,
    fetch_announcement_detail,
)
from applyhome_alert.models import Announcement, AnnouncementDetail, SupplyItem


def test_extract_rows_from_fixture() -> None:
    html = Path("tests/fixtures/applyhome_table.html").read_text(encoding="utf-8")
    rows = extract_rows_from_html(html, base_url="https://www.applyhome.co.kr")
    assert rows[0]["region"] == "경기"
    assert rows[0]["detail_url"] == "https://www.applyhome.co.kr/detail/1"
    assert rows[0]["house_manage_no"] == "2026910103"
    assert rows[0]["pblanc_no"] == "2026910103"


def test_extract_total_pages_from_html_reads_last_page_link() -> None:
    html = """
    <div class="pagination">
      <a href="?pageIndex=1">1</a>
      <a href="?pageIndex=2">2</a>
      <a href="?pageIndex=10">10</a>
      <a href="?pageIndex=61">맨끝으로</a>
    </div>
    """

    assert extract_total_pages_from_html(html) == 61


def test_ensure_success_status_raises_for_http_errors() -> None:
    with pytest.raises(RuntimeError):
        _ensure_success_status(500, "boom")


class _FakePage:
    def __init__(self, *, full_html: str, partial_html: str = "<html></html>") -> None:
        self.calls: list[tuple[str, str, int | None]] = []
        self._full_html = full_html
        self._partial_html = partial_html
        self._current_html = partial_html

    def goto(self, url: str, *, wait_until: str, timeout: int | None = None):
        self.calls.append((url, wait_until, timeout))
        if wait_until == "domcontentloaded":
            self._current_html = self._partial_html
            raise PlaywrightTimeoutError("timed out waiting for domcontentloaded")
        self._current_html = self._full_html
        return None

    def content(self) -> str:
        return self._current_html


def test_fetch_list_page_html_falls_back_to_commit_on_domcontentloaded_timeout() -> None:
    full_html = Path("tests/fixtures/applyhome_table.html").read_text(encoding="utf-8")
    page = _FakePage(full_html=full_html)

    html = _fetch_list_page_html(page, "https://www.applyhome.co.kr/list?pageIndex=2")

    assert extract_rows_from_html(html, base_url="https://www.applyhome.co.kr")
    assert page.calls == [
        ("https://www.applyhome.co.kr/list?pageIndex=2", "domcontentloaded", 30000),
        ("https://www.applyhome.co.kr/list?pageIndex=2", "commit", 15000),
    ]


def test_fetch_announcement_detail_returns_single_enriched_item(monkeypatch: pytest.MonkeyPatch) -> None:
    announcement = Announcement(
        region="경기",
        category="무순위(사후)",
        name="힐스테이트 금오 더퍼스트",
        provider="금오생활권1구역주택재개발정비사업조합",
        posted_on="2026-04-29",
        subscription_period="2026-05-04 ~ 2026-05-04",
        winner_date="2026-05-08",
        detail_url="https://www.applyhome.co.kr/detail/1",
        house_manage_no="2026910103",
        pblanc_no="2026910103",
    )
    detail = AnnouncementDetail(
        supply_location="경기 의정부시",
        supply_scale="아파트 1세대",
        notice_url="https://www.applyhome.co.kr/notice/1",
        contract_date="2026-05-15 ~ 2026-05-15",
        move_in_month="2026.06",
        supply_items=(SupplyItem(housing_type="084.7576A", supply_units="1", sale_price="48,660만원"),),
    )

    monkeypatch.setattr(
        "applyhome_alert.fetcher.fetch_announcement_details",
        lambda items: [items[0].with_detail(detail)],
    )

    enriched = fetch_announcement_detail(announcement)

    assert enriched == announcement.with_detail(detail)


