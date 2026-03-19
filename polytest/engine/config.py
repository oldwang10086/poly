from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path


@dataclass(slots=True, frozen=True)
class StrategyConfig:
    total_cost_buffer: Decimal = Decimal("0.005")
    min_size: Decimal = Decimal("1")
    max_size: Decimal = Decimal("100")
    capital_limit: Decimal = Decimal("100")
    emit_only_on_change: bool = True


@dataclass(slots=True, frozen=True)
class FeedConfig:
    ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    heartbeat_interval_sec: float = 10.0
    reconnect_delay_sec: float = 5.0
    subscription_batch_size: int = 500


@dataclass(slots=True, frozen=True)
class EngineConfig:
    whitelist_path: Path | None = None
    log_path: Path | None = None
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    feed: FeedConfig = field(default_factory=FeedConfig)
