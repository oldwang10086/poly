from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from polytest.engine.whitelist import is_fee_free_binary_market, load_market_definitions


class WhitelistLoaderTests(unittest.TestCase):
    def test_loads_explicit_yes_no_format(self) -> None:
        payload = [
            {
                "market_id": "market-1",
                "question": "Will it rain?",
                "yes_asset_id": "yes-1",
                "no_asset_id": "no-1",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "markets.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            definitions = load_market_definitions(path)

        definition = definitions["market-1"]
        self.assertEqual(definition.yes_asset_id, "yes-1")
        self.assertEqual(definition.no_asset_id, "no-1")
        self.assertEqual(definition.question, "Will it rain?")

    def test_loads_gamma_style_format(self) -> None:
        payload = {
            "markets": [
                {
                    "conditionId": "market-2",
                    "question": "Will Team A win?",
                    "outcomes": '["Yes", "No"]',
                    "clobTokenIds": '["yes-2", "no-2"]',
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "markets.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            definitions = load_market_definitions(path)

        definition = definitions["market-2"]
        self.assertEqual(definition.yes_asset_id, "yes-2")
        self.assertEqual(definition.no_asset_id, "no-2")

    def test_rejects_non_binary_outcomes(self) -> None:
        payload = [
            {
                "market_id": "market-3",
                "outcomes": ["Up", "Down"],
                "clobTokenIds": ["up-3", "down-3"],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "markets.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_market_definitions(path)

    def test_fee_free_binary_filter_accepts_expected_market(self) -> None:
        entry = {
            "conditionId": "market-4",
            "question": "Will it rain?",
            "closed": False,
            "active": True,
            "enableOrderBook": True,
            "feesEnabled": False,
            "outcomes": '["Yes", "No"]',
            "clobTokenIds": '["yes-4", "no-4"]',
        }
        self.assertTrue(is_fee_free_binary_market(entry))

    def test_fee_free_binary_filter_rejects_fee_enabled_market(self) -> None:
        entry = {
            "conditionId": "market-5",
            "closed": False,
            "active": True,
            "enableOrderBook": True,
            "feesEnabled": True,
            "outcomes": '["Yes", "No"]',
            "clobTokenIds": '["yes-5", "no-5"]',
        }
        self.assertFalse(is_fee_free_binary_market(entry))


if __name__ == "__main__":
    unittest.main()
