from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Sequence
from typing import Any

import websocket

from .config import FeedConfig
from .json_logging import JsonLogger


class PolymarketMarketFeed:
    def __init__(
        self,
        asset_ids: Sequence[str],
        event_handler: Callable[[dict[str, Any]], None],
        config: FeedConfig,
        logger: JsonLogger,
    ) -> None:
        self._asset_ids = list(asset_ids)
        self._event_handler = event_handler
        self._config = config
        self._logger = logger
        self._stop_event = threading.Event()
        self._current_ws: websocket.WebSocketApp | None = None

    def stop(self) -> None:
        self._stop_event.set()
        if self._current_ws is not None:
            self._current_ws.close()

    def run_forever(self) -> None:
        while not self._stop_event.is_set():
            self._logger.emit(
                "feed_connecting",
                ws_url=self._config.ws_url,
                asset_count=len(self._asset_ids),
            )
            ws = websocket.WebSocketApp(
                self._config.ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            self._current_ws = ws
            ws.run_forever(ping_interval=max(self._config.heartbeat_interval_sec * 2, 20.0))
            self._current_ws = None
            if self._stop_event.is_set():
                break
            time.sleep(self._config.reconnect_delay_sec)

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        batch_size = max(1, self._config.subscription_batch_size)
        batches = [
            self._asset_ids[index : index + batch_size]
            for index in range(0, len(self._asset_ids), batch_size)
        ]
        if not batches:
            raise ValueError("at least one asset_id is required")

        ws.send(json.dumps({"type": "market", "assets_ids": batches[0]}))
        for batch in batches[1:]:
            ws.send(json.dumps({"operation": "subscribe", "assets_ids": batch}))

        self._logger.emit(
            "feed_subscribed",
            asset_count=len(self._asset_ids),
            batch_count=len(batches),
            batch_size=batch_size,
        )

    def _on_message(self, _ws: websocket.WebSocketApp, raw: str) -> None:
        if raw == "ping":
            _ws.send("pong")
            return
        if raw == "pong":
            return
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._logger.emit("feed_decode_error", error=repr(exc), raw=raw)
            return

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if isinstance(item, dict):
                try:
                    self._event_handler(item)
                except Exception as exc:
                    self._logger.emit(
                        "event_processing_error",
                        error=repr(exc),
                        event_type=item.get("event_type"),
                        market=item.get("market"),
                        asset_id=item.get("asset_id"),
                    )

    def _on_error(self, _ws: websocket.WebSocketApp, error: Any) -> None:
        self._logger.emit("feed_error", error=repr(error))

    def _on_close(self, _ws: websocket.WebSocketApp, status_code: Any, message: Any) -> None:
        self._logger.emit("feed_closed", status_code=status_code, message=message)
