from datetime import datetime, timezone

from app.core.datetime_utils import normalize_for_json, to_api_iso
from app.core.response import success


def test_to_api_iso_naive_utc():
    dt = datetime(2026, 6, 19, 13, 33, 14, 969000)
    assert to_api_iso(dt) == "2026-06-19T13:33:14.969000Z"


def test_to_api_iso_aware_utc():
    dt = datetime(2026, 6, 19, 13, 33, 14, tzinfo=timezone.utc)
    assert to_api_iso(dt) == "2026-06-19T13:33:14Z"


def test_success_normalizes_nested_datetime():
    payload = success(
        {
            "created_at": datetime(2026, 6, 19, 5, 0, 0),
            "items": [{"updated_at": datetime(2026, 6, 19, 6, 0, 0)}],
        }
    )
    assert payload["data"]["created_at"] == "2026-06-19T05:00:00Z"
    assert payload["data"]["items"][0]["updated_at"] == "2026-06-19T06:00:00Z"


def test_normalize_for_json_leaves_strings():
    assert normalize_for_json("2026-06-19T05:00:00Z") == "2026-06-19T05:00:00Z"
