from pathlib import Path

import pytest

from applyhome_alert.fetcher import _ensure_success_status, extract_rows_from_html


def test_extract_rows_from_fixture() -> None:
    html = Path("tests/fixtures/applyhome_table.html").read_text(encoding="utf-8")
    rows = extract_rows_from_html(html, base_url="https://www.applyhome.co.kr")
    assert rows[0]["region"] == "경기"
    assert rows[0]["detail_url"] == "https://www.applyhome.co.kr/detail/1"
    assert rows[0]["house_manage_no"] == "2026910103"
    assert rows[0]["pblanc_no"] == "2026910103"


def test_ensure_success_status_raises_for_http_errors() -> None:
    with pytest.raises(RuntimeError):
        _ensure_success_status(500, "boom")
