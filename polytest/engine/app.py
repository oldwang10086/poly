from __future__ import annotations

from typing import Any

from .config import EngineConfig
from .executor import MockExecutor
from .json_logging import JsonLogger
from .models import MarketDefinition, MarketSnapshot, parse_timestamp_ms
from .orderbook import TopOfBookStore
from .strategy import BuyBothAndMergeStrategy


class ArbitrageEngine:
    def __init__(
        self,
        definitions: dict[str, MarketDefinition],
        config: EngineConfig,
        logger: JsonLogger,
        executor: MockExecutor | None = None,
    ) -> None:
        self._definitions = definitions
        self._config = config
        self._logger = logger
        self._store = TopOfBookStore(definitions)
        self._strategy = BuyBothAndMergeStrategy(config.strategy)
        self._executor = executor if executor is not None else MockExecutor(logger)
        self._last_opportunity_by_market: dict[str, str] = {}

    @property
    def asset_ids(self) -> list[str]:
        asset_ids: list[str] = []
        for definition in self._definitions.values():
            asset_ids.extend(definition.asset_ids)
        return asset_ids

    @property
    def executor(self) -> MockExecutor:
        return self._executor

    def handle_event(self, event: dict[str, Any]) -> None:
        self._store.apply_event(event)
        dirty_markets = self._store.consume_dirty_markets()
        if not dirty_markets:
            return

        event_type = event.get("event_type") or ("book" if "bids" in event else None)
        self._logger.emit(
            "market_data_applied",
            event_type=event_type,
            dirty_markets=dirty_markets,
        )

        detected_at_ms = parse_timestamp_ms(event.get("timestamp"))
        for market_id in dirty_markets:
            snapshot = self._store.snapshot_for_market(market_id)
            if snapshot is None:
                continue
            self._scan_market(snapshot, detected_at_ms)

    def _scan_market(self, snapshot: MarketSnapshot, detected_at_ms: int | None) -> None:
        opportunity = self._strategy.evaluate(snapshot, detected_at_ms)
        market_id = snapshot.definition.market_id

        if opportunity is None:
            self._last_opportunity_by_market.pop(market_id, None)
            return

        fingerprint = opportunity.fingerprint()
        if self._config.strategy.emit_only_on_change:
            previous = self._last_opportunity_by_market.get(market_id)
            if previous == fingerprint:
                return

        self._last_opportunity_by_market[market_id] = fingerprint
        self._logger.emit("opportunity", opportunity=opportunity)
        self._executor.execute(opportunity)
