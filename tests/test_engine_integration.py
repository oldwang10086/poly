from __future__ import annotations

import io
import json
import unittest
from decimal import Decimal
from pathlib import Path

from polytest.engine.app import ArbitrageEngine
from polytest.engine.config import EngineConfig, StrategyConfig
from polytest.engine.json_logging import JsonLogger
from polytest.engine.whitelist import load_market_definitions


class EngineIntegrationTests(unittest.TestCase):
    def test_engine_scans_dirty_market_and_mock_executes_once(self) -> None:
        definitions = load_market_definitions(Path("config/markets.example.json"))
        stream = io.StringIO()
        logger = JsonLogger(stream=stream)
        engine = ArbitrageEngine(
            definitions=definitions,
            config=EngineConfig(
                whitelist_path=Path("config/markets.example.json"),
                strategy=StrategyConfig(
                    total_cost_buffer=Decimal("0.01"),
                    min_size=Decimal("1"),
                    max_size=Decimal("100"),
                    capital_limit=Decimal("100"),
                ),
            ),
            logger=logger,
        )

        yes_asset_id = definitions[next(iter(definitions))].yes_asset_id
        no_asset_id = definitions[next(iter(definitions))].no_asset_id

        engine.handle_event(
            {
                "event_type": "book",
                "asset_id": yes_asset_id,
                "timestamp": "1000",
                "bids": [],
                "asks": [{"price": "0.48", "size": "5"}],
            }
        )
        engine.handle_event(
            {
                "event_type": "book",
                "asset_id": no_asset_id,
                "timestamp": "1001",
                "bids": [],
                "asks": [{"price": "0.49", "size": "7"}],
            }
        )
        engine.handle_event(
            {
                "event_type": "book",
                "asset_id": no_asset_id,
                "timestamp": "1002",
                "bids": [],
                "asks": [{"price": "0.49", "size": "7"}],
            }
        )

        self.assertEqual(len(engine.executor.records), 1)

        events = [json.loads(line)["event"] for line in stream.getvalue().splitlines()]
        self.assertIn("opportunity", events)
        self.assertIn("mock_execution", events)


if __name__ == "__main__":
    unittest.main()
