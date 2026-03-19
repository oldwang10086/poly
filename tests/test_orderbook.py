from __future__ import annotations

import unittest
from decimal import Decimal

from polytest.engine.models import MarketDefinition
from polytest.engine.orderbook import TopOfBookStore


class TopOfBookStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = MarketDefinition(
            market_id="market-1",
            question="Will it rain?",
            yes_asset_id="yes-1",
            no_asset_id="no-1",
        )
        self.store = TopOfBookStore({"market-1": self.definition})

    def test_book_snapshot_keeps_only_top_of_book(self) -> None:
        self.store.apply_event(
            {
                "event_type": "book",
                "asset_id": "yes-1",
                "timestamp": "1000",
                "bids": [
                    {"price": "0.47", "size": "4"},
                    {"price": "0.49", "size": "7"},
                ],
                "asks": [
                    {"price": "0.54", "size": "9"},
                    {"price": "0.52", "size": "11"},
                ],
            }
        )

        dirty = self.store.consume_dirty_markets()
        snapshot = self.store.snapshot_for_market("market-1")
        assert snapshot is not None

        self.assertEqual(dirty, ["market-1"])
        self.assertEqual(snapshot.yes_book.best_bid.price, Decimal("0.49"))
        self.assertEqual(snapshot.yes_book.best_bid.size, Decimal("7"))
        self.assertEqual(snapshot.yes_book.best_ask.price, Decimal("0.52"))
        self.assertEqual(snapshot.yes_book.best_ask.size, Decimal("11"))

    def test_price_change_rolls_top_price_to_unknown_size_when_next_level_is_not_in_event(self) -> None:
        self.store.apply_event(
            {
                "event_type": "book",
                "asset_id": "yes-1",
                "timestamp": "1000",
                "bids": [],
                "asks": [{"price": "0.52", "size": "11"}],
            }
        )
        self.store.consume_dirty_markets()

        self.store.apply_event(
            {
                "event_type": "price_change",
                "timestamp": "1001",
                "price_changes": [
                    {
                        "asset_id": "yes-1",
                        "price": "0.52",
                        "size": "0",
                        "side": "SELL",
                        "best_bid": "0.49",
                        "best_ask": "0.53",
                    }
                ],
            }
        )

        snapshot = self.store.snapshot_for_market("market-1")
        assert snapshot is not None

        self.assertEqual(snapshot.yes_book.best_ask.price, Decimal("0.53"))
        self.assertIsNone(snapshot.yes_book.best_ask.size)

    def test_price_change_updates_top_size_when_event_touches_current_best(self) -> None:
        self.store.apply_event(
            {
                "event_type": "book",
                "asset_id": "no-1",
                "timestamp": "1000",
                "bids": [],
                "asks": [{"price": "0.48", "size": "6"}],
            }
        )
        self.store.consume_dirty_markets()

        self.store.apply_event(
            {
                "event_type": "price_change",
                "timestamp": "1001",
                "price_changes": [
                    {
                        "asset_id": "no-1",
                        "price": "0.48",
                        "size": "9",
                        "side": "SELL",
                        "best_bid": "0.47",
                        "best_ask": "0.48",
                    }
                ],
            }
        )

        snapshot = self.store.snapshot_for_market("market-1")
        assert snapshot is not None

        self.assertEqual(snapshot.no_book.best_ask.price, Decimal("0.48"))
        self.assertEqual(snapshot.no_book.best_ask.size, Decimal("9"))


if __name__ == "__main__":
    unittest.main()
