from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path

from .app import ArbitrageEngine
from .config import EngineConfig, FeedConfig, StrategyConfig
from .feed import PolymarketMarketFeed
from .json_logging import JsonLogger
from .whitelist import discover_gamma_fee_free_market_definitions, load_market_definitions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polymarket arbitrage engine v1")
    parser.add_argument(
        "--market-source",
        choices=("gamma-fee-free", "file"),
        default="gamma-fee-free",
        help="How to source the market universe",
    )
    parser.add_argument(
        "--whitelist",
        default="config/markets.example.json",
        help="Path to the market whitelist JSON file when --market-source=file",
    )
    parser.add_argument("--log-file", default=None, help="Optional JSONL log output path")
    parser.add_argument("--buffer", type=Decimal, default=Decimal("0.005"), help="Total cost buffer")
    parser.add_argument("--min-size", type=Decimal, default=Decimal("1"), help="Minimum size to execute")
    parser.add_argument("--max-size", type=Decimal, default=Decimal("100"), help="Maximum size to execute")
    parser.add_argument(
        "--capital-limit",
        type=Decimal,
        default=Decimal("100"),
        help="Maximum notional capital per opportunity",
    )
    parser.add_argument(
        "--heartbeat-sec",
        type=float,
        default=10.0,
        help="Application-level heartbeat interval",
    )
    parser.add_argument(
        "--reconnect-sec",
        type=float,
        default=5.0,
        help="Reconnect delay after feed disconnect",
    )
    parser.add_argument(
        "--subscription-batch-size",
        type=int,
        default=500,
        help="Number of asset ids per subscribe message",
    )
    parser.add_argument(
        "--max-markets",
        type=int,
        default=None,
        help="Optional cap for discovered markets, useful for smoke tests",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    logger = JsonLogger(
        log_path=Path(args.log_file) if args.log_file else None,
        stream_include_events={"opportunity"},
    )
    whitelist_path = Path(args.whitelist) if args.market_source == "file" else None
    logger.emit(
        "market_universe_loading",
        market_source=args.market_source,
        whitelist_path=whitelist_path,
        max_markets=args.max_markets,
    )
    if args.market_source == "file":
        definitions = load_market_definitions(whitelist_path)
    else:
        definitions = discover_gamma_fee_free_market_definitions(max_markets=args.max_markets)
    logger.emit(
        "market_universe_loaded",
        market_source=args.market_source,
        market_count=len(definitions),
        asset_count=2 * len(definitions),
    )

    config = EngineConfig(
        whitelist_path=whitelist_path,
        log_path=Path(args.log_file) if args.log_file else None,
        strategy=StrategyConfig(
            total_cost_buffer=args.buffer,
            min_size=args.min_size,
            max_size=args.max_size,
            capital_limit=args.capital_limit,
        ),
        feed=FeedConfig(
            heartbeat_interval_sec=args.heartbeat_sec,
            reconnect_delay_sec=args.reconnect_sec,
            subscription_batch_size=args.subscription_batch_size,
        ),
    )

    engine = ArbitrageEngine(definitions=definitions, config=config, logger=logger)
    feed = PolymarketMarketFeed(
        asset_ids=engine.asset_ids,
        event_handler=engine.handle_event,
        config=config.feed,
        logger=logger,
    )

    logger.emit(
        "engine_start",
        market_count=len(definitions),
        asset_count=len(engine.asset_ids),
        config=config,
    )
    try:
        feed.run_forever()
    except KeyboardInterrupt:
        logger.emit("engine_stop", reason="keyboard_interrupt")
        feed.stop()
    finally:
        logger.close()


if __name__ == "__main__":
    main()
