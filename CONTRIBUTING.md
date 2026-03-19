# Contributing

## Setup

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -e .
```

## Run Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Guidelines

- Keep the repo focused on Polymarket arbitrage infrastructure.
- Preserve the current v1 scope unless a change explicitly expands it.
- Prefer deterministic tests over network-dependent tests.
- Avoid mixing unrelated notebooks, datasets, or personal scripts into the repo.
