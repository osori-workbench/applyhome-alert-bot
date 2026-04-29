from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright


def extract_rows_from_html(html: str, *, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []

    for tr in soup.select("table tbody tr"):
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
                "subscription_period": cells[5].get_text(strip=True),
                "winner_date": cells[6].get_text(strip=True),
                "detail_url": urljoin(base_url, link.get("href", "")) if link else base_url,
            }
        )

    return rows


def _load_target_page(page: Page) -> None:
    page.goto("https://www.applyhome.co.kr/co/coa/selectMainView.do", wait_until="domcontentloaded")
    page.get_by_role("link", name="APT 잔여세대").click()
    page.wait_for_timeout(1500)


def fetch_rows() -> list[dict[str, str]]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        _load_target_page(page)
        html = page.content()
        browser.close()
    return extract_rows_from_html(html, base_url="https://www.applyhome.co.kr")
