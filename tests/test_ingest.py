from unittest.mock import MagicMock, patch

from src import ingest_eia


def _fake_response(rows, total):
    resp = MagicMock()
    resp.json.return_value = {"response": {"data": rows, "total": str(total)}}
    resp.raise_for_status.return_value = None
    return resp


def test_fetch_all_rows_pages_until_total_reached():
    page1 = [{"period": "2020-01"}] * ingest_eia.PAGE_SIZE
    page2 = [{"period": "2020-02"}] * 3
    responses = [
        _fake_response(page1, total=ingest_eia.PAGE_SIZE + 3),
        _fake_response(page2, total=ingest_eia.PAGE_SIZE + 3),
    ]
    with patch("src.ingest_eia.requests.get", side_effect=responses) as mock_get:
        rows = ingest_eia.fetch_all_rows("key", ["CO"], "2020-01")

    assert len(rows) == ingest_eia.PAGE_SIZE + 3
    assert mock_get.call_count == 2


def test_fetch_stops_on_empty_page():
    responses = [_fake_response([], total=100)]
    with patch("src.ingest_eia.requests.get", side_effect=responses):
        rows = ingest_eia.fetch_all_rows("key", ["CO"], "2020-01")
    assert rows == []
