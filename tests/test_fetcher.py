from pathlib import Path

from applyhome_alert.fetcher import extract_rows_from_html


def test_extract_rows_from_fixture() -> None:
    html = Path("tests/fixtures/applyhome_table.html").read_text(encoding="utf-8")
    rows = extract_rows_from_html(html, base_url="https://www.applyhome.co.kr")
    assert rows[0]["region"] == "경기"
    assert rows[0]["detail_url"] == "https://www.applyhome.co.kr/detail/1"
