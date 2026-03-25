# Polymarket Arbitrage Engine

A focused event-driven engine for scanning fee-free Polymarket binary markets and detecting `buy-both-and-merge` arbitrage opportunities in real time.

This repo is intentionally narrow:
- discovers live fee-free `Yes/No` markets from Gamma
- subscribes to Polymarket market WebSocket data
- maintains local top-of-book only
- computes executable arbitrage opportunities
- prints only `opportunity` events to stdout
- records mock executions without placing real orders

## Why This Repo

Most trading repos try to do everything at once. This one does not.

The goal is to provide a clean first-stage arbitrage engine with:
- a clear market data pipeline
- deterministic sizing logic
- explicit v1 boundaries
- tests that validate core behavior
- an execution interface that can be replaced later

For a longer project introduction, see:
- [docs/INTRODUCTION.md](docs/INTRODUCTION.md)

## Strategy

Current strategy:

`buy-both-and-merge`

Trigger condition:

```text
best_ask_yes + best_ask_no + total_cost_buffer < 1
```

The engine then sizes the trade using:
- top-of-book size on the `YES` side
- top-of-book size on the `NO` side
- `max_size`
- `capital_limit / total_cost`

## Current Scope

Included:
- fee-free market discovery
- file-based whitelist mode
- WebSocket market subscription
- local top-of-book maintenance
- dirty market scanning
- arbitrage opportunity detection
- sizing logic
- mock execution
- structured logging
- unit and integration tests

Not included:
- real order placement
- wallet signing
- on-chain merge settlement
- full depth book maintenance
- inventory optimization
- persistence/database storage
- UI

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -e .
python run_engine.py --max-markets 100
```

Default behavior:
- source market universe from live Gamma fee-free binary markets
- print only `opportunity` events to stdout
- keep detailed logs optional via `--log-file`

## Example Output

Stdout:

```json
{"ts_ms":1773914468449,"event":"opportunity","opportunity":{"strategy":"buy-both-and-merge","market_id":"0x...","question":"Example market?","yes_asset_id":"...","no_asset_id":"...","detected_at_ms":1773914468440,"best_ask_yes":"0.48","best_ask_no":"0.49","best_ask_yes_size":"5","best_ask_no_size":"7","total_cost":"0.97","gross_edge":"0.03","total_cost_buffer":"0.005","net_edge":"0.025","size_contracts":"5","notional_cost":"4.85","expected_gross_pnl":"0.15","expected_net_pnl":"0.125"}}
```

More examples:
- [examples/opportunity.sample.jsonl](examples/opportunity.sample.jsonl)

## CLI

```bash
python run_engine.py --help
```

Main options:
- `--market-source gamma-fee-free`
- `--market-source file --whitelist config/markets.example.json`
- `--max-markets 100`
- `--log-file logs/engine.jsonl`
- `--buffer 0.005`
- `--capital-limit 100`

## Repository Layout

```text
polymarket-arbitrage-engine/
+-- README.md
+-- LICENSE
+-- CHANGELOG.md
+-- CONTRIBUTING.md
+-- .gitignore
+-- pyproject.toml
+-- run_engine.py
+-- .github/
|   `-- workflows/
|       `-- ci.yml
+-- config/
|   `-- markets.example.json
+-- docs/
|   +-- PROJECT_STRUCTURE.md
|   `-- ROADMAP.md
+-- examples/
|   `-- opportunity.sample.jsonl
+-- scripts/
|   `-- push_to_github.ps1
+-- polytest/
|   +-- __init__.py
|   `-- engine/
|       +-- __init__.py
|       +-- __main__.py
|       +-- app.py
|       +-- config.py
|       +-- executor.py
|       +-- feed.py
|       +-- json_logging.py
|       +-- models.py
|       +-- orderbook.py
|       +-- strategy.py
|       `-- whitelist.py
`-- tests/
    +-- test_engine_integration.py
    +-- test_logging.py
    +-- test_orderbook.py
    +-- test_strategy.py
    `-- test_whitelist.py
```

