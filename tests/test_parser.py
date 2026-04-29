from pathlib import Path

from applyhome_alert.parser import parse_detail_html, parse_row


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
        "house_manage_no": "2026910103",
        "pblanc_no": "2026910103",
    }

    announcement = parse_row(row)

    assert announcement.region == "경기"
    assert announcement.name == "힐스테이트 금오 더퍼스트"
    assert announcement.house_manage_no == "2026910103"
    assert announcement.pblanc_no == "2026910103"


def test_parse_detail_html_extracts_numeric_prices() -> None:
    html = Path("tests/fixtures/detail_price_table.html").read_text(encoding="utf-8")

    detail = parse_detail_html(html, base_url="https://www.applyhome.co.kr")

    assert detail.notice_url.startswith("https://www.applyhome.co.kr/ai/aia/getAtchmnfl.do")
    assert detail.contract_date == "2026-05-15 ~ 2026-05-15"
    assert detail.move_in_month == "2026.06"
    assert detail.supply_items[0].housing_type == "084.7576A"
    assert detail.supply_items[0].sale_price == "48,660만원"
    assert detail.supply_items[0].price_value == 48660


def test_parse_detail_html_extracts_inquiry_price() -> None:
    html = Path("tests/fixtures/detail_inquiry.html").read_text(encoding="utf-8")

    detail = parse_detail_html(html, base_url="https://www.applyhome.co.kr")

    assert detail.supply_items[0].housing_type == "036.1818"
    assert detail.supply_items[0].supply_units == "1"
    assert detail.supply_items[0].sale_price == "사업주체 문의"
    assert detail.supply_items[0].price_value is None
