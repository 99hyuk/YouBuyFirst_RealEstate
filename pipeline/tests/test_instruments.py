from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from youbuyfirst_pipeline.instruments import load_instrument_snapshot, load_instruments_from_snapshot_url
from youbuyfirst_pipeline.models import InstrumentAliasRule


def test_loads_instruments_from_backend_snapshot_url():
    server, thread, url = _snapshot_server(
        [
            {
                "instrumentId": 7,
                "market": "US",
                "symbol": "TSLA",
                "name": "Tesla",
                "aliases": ["테슬라", "슬라"],
            }
        ]
    )

    try:
        instruments = load_instruments_from_snapshot_url(url)
    finally:
        _stop_server(server, thread)

    assert [
        (instrument.instrument_id, instrument.market, instrument.symbol, instrument.name, instrument.aliases)
        for instrument in instruments
    ] == [
        (7, "US", "TSLA", "Tesla", ["테슬라", "슬라"])
    ]


def test_snapshot_loader_prefers_backend_url_over_csv(tmp_path):
    csv_path = tmp_path / "instruments.csv"
    csv_path.write_text("market,symbol,name,aliases\nUS,AAPL,Apple,애플\n", encoding="utf-8")
    server, thread, url = _snapshot_server(
        [
            {
                "instrumentId": 8,
                "market": "US",
                "symbol": "NVDA",
                "name": "NVIDIA",
                "aliases": ["엔비디아"],
            }
        ]
    )

    try:
        instruments = load_instrument_snapshot(
            csv_path,
            alias_rules=[InstrumentAliasRule(market="US", symbol="AAPL", alias="사과")],
            snapshot_url=url,
        )
    finally:
        _stop_server(server, thread)

    assert [
        (instrument.instrument_id, instrument.market, instrument.symbol, instrument.name, instrument.aliases)
        for instrument in instruments
    ] == [
        (8, "US", "NVDA", "NVIDIA", ["엔비디아"])
    ]


def test_snapshot_loader_retries_backend_url_before_fallback(tmp_path):
    csv_path = tmp_path / "instruments.csv"
    csv_path.write_text("market,symbol,name,aliases\nUS,AAPL,Apple,애플\n", encoding="utf-8")
    server, thread, url = _snapshot_server(
        [
            {
                "instrumentId": 9,
                "market": "US",
                "symbol": "MSFT",
                "name": "Microsoft",
                "aliases": ["마소"],
            }
        ],
        statuses=[503, 200],
    )

    try:
        instruments = load_instrument_snapshot(
            csv_path,
            snapshot_url=url,
            snapshot_retries=2,
            snapshot_retry_delay_seconds=0,
        )
    finally:
        _stop_server(server, thread)

    assert [
        (instrument.instrument_id, instrument.market, instrument.symbol, instrument.name, instrument.aliases)
        for instrument in instruments
    ] == [
        (9, "US", "MSFT", "Microsoft", ["마소"])
    ]


def test_snapshot_loader_falls_back_to_csv_after_backend_url_error(tmp_path):
    csv_path = tmp_path / "instruments.csv"
    csv_path.write_text("market,symbol,name,aliases\nUS,AAPL,Apple,애플\n", encoding="utf-8")
    server, thread, url = _snapshot_server([], statuses=[503, 503])

    try:
        instruments = load_instrument_snapshot(
            csv_path,
            alias_rules=[InstrumentAliasRule(market="US", symbol="AAPL", alias="사과")],
            snapshot_url=url,
            snapshot_retries=2,
            snapshot_retry_delay_seconds=0,
        )
    finally:
        _stop_server(server, thread)

    assert [
        (instrument.instrument_id, instrument.market, instrument.symbol, instrument.name, instrument.aliases)
        for instrument in instruments
    ] == [
        (None, "US", "AAPL", "Apple", ["애플", "사과"])
    ]


def _snapshot_server(
    payload: list[dict],
    *,
    statuses: list[int] | None = None,
) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    body = json.dumps(payload).encode("utf-8")
    status_sequence = list(statuses or [200])

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status = status_sequence.pop(0) if status_sequence else 200
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body) if status == 200 else 0))
            self.end_headers()
            if status == 200:
                self.wfile.write(body)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}/snapshot"


def _stop_server(server: ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
