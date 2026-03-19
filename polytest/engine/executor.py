from __future__ import annotations

import time

from .json_logging import JsonLogger
from .models import MockExecutionRecord, OpportunityEvent


class MockExecutor:
    def __init__(self, logger: JsonLogger | None = None) -> None:
        self._logger = logger
        self.records: list[MockExecutionRecord] = []

    def execute(self, opportunity: OpportunityEvent) -> MockExecutionRecord:
        record = MockExecutionRecord(
            status="mock_filled",
            market_id=opportunity.market_id,
            strategy=opportunity.strategy,
            executed_at_ms=int(time.time() * 1000),
            size_contracts=opportunity.size_contracts,
            notional_cost=opportunity.notional_cost,
            expected_net_pnl=opportunity.expected_net_pnl,
        )
        self.records.append(record)
        if self._logger is not None:
            self._logger.emit("mock_execution", execution=record)
        return record
