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
