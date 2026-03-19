from __future__ import annotations

from .config import StrategyConfig
from .models import MarketSnapshot, ONE, OpportunityEvent, ZERO


class BuyBothAndMergeStrategy:
    name = "buy-both-and-merge"

    def __init__(self, config: StrategyConfig) -> None:
        self._config = config

    def evaluate(self, snapshot: MarketSnapshot, detected_at_ms: int | None) -> OpportunityEvent | None:
        yes_ask = snapshot.yes_book.best_ask.price
        no_ask = snapshot.no_book.best_ask.price
        yes_size = snapshot.yes_book.best_ask.size
        no_size = snapshot.no_book.best_ask.size

        if (
            yes_ask is None
            or no_ask is None
            or yes_size is None
            or no_size is None
            or yes_size <= ZERO
            or no_size <= ZERO
        ):
            return None

        total_cost = yes_ask + no_ask
        if total_cost <= ZERO or total_cost >= ONE:
            return None

        gross_edge = ONE - total_cost
        net_edge = gross_edge - self._config.total_cost_buffer
        if net_edge <= ZERO:
            return None

        max_by_capital = self._config.capital_limit / total_cost
        size_contracts = min(yes_size, no_size, self._config.max_size, max_by_capital)
        if size_contracts < self._config.min_size:
            return None

        notional_cost = size_contracts * total_cost
        expected_gross_pnl = size_contracts * gross_edge
        expected_net_pnl = size_contracts * net_edge

        return OpportunityEvent(
            strategy=self.name,
            market_id=snapshot.definition.market_id,
            question=snapshot.definition.question,
            yes_asset_id=snapshot.definition.yes_asset_id,
            no_asset_id=snapshot.definition.no_asset_id,
            detected_at_ms=detected_at_ms,
            best_ask_yes=yes_ask,
            best_ask_no=no_ask,
            best_ask_yes_size=yes_size,
            best_ask_no_size=no_size,
            total_cost=total_cost,
            gross_edge=gross_edge,
            total_cost_buffer=self._config.total_cost_buffer,
            net_edge=net_edge,
            size_contracts=size_contracts,
            notional_cost=notional_cost,
            expected_gross_pnl=expected_gross_pnl,
            expected_net_pnl=expected_net_pnl,
        )
