from __future__ import annotations

import unittest
from decimal import Decimal

from polytest.engine.config import StrategyConfig
from polytest.engine.models import MarketDefinition, MarketSnapshot, OrderLevel, OutcomeBook, parse_decimal
from polytest.engine.strategy import BuyBothAndMergeStrategy


class BuyBothAndMergeStrategyTests(unittest.TestCase):
    def test_emits_opportunity_with_expected_sizing(self) -> None:
        strategy = BuyBothAndMergeStrategy(
            StrategyConfig(
                total_cost_buffer=Decimal("0.01"),
                min_size=Decimal("1"),
                max_size=Decimal("50"),
                capital_limit=Decimal("100"),
            )
        )
        snapshot = MarketSnapshot(
            definition=MarketDefinition(
                market_id="market-1",
                question="Will it rain?",
                yes_asset_id="yes-1",
                no_asset_id="no-1",
            ),
            yes_book=OutcomeBook(
                asset_id="yes-1",
                best_ask=OrderLevel(price=Decimal("0.48"), size=Decimal("20")),
            ),
            no_book=OutcomeBook(
                asset_id="no-1",
                best_ask=OrderLevel(price=Decimal("0.49"), size=Decimal("10")),
            ),
        )

        opportunity = strategy.evaluate(snapshot, detected_at_ms=1234)
        assert opportunity is not None

        self.assertEqual(opportunity.total_cost, Decimal("0.97"))
        self.assertEqual(opportunity.gross_edge, Decimal("0.03"))
        self.assertEqual(opportunity.net_edge, Decimal("0.02"))
        self.assertEqual(opportunity.size_contracts, Decimal("10"))
        self.assertEqual(opportunity.notional_cost, Decimal("9.70"))
        self.assertEqual(opportunity.expected_net_pnl, Decimal("0.20"))

    def test_skips_when_top_sizes_are_unknown(self) -> None:
        strategy = BuyBothAndMergeStrategy(StrategyConfig())
        snapshot = MarketSnapshot(
            definition=MarketDefinition(
                market_id="market-1",
                question="Will it rain?",
                yes_asset_id="yes-1",
                no_asset_id="no-1",
            ),
            yes_book=OutcomeBook(
                asset_id="yes-1",
                best_ask=OrderLevel(price=Decimal("0.48"), size=None),
            ),
            no_book=OutcomeBook(
                asset_id="no-1",
                best_ask=OrderLevel(price=Decimal("0.49"), size=Decimal("10")),
            ),
        )

        self.assertIsNone(strategy.evaluate(snapshot, detected_at_ms=1234))

    def test_parse_decimal_tolerates_invalid_input(self) -> None:
        self.assertIsNone(parse_decimal(""))
        self.assertIsNone(parse_decimal("not-a-number"))
        self.assertIsNone(parse_decimal("NaN"))


if __name__ == "__main__":
    unittest.main()
