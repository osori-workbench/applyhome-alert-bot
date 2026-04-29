from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import Announcement, AnnouncementDetail, SupplyItem


def parse_row(row: dict[str, str]) -> Announcement:
    return Announcement(
        region=row["region"].strip(),
        category=row["category"].strip(),
        name=row["name"].strip(),
        provider=row["provider"].strip(),
        posted_on=row["posted_on"].strip(),
        subscription_period=row["subscription_period"].strip(),
        winner_date=row["winner_date"].strip(),
        detail_url=row["detail_url"].strip(),
        house_manage_no=row.get("house_manage_no", "").strip(),
        pblanc_no=row.get("pblanc_no", "").strip(),
    )


def parse_rows(rows: Iterable[dict[str, str]]) -> list[Announcement]:
    return [parse_row(row) for row in rows]


def parse_detail_html(html: str, *, base_url: str) -> AnnouncementDetail:
    soup = BeautifulSoup(html, "html.parser")
    supply_location = _find_value_by_label(soup, "공급위치")
    supply_scale = _find_value_by_label(soup, "공급규모")
    contract_date = _find_value_by_label(soup, "계약일")
    move_in_month = _find_move_in_month(soup)
    notice_url = _find_notice_url(soup, base_url=base_url)
    supply_items = tuple(_parse_supply_items(soup, move_in_month=move_in_month))

    return AnnouncementDetail(
        supply_location=supply_location,
        supply_scale=supply_scale,
        notice_url=notice_url,
        contract_date=contract_date,
        move_in_month=move_in_month,
        supply_items=supply_items,
    )


def _find_value_by_label(soup: BeautifulSoup, label: str) -> str:
    for row in soup.select("tr"):
        header = row.find(["th", "td"])
        if not header or header.get_text(" ", strip=True) != label:
            continue
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            return cells[1].get_text(" ", strip=True)
    return ""


def _find_notice_url(soup: BeautifulSoup, *, base_url: str) -> str | None:
    link = soup.find("a", string=lambda text: bool(text and "모집공고문 보기" in text))
    if not link or not link.get("href"):
        return None
    return urljoin(base_url, link["href"])


def _find_move_in_month(soup: BeautifulSoup) -> str:
    for li in soup.select("ul.inde_txt li"):
        text = li.get_text(" ", strip=True)
        if "입주예정월" in text:
            return text.split(":", 1)[-1].strip()
    return ""


def _parse_supply_items(soup: BeautifulSoup, *, move_in_month: str) -> list[SupplyItem]:
    supply_units_by_type = _parse_supply_units_by_type(soup)
    tables = soup.select("table.tbl_st")
    for table in tables:
        headers = [th.get_text(" ", strip=True) for th in table.select("thead th")]
        if not headers or "주택형" not in headers:
            continue
        if "공급금액(최고가 기준)" in headers or "분양가" in headers:
            return _parse_price_table(
                table,
                headers=headers,
                supply_units_by_type=supply_units_by_type,
                move_in_month=move_in_month,
            )
        if "공급세대수" in headers and "비고" in headers:
            return _parse_inquiry_table(table, headers, move_in_month=move_in_month)
    return []


def _parse_supply_units_by_type(soup: BeautifulSoup) -> dict[str, str]:
    supply_units: dict[str, str] = {}
    for table in soup.select("table.tbl_st"):
        headers = [th.get_text(" ", strip=True) for th in table.select("thead th")]
        if "주택형" not in headers or "공급세대수" not in headers:
            continue
        if "공급금액(최고가 기준)" in headers:
            continue
        type_index = headers.index("주택형")
        units_index = headers.index("공급세대수")
        for tr in table.select("tbody tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(cells) <= max(type_index, units_index):
                continue
            housing_type = cells[type_index]
            supply_units[housing_type] = cells[units_index]
    return supply_units


def _parse_price_table(
    table,
    *,
    headers: list[str],
    supply_units_by_type: dict[str, str],
    move_in_month: str,
) -> list[SupplyItem]:
    rows: list[SupplyItem] = []
    type_index = headers.index("주택형")
    price_header = "공급금액(최고가 기준)" if "공급금액(최고가 기준)" in headers else "분양가"
    price_index = headers.index(price_header)
    units_index = headers.index("공급세대수") if "공급세대수" in headers else None

    for tr in table.select("tbody tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(cells) <= price_index or len(cells) <= type_index:
            continue
        housing_type = cells[type_index]
        rows.append(
            SupplyItem(
                housing_type=housing_type,
                supply_units=(cells[units_index] if units_index is not None and len(cells) > units_index else supply_units_by_type.get(housing_type, "-")),
                sale_price=_normalize_price(cells[price_index]),
                note="",
                move_in_month=move_in_month,
            )
        )
    return rows


def _parse_inquiry_table(table, headers: list[str], *, move_in_month: str) -> list[SupplyItem]:
    rows: list[SupplyItem] = []
    for tr in table.select("tbody tr"):
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        housing_type = cells[0].get_text(" ", strip=True)
        supply_units = cells[1].get_text(" ", strip=True)
        note_text = cells[2].get_text(" ", strip=True) if len(cells) >= 3 else ""
        sale_price = _extract_sale_price(note_text)
        rows.append(
            SupplyItem(
                housing_type=housing_type,
                supply_units=supply_units,
                sale_price=sale_price,
                note=note_text,
                move_in_month=move_in_month,
            )
        )
    return rows


def _extract_sale_price(note_text: str) -> str:
    if "공급금액" in note_text and ":" in note_text:
        value = note_text.split("공급금액", 1)[-1].split(":", 1)[-1].strip()
        first_line = value.split("잔여세대", 1)[0].strip()
        return _normalize_price(first_line)
    return "정보 없음"


def _normalize_price(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return "정보 없음"
    if any(char.isdigit() for char in cleaned) and "만원" not in cleaned:
        return f"{cleaned}만원"
    return cleaned
