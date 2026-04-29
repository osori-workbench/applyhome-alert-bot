from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from .models import Announcement
from .parser import parse_detail_html

LIST_URL = "https://www.applyhome.co.kr/ai/aia/selectAPTRemndrLttotPblancListView.do"
DETAIL_URL = "https://www.applyhome.co.kr/ai/aia/selectAPTRemndrLttotPblancDetailView.do"
BASE_URL = "https://www.applyhome.co.kr"
_PAGE_INDEX_RE = re.compile(r"pageIndex=(\d+)")


def extract_rows_from_html(html: str, *, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []

    for tr in soup.select("tr[data-hmno][data-pbno]"):
        cells = tr.find_all("td")
        if len(cells) < 7:
            continue

        link = cells[2].find("a")
        rows.append(
            {
                "region": cells[0].get_text(strip=True),
                "category": cells[1].get_text(strip=True),
                "name": cells[2].get_text(strip=True),
                "provider": cells[3].get_text(strip=True),
                "posted_on": cells[4].get_text(strip=True),
                "subscription_period": cells[5].get_text(" ", strip=True),
                "winner_date": cells[6].get_text(strip=True),
                "detail_url": urljoin(base_url, link.get("href", "")) if link else base_url,
                "house_manage_no": tr.get("data-hmno", ""),
                "pblanc_no": tr.get("data-pbno", ""),
            }
        )

    return rows


def extract_total_pages_from_html(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    page_indexes: list[int] = []
    for link in soup.select('a[href*="pageIndex="]'):
        href = link.get("href", "")
        match = _PAGE_INDEX_RE.search(href)
        if match:
            page_indexes.append(int(match.group(1)))
    return max(page_indexes, default=1)


def fetch_rows() -> list[dict[str, str]]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(LIST_URL, wait_until="domcontentloaded")
        first_html = page.content()
        total_pages = extract_total_pages_from_html(first_html)
        rows = extract_rows_from_html(first_html, base_url=BASE_URL)

        for page_index in range(2, total_pages + 1):
            page.goto(f"{LIST_URL}?pageIndex={page_index}", wait_until="domcontentloaded")
            rows.extend(extract_rows_from_html(page.content(), base_url=BASE_URL))

        browser.close()
    return rows


def fetch_announcement_details(items: list[Announcement]) -> list[Announcement]:
    if not items:
        return []

    with sync_playwright() as playwright:
        request_context = playwright.request.new_context(base_url=BASE_URL)
        enriched_items: list[Announcement] = []
        for item in items:
            if not item.house_manage_no or not item.pblanc_no:
                enriched_items.append(item)
                continue
            response = request_context.post(
                DETAIL_URL,
                form={
                    "houseManageNo": item.house_manage_no,
                    "pblancNo": item.pblanc_no,
                    "gvPgmId": "AIA03M01",
                },
                headers={"Referer": LIST_URL},
            )
            body = response.text()
            _ensure_success_status(response.status, body)
            detail = parse_detail_html(body, base_url=BASE_URL)
            enriched_items.append(item.with_detail(detail))
        request_context.dispose()
    return enriched_items


def _ensure_success_status(status: int, body: str) -> None:
    if 200 <= status < 300:
        return
    raise RuntimeError(f"ApplyHome detail request failed: status={status}, body={body[:200]}")
