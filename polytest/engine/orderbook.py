from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import (
    MarketDefinition,
    MarketSnapshot,
    ZERO,
    OrderLevel,
    OutcomeBook,
    normalize_ask_price,
    normalize_bid_price,
    parse_decimal,
    parse_timestamp_ms,
)


class TopOfBookStore:
    def __init__(self, definitions: dict[str, MarketDefinition]) -> None:
        self._definitions = definitions
        self._asset_to_market: dict[str, str] = {}
        self._books_by_asset: dict[str, OutcomeBook] = {}
        self._dirty_markets: set[str] = set()

        for market_id, definition in definitions.items():
            self._asset_to_market[definition.yes_asset_id] = market_id
            self._asset_to_market[definition.no_asset_id] = market_id
            self._books_by_asset[definition.yes_asset_id] = OutcomeBook(asset_id=definition.yes_asset_id)
            self._books_by_asset[definition.no_asset_id] = OutcomeBook(asset_id=definition.no_asset_id)

    def apply_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("event_type") or self._infer_event_type(event)).lower()
        if event_type == "book":
            self._apply_book(event)
        elif event_type == "price_change":
            self._apply_price_change(event)
        elif event_type == "best_bid_ask":
            self._apply_best_bid_ask(event)

    def consume_dirty_markets(self) -> list[str]:
        dirty = sorted(self._dirty_markets)
        self._dirty_markets.clear()
        return dirty

    def snapshot_for_market(self, market_id: str) -> MarketSnapshot | None:
        definition = self._definitions.get(market_id)
        if definition is None:
            return None
        return MarketSnapshot(
            definition=definition,
            yes_book=self._books_by_asset[definition.yes_asset_id],
            no_book=self._books_by_asset[definition.no_asset_id],
        )

    def _infer_event_type(self, event: dict[str, Any]) -> str:
        if "price_changes" in event:
            return "price_change"
        if "bids" in event or "asks" in event:
            return "book"
        return "unknown"

    def _mark_dirty_for_asset(self, asset_id: str) -> None:
        market_id = self._asset_to_market.get(asset_id)
        if market_id is not None:
            self._dirty_markets.add(market_id)

    def _apply_book(self, event: dict[str, Any]) -> None:
        asset_id = str(event.get("asset_id") or "")
        book = self._books_by_asset.get(asset_id)
        if book is None:
            return

        timestamp_ms = parse_timestamp_ms(event.get("timestamp"))
        best_bid = self._pick_best_bid(event.get("bids", []))
        best_ask = self._pick_best_ask(event.get("asks", []))

        changed = False
        changed |= self._set_level(book.best_bid, best_bid[0], best_bid[1], timestamp_ms)
        changed |= self._set_level(book.best_ask, best_ask[0], best_ask[1], timestamp_ms)

        tick_size = parse_decimal(event.get("tick_size"))
        last_trade_price = parse_decimal(event.get("last_trade_price"))
        if book.tick_size != tick_size:
            book.tick_size = tick_size
            changed = True
        if book.last_trade_price != last_trade_price:
            book.last_trade_price = last_trade_price
            changed = True

        last_book_hash = event.get("hash")
        if book.last_book_hash != last_book_hash:
            book.last_book_hash = str(last_book_hash) if last_book_hash is not None else None
            changed = True

        if book.last_update_ms != timestamp_ms:
            book.last_update_ms = timestamp_ms
            changed = True

        if changed:
            self._mark_dirty_for_asset(asset_id)

    def _apply_price_change(self, event: dict[str, Any]) -> None:
        timestamp_ms = parse_timestamp_ms(event.get("timestamp"))
        for change in event.get("price_changes", []):
            asset_id = str(change.get("asset_id") or "")
            book = self._books_by_asset.get(asset_id)
            if book is None:
                continue
            side = str(change.get("side") or "").upper()
            level_price = parse_decimal(change.get("price"))
            level_size = parse_decimal(change.get("size"))
            best_bid = parse_decimal(change.get("best_bid"))
            best_ask = parse_decimal(change.get("best_ask"))

            changed = False
            if side == "BUY":
                changed |= self._apply_top_level_delta(
                    level=book.best_bid,
                    updated_level_price=normalize_bid_price(level_price),
                    updated_level_size=level_size,
                    new_best_price=normalize_bid_price(best_bid),
                    timestamp_ms=timestamp_ms,
                )
            elif side == "SELL":
                changed |= self._apply_top_level_delta(
                    level=book.best_ask,
                    updated_level_price=normalize_ask_price(level_price),
                    updated_level_size=level_size,
                    new_best_price=normalize_ask_price(best_ask),
                    timestamp_ms=timestamp_ms,
                )

            if changed:
                book.last_update_ms = timestamp_ms
                self._mark_dirty_for_asset(asset_id)

    def _apply_best_bid_ask(self, event: dict[str, Any]) -> None:
        asset_id = str(event.get("asset_id") or "")
        book = self._books_by_asset.get(asset_id)
        if book is None:
            return

        timestamp_ms = parse_timestamp_ms(event.get("timestamp"))
        new_best_bid = normalize_bid_price(parse_decimal(event.get("best_bid")))
        new_best_ask = normalize_ask_price(parse_decimal(event.get("best_ask")))

        changed = False
        changed |= self._set_level(
            book.best_bid,
            new_best_bid,
            book.best_bid.size if book.best_bid.price == new_best_bid else None,
            timestamp_ms,
        )
        changed |= self._set_level(
            book.best_ask,
            new_best_ask,
            book.best_ask.size if book.best_ask.price == new_best_ask else None,
            timestamp_ms,
        )
        if changed:
            book.last_update_ms = timestamp_ms
            self._mark_dirty_for_asset(asset_id)

    def _pick_best_bid(self, levels: list[dict[str, Any]]) -> tuple[Decimal | None, Decimal | None]:
        best_price: Decimal | None = None
        best_size: Decimal | None = None
        for level in levels:
            price = normalize_bid_price(parse_decimal(level.get("price")))
            size = parse_decimal(level.get("size"))
            if price is None or size is None or size <= ZERO:
                continue
            if best_price is None or price > best_price:
                best_price = price
                best_size = size
        return best_price, best_size

    def _pick_best_ask(self, levels: list[dict[str, Any]]) -> tuple[Decimal | None, Decimal | None]:
        best_price: Decimal | None = None
        best_size: Decimal | None = None
        for level in levels:
            price = normalize_ask_price(parse_decimal(level.get("price")))
            size = parse_decimal(level.get("size"))
            if price is None or size is None or size <= ZERO:
                continue
            if best_price is None or price < best_price:
                best_price = price
                best_size = size
        return best_price, best_size

    def _set_level(
        self,
        level: OrderLevel,
        price: Decimal | None,
        size: Decimal | None,
        timestamp_ms: int | None,
    ) -> bool:
        if price is None:
            size = None
        elif size is not None and size <= ZERO:
            size = None
        changed = level.price != price or level.size != size or level.timestamp_ms != timestamp_ms
        level.price = price
        level.size = size
        level.timestamp_ms = timestamp_ms
        return changed

    def _apply_top_level_delta(
        self,
        level: OrderLevel,
        updated_level_price: Decimal | None,
        updated_level_size: Decimal | None,
        new_best_price: Decimal | None,
        timestamp_ms: int | None,
    ) -> bool:
        if new_best_price is None:
            return self._set_level(level, None, None, timestamp_ms)

        if updated_level_price == new_best_price:
            return self._set_level(level, new_best_price, updated_level_size, timestamp_ms)

        if level.price == new_best_price:
            if level.price == updated_level_price:
                return self._set_level(level, new_best_price, updated_level_size, timestamp_ms)
            return False

        return self._set_level(level, new_best_price, None, timestamp_ms)
