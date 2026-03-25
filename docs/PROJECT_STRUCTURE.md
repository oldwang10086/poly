# Project Structure

Use this as the repository root when publishing to GitHub:

```text
polymarket-arbitrage-engine/
+-- README.md
+-- .gitignore
+-- pyproject.toml
+-- run_engine.py
+-- config/
|   `-- markets.example.json
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

## Module Roles

- `run_engine.py`: convenience entrypoint
- `polytest/engine/feed.py`: WebSocket subscription and message intake
- `polytest/engine/orderbook.py`: local top-of-book state
- `polytest/engine/strategy.py`: `buy-both-and-merge` scan logic
- `polytest/engine/executor.py`: mock execution only
- `polytest/engine/whitelist.py`: fee-free market discovery and file whitelist loading
- `tests/`: deterministic local validation

- 
