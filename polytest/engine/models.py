from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

ZERO = Decimal("0")
ONE = Decimal("1")


def parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if isinstance(value, bool):
        raise TypeError("boolean cannot be parsed as Decimal")
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def parse_timestamp_ms(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def normalize_bid_price(value: Decimal | None) -> Decimal | None:
    if value is None or value <= ZERO:
        return None
    return value


def normalize_ask_price(value: Decimal | None) -> Decimal | None:
    if value is None or value <= ZERO or value >= ONE:
        return None
    return value


@dataclass(slots=True)
class OrderLevel:
    price: Decimal | None = None
    size: Decimal | None = None
    timestamp_ms: int | None = None


@dataclass(slots=True)
class OutcomeBook:
    asset_id: str
    best_bid: OrderLevel = field(default_factory=OrderLevel)
    best_ask: OrderLevel = field(default_factory=OrderLevel)
    last_update_ms: int | None = None
    tick_size: Decimal | None = None
    last_trade_price: Decimal | None = None
    last_book_hash: str | None = None


@dataclass(slots=True, frozen=True)
class MarketDefinition:
    market_id: str
    question: str
    yes_asset_id: str
    no_asset_id: str
    slug: str | None = None
    outcomes: tuple[str, str] = ("Yes", "No")
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def asset_ids(self) -> tuple[str, str]:
        return (self.yes_asset_id, self.no_asset_id)


@dataclass(slots=True, frozen=True)
class MarketSnapshot:
    definition: MarketDefinition
    yes_book: OutcomeBook
    no_book: OutcomeBook


@dataclass(slots=True, frozen=True)
class OpportunityEvent:
    strategy: str
    market_id: str
    question: str
    yes_asset_id: str
    no_asset_id: str
    detected_at_ms: int | None
    best_ask_yes: Decimal
    best_ask_no: Decimal
    best_ask_yes_size: Decimal
    best_ask_no_size: Decimal
    total_cost: Decimal
    gross_edge: Decimal
    total_cost_buffer: Decimal
    net_edge: Decimal
    size_contracts: Decimal
    notional_cost: Decimal
    expected_gross_pnl: Decimal
    expected_net_pnl: Decimal

    def fingerprint(self) -> str:
        return "|".join(
            [
                self.market_id,
                str(self.best_ask_yes),
                str(self.best_ask_no),
                str(self.size_contracts),
                str(self.net_edge),
            ]
        )


@dataclass(slots=True, frozen=True)
class MockExecutionRecord:
    status: str
    market_id: str
    strategy: str
    executed_at_ms: int
    size_contracts: Decimal
    notional_cost: Decimal
    expected_net_pnl: Decimal
